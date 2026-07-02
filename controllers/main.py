# -*- coding: utf-8 -*-
import os

from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website

_HOME_HTML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "src", "home.html",
)
_CACHE = {}


_NAV_PLACEHOLDER = "<!--NUMO_NAV-->"

# home.html ships as Arabic; we rewrite the opening <html> tag to the language
# the server actually resolved so the client-side toggle trusts it (see below).
_HTML_OPEN_AR = '<html lang="ar" dir="rtl" data-lang="ar">'
_HTML_OPEN_EN = '<html lang="en" dir="ltr" data-lang="en">'

# Odoo shows a diagonal "Neutralized" watermark on backend/website pages when the
# database is neutralized (staging/dev copies of prod). The homepage is served
# verbatim and never renders through website.layout, so it misses that ribbon.
# We inject an identical one ourselves. Style is copied verbatim from
# website.neutralize_ribbon; text uses Odoo's own EN/AR strings. On a real
# production DB, database.is_neutralized is falsy so nothing is injected.
_NEUTRALIZE_RIBBON = (
    '<span id="oe_neutralize_ribbon" style="'
    "width:400px;top:55px;left:-100px;font-size:32px;text-align:center;"
    "padding:10px;line-height:30px;color:#F0F0F0;transform:rotate(-45deg);"
    "position:fixed;box-shadow:0 0 3px rgba(0,0,0,0.3);background:#D0442C;"
    "opacity:0.6;pointer-events:none;text-transform:uppercase;z-index:9999;"
    '">{text}</span>'
)
_NEUTRALIZE_TEXT = {"ar": "معطلة لأغراض الاختبار", "en": "Neutralized"}


def _home_html():
    """Serve the static homepage with the shared navbar spliced in.

    The navbar is the single shared QWeb template ``numo_website.numo_nav``
    (also used by login/reset). It computes its language + hrefs from
    ``request.lang`` (the URL prefix), so the homepage at ``/`` gets the English
    nav and ``/ar`` gets the Arabic nav. The composed page is cached per language
    (``_CACHE['en']`` / ``_CACHE['ar']``); the raw file is read once.
    """
    raw = _CACHE.get("raw")
    if raw is None:
        with open(_HOME_HTML_PATH, encoding="utf-8") as fh:
            raw = fh.read()
        _CACHE["raw"] = raw

    lang = request.lang
    is_ar = bool(lang) and (getattr(lang, "code", "") or "").startswith("ar")
    key = "ar" if is_ar else "en"

    composed = _CACHE.get(key)
    if composed is None:
        # Stamp the resolved language onto <html> so the client-side toggle in
        # home.html can trust it, instead of re-guessing from the URL path
        # (which breaks when Arabic — not English — is the site default).
        body = raw if is_ar else raw.replace(_HTML_OPEN_AR, _HTML_OPEN_EN, 1)
        if _NAV_PLACEHOLDER in body:
            try:
                # numo_nav derives language + hrefs from request.lang (URL prefix)
                nav = request.env["ir.qweb"]._render("numo_website.numo_nav", {})
                composed = body.replace(_NAV_PLACEHOLDER, str(nav))
            except Exception:
                composed = body.replace(_NAV_PLACEHOLDER, "")  # never break the page
        else:
            composed = body
        # Splice in the neutralize ribbon (dev/staging only; see constant above).
        try:
            if request.env["ir.config_parameter"].sudo().get_param("database.is_neutralized"):
                ribbon = _NEUTRALIZE_RIBBON.format(text=_NEUTRALIZE_TEXT[key])
                composed = (
                    composed.replace("</body>", ribbon + "</body>", 1)
                    if "</body>" in composed else composed + ribbon
                )
        except Exception:
            pass  # never break the page over a dev-only watermark
        _CACHE[key] = composed
    return composed


def _home_response():
    return request.make_response(
        _home_html(),
        headers=[("Content-Type", "text/html; charset=utf-8")],
    )


class NumoWebsite(Website):
    """Override the site root so the branded numo homepage is served at /."""

    @http.route("/", type="http", auth="public", website=True, sitemap=True)
    def index(self, **kw):
        return _home_response()


class NumoHome(http.Controller):
    """Stable direct route, handy for testing / direct linking."""

    @http.route("/numo-home", type="http", auth="public", website=True, sitemap=False)
    def numo_home(self, **kw):
        return _home_response()
