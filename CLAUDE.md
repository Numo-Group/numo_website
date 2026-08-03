# CLAUDE.md — numo Group Website & Login (`numo_website`)

> Project context for any agent working here. See `MEMORY.md` for the work history.
> **Merged module:** the former `numo_login` was folded into this one (2026-06-09). There is no separate login module anymore — login templates, scss, and the auth controller all live here.

## What this is
Odoo 19 module (depends on **`website`**, **`auth_signup`**, **`auth_totp`**) with two responsibilities:
1. **Marketing homepage** — branded **bilingual (AR-RTL default / EN-LTR)** page at the site root `/`. **Fully static** (client-side AR/EN toggle, no Odoo data), served **verbatim** for pixel-fidelity — no Bootstrap/website-theme interference.
2. **Branded login + password reset + 2FA** — reskins `web.login` / `web.login_layout` / `auth_signup.reset_password` / **`auth_totp.auth_totp_form`** (split-screen hero) while keeping Odoo's native auth intact (real `/web/login` POST, csrf, redirect, passkey/WebAuthn, MFA, reset). Defaults to Arabic; language pill toggles + remembers via cookie.

## How it works (important — not a normal QWeb website page)
- `controllers/main.py`:
  - `class NumoWebsite(Website)` **overrides the `/` route** (`index`) to return `static/src/home.html` via `request.make_response(...)`.
  - `class NumoHome` exposes `/numo-home` (same content) for direct testing.
  - The HTML is **read once and cached in a module-global `_CACHE`**.
- ⚠️ **Cache gotcha:** editing `static/src/home.html` does **nothing** until you **restart the container** (the cache only reloads on process start). This differs from a normal template.

## Files
- `__manifest__.py` (depends `website` + `auth_signup`; data: `views/login_templates.xml`; asset: `static/src/scss/login.scss` in `web.assets_frontend`)
- **Homepage:** `controllers/main.py` (`NumoWebsite` overrides `/`, `NumoHome` exposes `/numo-home`) · `static/src/home.html` (the whole page)
- **Login:** `controllers/login.py` (`NumoLoginHome(AuthSignupHome)` — picks render language for `web_login` / `web_auth_reset_password`) · `views/login_templates.xml` (QWeb reskin; templates `numo_shell`, `numo_trust`, `numo_login_layout`, `numo_login`, `numo_reset_password`, `numo_reset_done`, **`numo_totp`**) · `static/src/scss/login.scss`
- **2FA (`/web/login/totp`):** template **`numo_totp`** inherits `auth_totp.auth_totp_form` and replaces `div.oe_login_form` with the `numo_shell` + a purpose-built six-digit code field. No Python — the route is already `website=True`, so it picks up the language on its own (unlike `/web/login`, which is why only that one needs `_numo_sync_lang()`). Handles both `user._mfa_type()` branches: `totp` (authenticator app) and `totp_mail` (code e-mailed → extra "Re-send code" form + the address in the subtitle).
  - ⚠️ **`priority="100"` on `numo_totp` is load-bearing.** `auth_totp_mail` (installed) also inherits `auth_totp.auth_totp_form`, at the default priority 16, and its xpaths target `//form/div[1]`, `//form[1]` and `//div[hasclass('border-top')]` — all inside the div we replace. Views apply in priority order, so at 100 its xpaths still resolve first. Lower our priority and **`auth_totp_mail` fails to load**.
  - ⚠️ **The code input is constrained by an inline `oninput` sanitiser, NOT by `maxlength`/`pattern`.** `oninput` strips non-digits and slices to 6. This matters because `inputmode="numeric"` is only a mobile *keyboard hint* — on desktop it restricts nothing, so letters went in (spellcheck-underlined) and the field had no length cap at all. Both `maxlength` and `pattern` are deliberately absent: **they act before the sanitiser**, so any cap truncates a paste (`"123 456"` at `maxlength="6"` → `"123 45"`; `"Your code is 123456"` at `maxlength="12"` → `""`) and `pattern="[0-9]*"` rejects a spaced paste outright. The sanitiser handles typing, spaced/dashed pastes, prose pastes and OS autofill in one place, and only reassigns when the value changed so the caret is not shunted. Also carries `spellcheck="false"`/`autocorrect="off"`/`autocapitalize="off"`, plus `autocomplete="one-time-code"` (OS autofill) and `dir="ltr"` (digits read LTR on the RTL page). Inline handlers are the established pattern in this file — see the password eye toggle's `onclick`.
  - The 2FA screen is the **first consumer of the `.remember` CSS** in `login.scss` — that block existed from the start but no template used it. The checkbox must stay the immediate previous sibling of `<span class="box">` or `input:checked + .box` won't paint.
- **Images** `static/src/img/`: `logo.png` (homepage nav) · **`login-logo.png`** (login nav — distinct file) · `hero.webp` (shared) · `hero-ltr.webp` (login LTR) · **`clients/` (31 logos)** · **`accreditations/` (11 logos)**. All resolve to `/numo_website/static/src/img/…`.

## Design / theme
- ⚠️ **Directional glyphs need an explicit flip.** `login.scss` is entirely inside
  `/*rtl:begin:ignore*/`, so **rtlcss mirrors nothing in this file** — layout is handled by
  logical properties and hand-written `[dir="rtl"]` / `[dir="ltr"]` rules. The log-in arrow
  therefore needs `[dir="rtl"] .numo-page .btn .ic{transform:scaleX(-1)}`, which covers all
  three buttons that use it (`numo_login` Sign in, `numo_reset_done`, `numo_totp` Log in).
  Scoped to **`.ic`** on purpose: non-directional button icons must NOT flip (the password
  eye, the passkey glyph, the 2FA re-send envelope). Add `.ic` to any future arrow/chevron;
  leave it off symmetric icons.
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
