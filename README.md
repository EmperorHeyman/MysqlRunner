# MySQL Runner

> A WinSCP-style session manager for **phpMyAdmin** - store your servers once,
> then connect to any of them in isolated, auto-logging-in tabs.

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white">
  <img alt="PyQt6" src="https://img.shields.io/badge/GUI-PyQt6-41cd52?logo=qt&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

MySQL Runner handles only the **login and secure storage of credentials** - phpMyAdmin
itself does all the database work. Save a server's URL, username and password (encrypted
locally), then double-click to open it in a browser tab that logs you in automatically.
Open several servers side by side, each in its own isolated session.

---


<img width="1194" height="831" alt="image" src="https://github.com/user-attachments/assets/31e3e8d6-8f60-4373-9dbb-5a0fa7ca17d2" />


## Features

- **Encrypted credential vault** - a random Data Encryption Key protects every credential.
  The key is derived from your **master password** (PBKDF2-HMAC-SHA256) and cached in the
  **Windows Credential Manager**, so you rarely have to retype it. Nothing is ever written
  to disk in plaintext.
- **Saved server list with groups & search** - organise servers under collapsible groups
  (Production, Staging, Client Projects...) and filter instantly with the search box.
- **Auto-login** - fills and submits the phpMyAdmin cookie login form and answers HTTP
  Basic Auth prompts. Auth mode is auto-detected or can be forced per server.
- **Per-tab session isolation** - each tab gets its own in-memory cookie jar, so the same
  server can be open in two tabs without sharing a session. Closing a tab discards its cookies.
- **Session cloning** (`Ctrl+D`) - duplicate the current tab to get a second view into the
  **same** logged-in session (shared cookie jar) - inspect a table in one tab while you run a
  query in another.
- **Dark mode** (`Ctrl+Shift+D`) - injects a CSS filter to tame phpMyAdmin's bright theme.
- **Environment badges** - mark servers as Dev / Staging / **Production**; production tabs
  get a red dot and tint so you never run a destructive query on the wrong server.
- **Startup SQL** - optionally run a query automatically after login (e.g. `SET NAMES utf8;`).
- **Keyboard-driven "Zen Mode"** - hide the sidebar and drive everything from the keyboard.
- **Auto-lock on idle** - after 15 minutes of inactivity (configurable) the key is wiped
  from memory and the keyring cache is cleared. Step away safely.
- **Portable export / import** - export your connections to an encrypted `.mrx` file
  protected by a passphrase, and import them on another PC.
- **Tabbed multi-server workflow** - work with many MySQL servers at the same time.

---

## Keyboard shortcuts

| Shortcut            | Action                          |
| ------------------- | ------------------------------- |
| `Ctrl+B`            | Toggle the sidebar (Zen Mode)   |
| `Ctrl+Shift+D`      | Toggle dark mode                |
| `Ctrl+W`            | Close the current tab           |
| `Ctrl+D`            | Clone the current tab (session) |
| `Ctrl+Tab`          | Next tab                        |
| `Ctrl+Shift+Tab`    | Previous tab                    |
| `Ctrl+1` … `Ctrl+9` | Jump to tab 1–9                 |

---

## Getting started

Requires **Windows** and **Python 3.10+**.

```powershell
git clone https://github.com/<your-username>/mysql-runner.git
cd mysql-runner
python -m pip install -r requirements.txt
python main.py
```

On first launch you'll set a **master password**. Then:

1. Click **Add** and enter the server's display name, URL, username and password.
   Optionally set a group, environment level and startup SQL.
2. Double-click the server (or select it and press **Connect**) to open a tab that
   logs you in automatically.
3. Use **File → Export / Import** to move your connections between machines.

---

## Building a standalone `.exe`

A [PyInstaller](https://pyinstaller.org/) spec is included that bundles the Qt WebEngine
runtime:

```powershell
python -m pip install -r requirements.txt
pyinstaller MySQLRunner.spec
```

The executable is produced at `dist/MySQLRunner/MySQLRunner.exe` (a one-folder build,
which is the most reliable mode for Qt WebEngine).

---

## Project layout

```
main.py                          Entry point
MySQLRunner.spec                 PyInstaller build spec
mysql_runner/
  app.py                         Bootstrap: unlock vault -> main window, idle auto-lock
  paths.py                       Per-user AppData file locations
  crypto/vault.py                DEK/KEK, keyring + master-password, Fernet
  storage/models.py              ServerProfile (groups, environment, startup SQL)
  storage/store.py               Encrypted load/save of profiles
  storage/settings.py            Plain-JSON UI preferences
  storage/portable.py            Passphrase-encrypted export/import (.mrx)
  ui/main_window.py              Grouped sidebar + search, tabs, menus, shortcuts
  ui/server_dialog.py            Add/edit server
  ui/master_password_dialog.py   Set / unlock dialogs
  ui/idle_watcher.py             Global idle auto-lock timer
  web/profile_factory.py         Isolated in-memory profile per tab
  web/browser_tab.py             QWebEngineView + auto-login + dark mode + startup SQL
  web/autologin.py               phpMyAdmin login / dark-mode / startup JavaScript
```

---

## Security notes

- Files live under `%APPDATA%\MySQLRunner\` (`vault.json`, `servers.enc`, `settings.json`).
- Credentials are stored encrypted; the key lives in memory only while the app runs and is
  wiped on **Lock** or idle auto-lock.
- Exported `.mrx` files are encrypted with a passphrase you choose — keep that passphrase safe.
- This tool only handles login and credential storage; all database operations happen inside
  phpMyAdmin.

---

## License

Released under the MIT License. See [LICENSE](LICENSE).








