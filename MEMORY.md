# MEMORY.md — numo_website work history

Newest first. Captured from the build/deploy session (2026-06-08 → 09).

## 2026-06-09 — MERGED numo_login → numo_website (now one module)
- **`numo_login` folded into this module.** End state: a single Odoo module `numo_website` (display name **"numo Group — Website & Login"**, version **19.0.2.0.0**) owning both the marketing homepage and the branded login/reset.
- Manifest: `depends = ["website", "auth_signup"]`; `data = ["views/login_templates.xml"]`; asset `static/src/scss/login.scss` in `web.assets_frontend`.
- Controllers split by concern: `controllers/main.py` (homepage `/` + `/numo-home`) and `controllers/login.py` (`NumoLoginHome(AuthSignupHome)` — render-language picker for `web_login` / `web_auth_reset_password`). `__init__` imports both.
- Templates moved in (`numo_shell`, `numo_trust`, `numo_login_layout`, `numo_login`, `numo_reset_password`); all `t-call` external IDs rewritten `numo_login.* → numo_website.*`.
- Images: `hero.webp` was **byte-identical** → deduped. `logo.png` **differed** between the two → login's kept as a distinct **`login-logo.png`** (template + scss updated). `hero-ltr.webp` (login LTR) copied in. All resolve under `/numo_website/static/src/img/…`.
- **Dropped** the legacy `migrations/19.0.1.1.0/post-migrate.py` (`numo_app_loader` cleanup) — it was specific to numo_login's own upgrade chain, irrelevant to the fresh merged module.
- **Deployed to local** (`web-numo-local` / `odoo19_local`): uninstalled both old modules (0 leftover `ir_model_data` rows) → swapped disk addons (removed deployed `numo_login/`, deployed merged `numo_website/`) → `-i numo_website` → restart. Verified: `/`, `/numo-home`, `/web/login`, `/web/reset_password` all **200** with branded markers; `login-logo.png` + `hero-ltr.webp` + client/accreditation logos all serve **200**.
- **PROD NOT TOUCHED:** `erp.numo.sa` / `web-vm` still runs the old separate `numo_login` + `numo_website`. To roll out: uninstall `numo_login`, deploy merged `numo_website`, install/upgrade, restart.
- ⚠️ Early `-i` runs printed `numo_bi` / `numo_business_intelligence` import tracebacks — transient import-order noise from those unrelated broken modules; final install exited 0.

## 2026-06-09 — copied to Claude root
- Copied deployed `extra-addons/numo_website` → `/Users/amro/Downloads/Claude/numo_website` as a standalone dev/repo copy. Deployed copy untouched. The two will diverge — sync back to deploy.

## Built from the home-page design (this session)
- Source: `numo home page.zip` (`Numo Home.html` + `NUMO-HOME-HANDOFF.md`). The page was already on the **blue** scheme (handoff doc tokens were stale plum).
- Chosen architecture: **serve the static HTML verbatim** via a controller, NOT a QWeb `website.layout` page — to guarantee pixel-fidelity and avoid Bootstrap/theme bleed and CSS-scoping work.
  - `NumoWebsite(Website)` overrides `/` (`index`) → returns `static/src/home.html`.
  - `NumoHome` → `/numo-home` for testing.
  - HTML cached once in module-global `_CACHE` → **editing home.html needs a container restart**.
- Asset paths rewritten `assets/… → /numo_website/static/src/img/…`; nav "Sign in" rewritten `# → /web/login`. Copied 31 client logos + 11 accreditation logos + logo + hero (45 refs, all resolve, verified 200/image-png).
- Deployed: `-i numo_website` + restart; served at `http://127.0.0.1:8169/`. Verified nav/hero/sections render and a client logo serves 200.

## Width alignment (by another agent)
- Home container widened to match the login: `--maxw 1240px→1466px`, `.wrap/.nav__in/.announce__in` gutters `34px→40px`. Both pages' `.nav__in` now compute to 1466 / 40px padding. (Required a container restart due to the home.html cache.)

## Gotchas
- **Cache:** `home.html` is read once into `_CACHE`; any edit needs `docker restart web-numo-local`.
- `/` is owned by this controller now → the site root shows the marketing page for everyone (incl. staff); backend is at `/odoo` or `/web`.
- `numo_website` depends on `website` + `auth_signup` (both installed on odoo19_local).
- The homepage renders headlessly (inline CSS); the **login/reset** pages (now in this same module, ex-`numo_login`) need the Odoo JS runtime + the `web.assets_frontend` scss bundle.

## Open / future
- The `NUMO-HOME-HANDOFF.md` §2 design tokens still list OLD plum — stale vs the live blue.
- Becomes private repo `Numo-Group/numo_website`.
