# CLAUDE.md — numo Group Website & Login (`numo_website`)

> Project context for any agent working here. See `MEMORY.md` for the work history.
> **Merged module:** the former `numo_login` was folded into this one (2026-06-09). There is no separate login module anymore — login templates, scss, and the auth controller all live here.

## What this is
Odoo 19 module (depends on **`website`**, **`auth_signup`**) with two responsibilities:
1. **Marketing homepage** — branded **bilingual (AR-RTL default / EN-LTR)** page at the site root `/`. **Fully static** (client-side AR/EN toggle, no Odoo data), served **verbatim** for pixel-fidelity — no Bootstrap/website-theme interference.
2. **Branded login + password reset** — reskins `web.login` / `web.login_layout` / `auth_signup.reset_password` (split-screen hero) while keeping Odoo's native auth intact (real `/web/login` POST, csrf, redirect, passkey/WebAuthn, MFA, reset). Defaults to Arabic; language pill toggles + remembers via cookie.

## How it works (important — not a normal QWeb website page)
- `controllers/main.py`:
  - `class NumoWebsite(Website)` **overrides the `/` route** (`index`) to return `static/src/home.html` via `request.make_response(...)`.
  - `class NumoHome` exposes `/numo-home` (same content) for direct testing.
  - The HTML is **read once and cached in a module-global `_CACHE`**.
- ⚠️ **Cache gotcha:** editing `static/src/home.html` does **nothing** until you **restart the container** (the cache only reloads on process start). This differs from a normal template.

## Files
- `__manifest__.py` (depends `website` + `auth_signup`; data: `views/login_templates.xml`; asset: `static/src/scss/login.scss` in `web.assets_frontend`)
- **Homepage:** `controllers/main.py` (`NumoWebsite` overrides `/`, `NumoHome` exposes `/numo-home`) · `static/src/home.html` (the whole page)
- **Login:** `controllers/login.py` (`NumoLoginHome(AuthSignupHome)` — picks render language for `web_login` / `web_auth_reset_password`) · `views/login_templates.xml` (QWeb reskin; templates `numo_shell`, `numo_trust`, `numo_login_layout`, `numo_login`, `numo_reset_password`) · `static/src/scss/login.scss`
- **Images** `static/src/img/`: `logo.png` (homepage nav) · **`login-logo.png`** (login nav — distinct file) · `hero.webp` (shared) · `hero-ltr.webp` (login LTR) · **`clients/` (31 logos)** · **`accreditations/` (11 logos)**. All resolve to `/numo_website/static/src/img/…`.

## Design / theme
- **Blue scheme matching `numo_login`** (`--plum-strong:#2A5BC8`, etc. — same blue tokens; names kept as `--plum*`). Two plum→blue gradient accent bands (Stats + CTA).
- Sections: sticky nav · hero (+120 partners badge) · partners · stats · about · why-numo · CTA · footer.
- **Container width matched to the login**: `--maxw:1466px`, gutters `40px` (so home and login align).
- Nav "Sign in" → `/web/login` (now styled by this same module's `login_templates.xml`).
- RTL/LTR via logical CSS props + a client-side `data-i18n` toggle in the inline `<script>`.

## Deploy / dev (local)
- **This dir is a dev/working copy.** Deployed copy: `/Users/amro/odoo19/stack/extra-addons/numo_website`, mounted into container **`web-numo-local`**, db **`odoo19_local`**, served at **http://127.0.0.1:8169/**.
- Install/update the module:
  ```bash
  docker exec web-numo-local odoo -d odoo19_local -u numo_website --stop-after-init --no-http
  docker restart web-numo-local
  ```
- **After editing `home.html`: `docker restart web-numo-local`** (clears the in-memory cache). No module update needed for HTML-only changes.
- Don't grep/read the whole `static/src/img/` tree casually — it's many logos.

## Repo target
Private repo `Numo-Group/numo_website`. Design source: `numo home page.zip` / `NUMO-HOME-HANDOFF.md`.
Consider gitignoring large vendored assets if any creep in.
