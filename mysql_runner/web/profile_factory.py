"""Factory for isolated, off-the-record web engine profiles.

Each browser tab receives its own off-the-record :class:`QWebEngineProfile`.
Off-the-record profiles keep all cookies and cache in memory only, so:

* Two tabs pointing at the same server never share a session.
* Closing a tab (and dropping its profile) discards every cookie it held.
"""

from __future__ import annotations

import uuid

from PyQt6.QtWebEngineCore import QWebEngineProfile


def create_isolated_profile(parent=None) -> QWebEngineProfile:
    """Create a unique in-memory profile for a single tab.

    The caller must keep a reference to the returned profile alive for the
    lifetime of the tab (e.g. by parenting it to the view).
    """
    # A unique storage name guarantees the profile does not collide with any
    # other; passing no persistent name keeps it off-the-record (in-memory).
    profile = QWebEngineProfile(parent)
    profile.setObjectName(f"mysql-runner-{uuid.uuid4().hex}")
    # Off-the-record profiles already use NoPersistentCookies; set explicitly
    # for clarity and to stay robust across versions.
    profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
    )
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
    return profile
