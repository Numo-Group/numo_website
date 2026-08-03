{
    "name": "numo Group — Website & Login",
    "version": "19.0.2.1.0",
    "summary": "Branded bilingual (AR/EN) marketing homepage + login screen for numo Group",
    "description": """
numo Group — Website & Login
============================
Single module that delivers the branded bilingual (Arabic RTL default +
English LTR) numo Group experience for the public site and backend auth:

* Marketing homepage served verbatim at the site root (/) from
  static/src/home.html — fully static, client-side AR/EN toggle, so it
  renders pixel-identical to the approved design with no website-theme
  interference.
* Branded split-screen login + password reset that reskins
  web.login / web.login_layout / auth_signup.reset_password while keeping
  Odoo's native authentication (real /web/login POST, csrf_token, redirect,
  passkey/WebAuthn, MFA, password reset) fully intact.
* The two-factor step (/web/login/totp) is skinned into the same shell, with a
  purpose-built six-digit code field, so a 2FA sign-in never drops the user onto
  a stock Odoo screen mid-flow. Native TOTP auth (totp_token, remember /
  trusted-device cookie, e-mailed codes, logout-cancel) is unchanged.

Login/reset default to Arabic (RTL); users switch with the language pill,
remembered in a cookie. Logical CSS properties mirror the layout for RTL/LTR.

(Merged from the former numo_login + numo_website modules.)
""",
    "category": "Website",
    "author": "Numo",
    "website": "https://numo.sa",
    "license": "LGPL-3",
    # auth_totp is required for the numo_totp view's inherit_id to resolve. It is
    # a stock community module and is already installed on local, staging and prod.
    "depends": ["website", "auth_signup", "auth_totp"],
    "data": [
        "views/login_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "numo_website/static/src/scss/login.scss",
        ],
    },
    "images": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
