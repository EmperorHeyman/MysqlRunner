MySQL Runner
============

> A WinSCP-style session manager for **phpMyAdmin** store your servers once,then connect to any of them in isolated, auto-logging-in tabs.

MySQL Runner handles only the **login and secure storage of credentials** phpMyAdminitself does all the database work. Save a server's URL, username and password (encryptedlocally), then double-click to open it in a browser tab that logs you in automatically.Open several servers side by side, each in its own isolated session.

Features
--------

*   **Encrypted credential vault** a random Data Encryption Key protects every credential.The key is derived from your **master password** (PBKDF2-HMAC-SHA256) and cached in the**Windows Credential Manager**, so you rarely have to retype it. Nothing is ever writtento disk in plaintext.
    
*   **Saved server list with groups & search** organise servers under collapsible groups(Production, Staging, Client Projects…) and filter instantly with the search box.
    
*   **Auto-login** fills and submits the phpMyAdmin cookie login form and answers HTTPBasic Auth prompts. Auth mode is auto-detected or can be forced per server.
    
*   **Per-tab session isolation** each tab gets its own in-memory cookie jar, so the sameserver can be open in two tabs without sharing a session. Closing a tab discards its cookies.
    
*   **Session cloning** (Ctrl+D) duplicate the current tab to get a second view into thesame logged-in session (shared cookie jar) inspect a table in one tab while you run aquery in another.
    
*   **Dark mode** (Ctrl+Shift+D) injects a CSS filter to tame phpMyAdmin's bright theme.
    
*   **Environment badges** mark servers as Dev / Staging / **Production**; production tabsget a red dot and tint so you never run a destructive query on the wrong server.
    
*   **Startup SQL** optionally run a query automatically after login (e.g. SET NAMES utf8;).
    
*   **Keyboard-driven "Zen Mode"** hide the sidebar and drive everything from the keyboard.
    
*   **Auto-lock on idle** after 15 minutes of inactivity (configurable) the key is wipedfrom memory and the keyring cache is cleared. Step away safely.
    
*   **Portable export / import** export your connections to an encrypted .mrx fileprotected by a passphrase, and import them on another PC.
    
*   **Tabbed multi-server workflow** work with many MySQL servers at the same time.
    

Keyboard shortcuts
------------------

Shortcut

Action

Ctrl+B

Toggle the sidebar (Zen Mode)

Ctrl+Shift+D

Toggle dark mode

Ctrl+W

Close the current tab

Ctrl+D

Clone the current tab (session)

Ctrl+Tab

Next tab

Ctrl+Shift+Tab

Previous tab

Ctrl+1 ... Ctrl+9

Jump to tab 1-9

Getting started
---------------

Requires **Windows** and **Python 3.10+**.

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   git clone [https://github.com/](https://github.com/)/mysql-runner.git  cd mysql-runner  python -m pip install -r requirements.txt  python main.py   `

On first launch you'll set a **master password**. Then:

1.  Click **Add** and enter the server's display name, URL, username and password.Optionally set a group, environment level and startup SQL.
    
2.  Double-click the server (or select it and press **Connect**) to open a tab thatlogs you in automatically.
    
3.  Use **File → Export / Import** to move your connections between machines.
    

Building a standalone .exe
--------------------------

A [PyInstaller](https://pyinstaller.org/) spec is included that bundles the Qt WebEngineruntime:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python -m pip install -r requirements.txt  pyinstaller MySQLRunner.spec   `

The executable is produced at dist/MySQLRunner/MySQLRunner.exe (a one-folder build,which is the most reliable mode for Qt WebEngine).

Project layout
--------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   main.py                          Entry point  MySQLRunner.spec                 PyInstaller build spec  mysql_runner/    app.py                         Bootstrap: unlock vault -> main window, idle auto-lock    paths.py                       Per-user AppData file locations    crypto/vault.py                DEK/KEK, keyring + master-password, Fernet    storage/models.py              ServerProfile (groups, environment, startup SQL)    storage/store.py               Encrypted load/save of profiles    storage/settings.py            Plain-JSON UI preferences    storage/portable.py            Passphrase-encrypted export/import (.mrx)    ui/main_window.py              Grouped sidebar + search, tabs, menus, shortcuts    ui/server_dialog.py            Add/edit server    ui/master_password_dialog.py   Set / unlock dialogs    ui/idle_watcher.py             Global idle auto-lock timer    web/profile_factory.py         Isolated in-memory profile per tab    web/browser_tab.py             QWebEngineView + auto-login + dark mode + startup SQL    web/autologin.py               phpMyAdmin login / dark-mode / startup JavaScript   `

Security notes
--------------

*   Files live under %APPDATA%\\MySQLRunner\\ (vault.json, servers.enc, settings.json).
    
*   Credentials are stored encrypted; the key lives in memory only while the app runs and iswiped on **Lock** or idle auto-lock.
    
*   Exported .mrx files are encrypted with a passphrase you choose keep that passphrase safe.
    
*   This tool only handles login and credential storage; all database operations happen insidephpMyAdmin.
    

License
-------

Released under the MIT License. See [LICENSE](LICENSE).