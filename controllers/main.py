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
        if _NAV_PLACEHOLDER in raw:
            try:
                # numo_nav derives language + hrefs from request.lang (URL prefix)
                nav = request.env["ir.qweb"]._render("numo_website.numo_nav", {})
                composed = raw.replace(_NAV_PLACEHOLDER, str(nav))
            except Exception:
                composed = raw.replace(_NAV_PLACEHOLDER, "")  # never break the page
        else:
            composed = raw
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
