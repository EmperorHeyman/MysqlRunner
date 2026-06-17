"""Credential vault.

A random Data Encryption Key (DEK) protects all stored credentials. The DEK is
itself encrypted with a Key Encryption Key (KEK) derived from the user's master
password via PBKDF2-HMAC-SHA256. The encrypted DEK and its salt live in a small
JSON metadata file on disk.

For convenience the plaintext DEK is also cached in the OS keyring (Windows
Credential Manager). On unlock we try the keyring first; if it is unavailable or
empty we fall back to prompting for the master password.
"""

from __future__ import annotations

import base64
import importlib
import json
import os
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from mysql_runner.paths import vault_path

_KEYRING_SERVICE = "MySQLRunner"
_KEYRING_USERNAME = "dek"
_PBKDF2_ITERATIONS = 480_000
_SALT_BYTES = 16


def _get_keyring_module():
    """Import keyring lazily so packaging can omit it when unavailable."""
    try:
        return importlib.import_module("keyring")
    except Exception:
        return None


class VaultError(Exception):
    """Base class for vault errors."""


class InvalidMasterPassword(VaultError):
    """Raised when the supplied master password cannot decrypt the DEK."""


class VaultNotInitialized(VaultError):
    """Raised when an operation needs an initialized vault but none exists."""


def _derive_kek(master_password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode("utf-8")))


@dataclass
class Vault:
    """Holds the active Data Encryption Key for the running session."""

    _dek: bytes

    @property
    def fernet(self) -> Fernet:
        return Fernet(self._dek)

    def encrypt(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        return self.fernet.decrypt(token)

    def lock(self) -> None:
        """Wipe the in-memory key reference."""
        self._dek = b""


def is_initialized() -> bool:
    return vault_path().exists()


def _write_metadata(salt: bytes, encrypted_dek: bytes) -> None:
    payload = {
        "version": 1,
        "salt": base64.b64encode(salt).decode("ascii"),
        "encrypted_dek": base64.b64encode(encrypted_dek).decode("ascii"),
    }
    path = vault_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _read_metadata() -> tuple[bytes, bytes]:
    if not is_initialized():
        raise VaultNotInitialized("Vault has not been created yet.")
    data = json.loads(vault_path().read_text(encoding="utf-8"))
    return (
        base64.b64decode(data["salt"]),
        base64.b64decode(data["encrypted_dek"]),
    )


def _cache_dek_in_keyring(dek: bytes) -> None:
    keyring = _get_keyring_module()
    if keyring is None:
        return
    try:
        keyring.set_password(
            _KEYRING_SERVICE,
            _KEYRING_USERNAME,
            base64.b64encode(dek).decode("ascii"),
        )
    except Exception:
        # Keyring is a convenience layer only; ignore backend failures.
        pass


def _load_dek_from_keyring() -> bytes | None:
    keyring = _get_keyring_module()
    if keyring is None:
        return None
    try:
        stored = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    except Exception:
        return None
    if not stored:
        return None
    try:
        return base64.b64decode(stored)
    except Exception:
        return None


def clear_keyring_cache() -> None:
    keyring = _get_keyring_module()
    if keyring is None:
        return
    try:
        keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
    except Exception:
        pass


def initialize(master_password: str) -> Vault:
    """Create a brand-new vault protected by ``master_password``."""
    salt = os.urandom(_SALT_BYTES)
    dek = Fernet.generate_key()
    kek = _derive_kek(master_password, salt)
    encrypted_dek = Fernet(kek).encrypt(dek)
    _write_metadata(salt, encrypted_dek)
    _cache_dek_in_keyring(dek)
    return Vault(_dek=dek)


def unlock_with_keyring() -> Vault | None:
    """Try to unlock using the DEK cached in the OS keyring."""
    if not is_initialized():
        return None
    dek = _load_dek_from_keyring()
    if dek is None:
        return None
    # Sanity-check that the cached DEK is usable.
    try:
        Fernet(dek)
    except Exception:
        return None
    return Vault(_dek=dek)


def unlock_with_password(master_password: str) -> Vault:
    """Unlock the vault using the master password."""
    salt, encrypted_dek = _read_metadata()
    kek = _derive_kek(master_password, salt)
    try:
        dek = Fernet(kek).decrypt(encrypted_dek)
    except InvalidToken as exc:
        raise InvalidMasterPassword("Incorrect master password.") from exc
    _cache_dek_in_keyring(dek)
    return Vault(_dek=dek)


def change_master_password(old_password: str, new_password: str) -> None:
    """Re-encrypt the DEK under a new master password."""
    salt, encrypted_dek = _read_metadata()
    old_kek = _derive_kek(old_password, salt)
    try:
        dek = Fernet(old_kek).decrypt(encrypted_dek)
    except InvalidToken as exc:
        raise InvalidMasterPassword("Incorrect master password.") from exc
    new_salt = os.urandom(_SALT_BYTES)
    new_kek = _derive_kek(new_password, new_salt)
    new_encrypted = Fernet(new_kek).encrypt(dek)
    _write_metadata(new_salt, new_encrypted)
