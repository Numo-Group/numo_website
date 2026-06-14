from odoo import http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

# Login/reset language follows the URL prefix (Odoo website lang routing):
#   /web/login        → English (default, no prefix)
#   /ar/web/login     → Arabic
# So the URL is the single source of truth for language — it always matches the
# language shown and the homepage. We only (a) make sure the render language
# tracks request.lang even though /web/login isn't a website route, and
# (b) auto-login after a successful password reset + show the branded interstitial.


class NumoLoginHome(AuthSignupHome):

    def _numo_sync_lang(self):
        """Force the render language to follow the URL prefix (request.lang)."""
        lang = request.lang
        code = getattr(lang, "code", None) if lang else None
        if code:
            request.update_context(lang=code)

    @http.route()
    def web_login(self, *args, **kw):
        self._numo_sync_lang()
        return super().web_login(*args, **kw)

    @http.route()
    def web_auth_reset_password(self, *args, **kw):
        self._numo_sync_lang()

        # --- Auto-login after a *successful* token reset ---------------------
        # Native Odoo 19 sets the new password but does NOT log the user in
        # (do_signup(..., do_login=False)) and just shows a success page. Users
        # expect to be signed straight in, so once super() confirms the reset
        # succeeded we authenticate with the freshly-set password and redirect.
        # We delegate the entire reset (password match, weak-password and token
        # validation, DB commit) to super() so all native safeguards stay intact.
        login = None
        if request.httprequest.method == "POST" and kw.get("token"):
            try:
                info = request.env["res.partner"].sudo()._signup_retrieve_info(kw["token"])
                login = (info or {}).get("login")  # present for an existing user
            except Exception:
                login = None

        response = super().web_auth_reset_password(*args, **kw)

        if login and kw.get("password"):
            qctx = getattr(response, "qcontext", {}) or {}
            # success == Odoo set a confirmation message and raised no error
            if qctx.get("message") and not qctx.get("error"):
                try:
                    request.session.authenticate(
                        request.env,
                        {"login": login, "password": kw["password"], "type": "password"},
                    )
                    # logged in → show a brief "password changed" confirmation,
                    # then auto-forward to the backend. Only allow a local path as
                    # the redirect target (no open redirect off-site).
                    target = kw.get("redirect") or "/odoo"
                    if not (isinstance(target, str) and target.startswith("/")):
                        target = "/odoo"
                    resp = request.render("numo_website.numo_reset_done", {"redirect": target})
                    # Auto-forward to the dashboard after a short pause so the
                    # "password changed" confirmation is visible. An HTTP Refresh
                    # header is used because website pages strip inline <script>.
                    resp.headers["Refresh"] = "2; url=%s" % target
                    return resp
                except Exception:
                    # MFA / any auth hurdle → leave the native success page,
                    # whose message now reads "password reset successfully".
                    pass

        return response
