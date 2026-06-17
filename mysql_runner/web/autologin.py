"""Auto-login helpers for phpMyAdmin.

The login form for phpMyAdmin's cookie auth varies between versions and themes,
so we match several known field selectors. The injected JavaScript fills the
username/password fields and submits the form. A guard flag on ``window`` keeps
us from re-submitting endlessly if a login fails.
"""

from __future__ import annotations

import json


def build_login_script(username: str, password: str) -> str:
    """Return JS that fills and submits the phpMyAdmin cookie login form.

    Returns ``true`` (as the JS result) when a login form was found and
    submitted, ``false`` otherwise.
    """
    user_js = json.dumps(username)
    pass_js = json.dumps(password)
    return f"""
(function () {{
    var userSelectors = ['#input_username', 'input[name="pma_username"]'];
    var passSelectors = ['#input_password', 'input[name="pma_password"]'];

    function findFirst(selectors) {{
        for (var i = 0; i < selectors.length; i++) {{
            var el = document.querySelector(selectors[i]);
            if (el) {{ return el; }}
        }}
        return null;
    }}

    var userField = findFirst(userSelectors);
    var passField = findFirst(passSelectors);
    if (!userField || !passField) {{
        return false;
    }}
    if (window.__mysqlRunnerSubmitted) {{
        return false;
    }}
    window.__mysqlRunnerSubmitted = true;

    userField.value = {user_js};
    passField.value = {pass_js};
    userField.dispatchEvent(new Event('input', {{ bubbles: true }}));
    passField.dispatchEvent(new Event('input', {{ bubbles: true }}));

    var form = passField.form || userField.form;
    if (form) {{
        if (typeof form.requestSubmit === 'function') {{
            form.requestSubmit();
        }} else {{
            form.submit();
        }}
        return true;
    }}
    return false;
}})();
"""


def build_login_form_present_script() -> str:
    """Return JS evaluating to ``true`` if a login form is on the page."""
    return """
(function () {
    var sel = ['#input_username', 'input[name="pma_username"]',
               '#input_password', 'input[name="pma_password"]'];
    for (var i = 0; i < sel.length; i++) {
        if (document.querySelector(sel[i])) { return true; }
    }
    return false;
})();
"""


# Dark theme applied as a filter so it works regardless of phpMyAdmin version.
_DARK_CSS = """
:root { background:#1e1e1e !important; }
html { background:#1e1e1e !important; }
html.__mysql_runner_dark {
    filter: invert(1) hue-rotate(180deg) !important;
    background:#1e1e1e !important;
}
html.__mysql_runner_dark img,
html.__mysql_runner_dark video,
html.__mysql_runner_dark canvas,
html.__mysql_runner_dark [style*="background-image"],
html.__mysql_runner_dark .icon,
html.__mysql_runner_dark svg {
    filter: invert(1) hue-rotate(180deg) !important;
}
"""


def build_dark_mode_script(enable: bool) -> str:
    """Return JS that toggles a dark theme on the current document.

    Uses a CSS ``invert`` filter (re-inverting media) so it adapts to any
    phpMyAdmin theme without targeting specific selectors.
    """
    css_js = json.dumps(_DARK_CSS)
    enable_js = "true" if enable else "false"
    return f"""
(function () {{
    var enable = {enable_js};
    var STYLE_ID = '__mysql_runner_dark_style';
    var existing = document.getElementById(STYLE_ID);
    if (!enable) {{
        if (existing) {{ existing.remove(); }}
        document.documentElement.classList.remove('__mysql_runner_dark');
        return;
    }}
    if (!existing) {{
        var style = document.createElement('style');
        style.id = STYLE_ID;
        style.textContent = {css_js};
        (document.head || document.documentElement).appendChild(style);
    }}
    document.documentElement.classList.add('__mysql_runner_dark');
}})();
"""


def build_startup_script(query: str) -> str:
    """Return JS that opens phpMyAdmin's SQL tab and fills ``query``.

    Best-effort across phpMyAdmin versions: it clicks the SQL tab link, then
    fills the CodeMirror editor (if present) or the raw ``#sqlquery`` textarea.
    A guard flag prevents it from running more than once per session.
    """
    query_js = json.dumps(query)
    return f"""
(function () {{
    var query = {query_js};
    if (!query || window.__mysqlRunnerStartupDone) {{ return false; }}

    function fill() {{
        var cm = document.querySelector('.CodeMirror');
        if (cm && cm.CodeMirror) {{
            cm.CodeMirror.setValue(query);
            return true;
        }}
        var ta = document.querySelector('#sqlquery, textarea[name="sql_query"]');
        if (ta) {{
            ta.value = query;
            ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
            return true;
        }}
        return false;
    }}

    // Already on a page that has a SQL box?
    if (fill()) {{ window.__mysqlRunnerStartupDone = true; return true; }}

    // Otherwise try to navigate to the SQL tab.
    var sqlLink = document.querySelector('a[href*="sql.php"], #topmenu a[href*="route=/table/sql"], a[href*="route=/sql"]');
    if (sqlLink) {{
        window.__mysqlRunnerStartupDone = true;
        sqlLink.click();
        return true;
    }}
    return false;
}})();
"""
