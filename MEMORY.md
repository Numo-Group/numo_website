# MEMORY.md — numo_website work history

Newest first. Captured from the build/deploy session (2026-06-08 → 09).

## 2026-07-08  Portal horizontal-overflow fix (SAR font canary) + hide homepage announce bar
Session on a staging bug report (`/my/orders/164` — "huge empty space you can scroll"). Dev copy → synced to deployed copy → `web-numo-local` / `odoo19_local` / http://127.0.0.1:8169/. Verified with **Playwright (`channel:'chrome'`)** measuring `document.documentElement.scrollWidth - clientWidth` before reporting.

### Portal horizontal overflow FIXED — commit `7fe7dc7` (pushed)
- **Root cause:** Odoo 19 injects a hidden `#sar-font-canary` probe (`position:absolute; left:-9999px`, plus inner `<span>`s) to detect whether the Saudi-Riyal (⃀) symbol font loaded. On layouts that don't clip it, it inflates the document by **~9999px** → a huge empty horizontal scroll band on any portal page rendering SAR amounts (sale orders / invoices). The existing pin in `login.scss` was scoped `body:has(.numo-page)` → **auth pages only**, so the customer portal was uncovered.
- **Fix:** `static/src/scss/login.scss` — dropped the `.numo-page` scope so `#sar-font-canary{inset-block-start:0!important;inset-inline-start:0!important;left:0!important;top:0!important}` applies across the whole frontend.
- **Proof (Playwright, RTL, `Accept-Language: ar`):** staging `/my/orders/164` overflow **9999px → 0px** after the rule applies. Local `/my/orders/140` reads 0px with OR without the fix at every width 800–2560 (local layout happens to clip the probe — that's why local never reproduced it and misled the first passes).
- ⚠️ **False starts (retracted):** first blamed the nested `<body>` (Odoo does emit a stray `<body data-bs-spy>` inside `#wrap` — invalid but HARMLESS; local order 140 has the same and renders fine), then "normal short-sidebar whitespace". Both wrong. **Lesson: drive a real browser (Playwright `scrollWidth`) from the start for layout bugs — static HTML/CSS grep was inconclusive.**
- **Deployed to LOCAL** (bundle rebuilt `86d8584`→`621163e`, rule now global, verified 0px overflow + clean RTL full-page screenshot). **STAGING NOT deployed.**

### Homepage announcement bar hidden — commit `01cfeb0` (pushed)
- Commented out the `.announce` block in `home.html` (the "NEW / نُمو الآن شركة مستقلّة…" top bar) per request. Markup kept, wrapped in one HTML comment (`ANNOUNCEMENT BAR (hidden 2026-07-08…)`) — uncomment to restore. Deployed local + restart; verified `.announce` absent from DOM + screenshot (page now opens straight to nav + hero).
- ⚠️ **This commit also swept in the previously-uncommitted 2026-07-02 markup** (announce + **conference**) because `git add home.html` staged the whole working tree. So the **`.conference` section (home.html ~line 441) is now LIVE / committed with PLACEHOLDER content.** The 07-02 "awaiting decision" is resolved-by-accident for announce (hidden), but the **conference card is now public with placeholder text — review/decide it** (supply real content or comment it out like announce).

### GlitchTip / status.numo.sa
- `https://status.numo.sa/amr-afifi/issues` = GlitchTip SPA, **login-gated**. API `/api/0/organizations/amr-afifi/issues/` → **401 Unauthorized**. Can't read issues without the user's session (paste, drive their logged-in browser profile, or authenticated `!`-prefixed curl). Headers healthy (X-Frame-Options DENY, CSP nonces, nosniff).

### Tooling note
- **Playwright is installed** in the npx cache: `NODE_PATH=/Users/amro/.npm/_npx/9833c18b2d85bc59/node_modules node <script>.cjs`, `chromium.launch({channel:'chrome'})`. RTL/Arabic view needs `locale:'ar-SA'` + `extraHTTPHeaders:{'Accept-Language':'ar-SA,ar;q=0.9'}` (server default lang is Arabic; a default en-US context renders the LTR English page instead).

### Still open for next session
- **Deploy to staging** `stg-erp-001.numo.sa`: **5** pushed commits now pending (`a30bef3`, `c1c303e`, `0aaa04a`, `7fe7dc7`, `01cfeb0`). SCSS/QWeb → `-u numo_website` + restart; html/controller → restart. Then confirm portal overflow gone + announce bar hidden.
- **Conference section** — now committed with placeholder content; supply real content or hide it.
- GlitchTip local-mirror decision (from 07-02) still pending.
- `.env` still uncommitted at repo root — confirm it's gitignored before any secrets.

## 2026-07-02  Arabic switcher fix, neutralize ribbon on home, login-500 fix, hidden sections, GlitchTip
Session on staging `stg-erp-001.numo.sa` bug reports. Worked in dev copy, synced each file to deployed copy (`/Users/amro/odoo19/stack/extra-addons/numo_website`, container **`web-numo-local`**, db **`odoo19_local`**, http://127.0.0.1:8169/), verified with curl + a Python urllib/cookiejar harness before reporting.

### ⚠️ CORRECTION to the 2026-06-09 "URL-driven language" notes below
- **This DB's website default lang is `ar_001` (url_code `ar`), and English is `en_US` (url_code `en`).** So **Arabic lives at `/` (no prefix), English lives at `/en`** — the OPPOSITE of the old memory (lines ~31/35 say "/ = English, /ar = Arabic"). That hardcoded `en=''/ar='/ar'` assumption WAS the switcher bug. Staging is the same (Arabic default). Confirmed via `SELECT default_lang_id … FROM website` → `ar_001`.

### Language switcher fix — commits `a30bef3` + `c1c303e` (pushed to main)
- **`numo_nav`** (`views/login_templates.xml`): stopped hardcoding `/ar`. Now derives prefixes from `request.website.default_lang_id` + each lang's `url_code` (default lang → no prefix, other lang → `/<url_code>`). **`request.lang` is a lightweight `LangData` (only `.code` is safe — NOT a recordset)**; pull real `res.lang` records via `request.website.language_ids.filtered(lambda l: l.code == …)`. Recordset subtraction `(langs - lang)` throws `TypeError` — don't.
- **`controllers/main.py`**: stamps resolved language onto `<html>` (`lang/dir/data-lang`) by rewriting `_HTML_OPEN_AR`→`_HTML_OPEN_EN` for English. **`home.html` JS now reads `html[data-lang]`** instead of guessing from `location.pathname` (old `/^\/ar/` logic was wrong here).
- **Cookie-bounce fix (`c1c303e`)**: a plain `<a href>` to the other-lang URL gets **redirected straight back** by Odoo when a `frontend_lang` cookie for the current lang exists ("stuck on one language"). Fix: pill routes through Odoo's own **`/website/lang/<url_code>?r=<target>`** (sets the cookie then redirects). Uses QWeb's injected `quote_plus` for the `r` param. Works JS-free (home + login).

### Neutralize watermark on the homepage — commit `0aaa04a` (pushed)
- Odoo's diagonal "Neutralized" ribbon comes from `website.neutralize_ribbon` (inherits `website.layout`) and only shows when `ir.config_parameter database.is_neutralized` is true. The static homepage bypasses `website.layout`, so it never got it.
- `controllers/main.py` now injects an identical ribbon (`_NEUTRALIZE_RIBBON`, style copied verbatim) before `</body>` when neutralized; text `_NEUTRALIZE_TEXT` = {"ar":"معطلة لأغراض الاختبار","en":"Neutralized"} (Odoo's own strings). Guarded by try/except; baked into the per-lang cache. Production DB is NOT neutralized → nothing injected (auto-clean).

### `/web/login` 500 FIXED — was orphan `numo_login` records (LOCAL DB only, NOT a repo change)
- Root cause: the old **`numo_login` module was still `state=installed` in `odoo19_local`** with **6 orphan `ir.ui.view`s** (folded into numo_website 06-09 but never uninstalled on this DB). Its `numo_login.numo_login` (id 3733) AND our `numo_website.numo_login` (3805) BOTH inherit base `web.login` (189) → collided on `//owl-component[@name='web.user_switch']` xpath → 500. The 500-error *page* itself also failed (web_studio user_switch xpath) which MASKED the real error.
- **Fix (local DB hygiene, no code/repo/staging change):** via `odoo shell -d odoo19_local` unlinked the 6 orphan views + their `ir_model_data` rows, set module `state='uninstalled'`, `cr.commit()`. Backup dumped to scratchpad first. Result: `/web/login` + `/en/web/login` → **200**, branding intact, 0 leftover `numo_login` refs. Staging was already clean (that's why it worked there).
- Note: `odoo shell` prints an `advanced_web_domain_widget` import traceback during registry load but STILL executes the command (recovers).

### "Hidden sections" — orphan CSS given markup (LOCAL PREVIEW, **UNCOMMITTED**, awaiting decision)
- `home.html` had full CSS for **`.announce`** (top announcement bar) and **`.conference`** (dark event card) with **zero markup** — and the i18n dict ALREADY had all keys (annChip/annMsg/annLink, confH2/confSub/confDate/confVenue/confCta/confSlot, both AR+EN). So they were designed, translated, then markup dropped.
- Added markup for both (announce bar above the sticky nav; conference card between testimonial and promos) with **placeholder** content. Deployed to LOCAL only, verified on `/` + `/en`. **NOT committed, NOT pushed.** User must decide: keep both / keep one / drop + optionally strip the ~26 orphan CSS rules; and supply real content (announce msg+link, event title/date/venue/image) if keeping.

### GlitchTip / status.numo.sa
- Sentry/GlitchTip config is in **`odoo.conf [sentry]`** (OCA `sentry` module, `server_wide_modules=base,web,sentry`), NOT env vars. `sentry_dsn = http://<key>@glitchtip-web:8000/1`.
- **`glitchtip-web` (docker) == the LOCAL mirror of `https://status.numo.sa`** (prod, host port 3001). Per `stack/glitchtip/DEPLOY.md`: local uses the docker hostname, "Production swaps this for the https domain." Same product, not two systems.
- The session-long `Failed to resolve 'glitchtip-web'` warnings = the 3 local glitchtip containers (`glitchtip-web`/`-postgres`/`-valkey`) were **stopped** (exited ~2wk). I started them (glitchtip-web is on `odoo-net-numo-local` so Odoo resolves it) → now HTTP 200, warnings gone. UI from host: http://127.0.0.1:8001.
- **User pushed back ("we only use status.numo.sa") — DECISION PENDING:** (1) stop the 3 local containers + `sentry_enabled=false` on local [default recommendation], (2) point local `sentry_dsn`→`https://status.numo.sa`, or (3) leave local mirror running. Containers have no restart policy (won't survive reboot).
- ⚠️ Security: `odoo.conf` embeds a GlitchTip DSN project key — keep odoo.conf out of public repos; rotate if leaked.

### Still open for next session
- **Decide the announce/conference sections** (content or drop) — then commit+push if keeping.
- **Decide GlitchTip local handling** (options above).
- **Deploy the 3 pushed commits to staging** (`a30bef3`, `c1c303e`, `0aaa04a`): QWeb change needs `-u numo_website` + restart; controller/html changes need restart. Then confirm pill href = `/website/lang/...` and ribbon on `/`.
- `.env` created empty at repo root (no creds). Confirm it's gitignored before any secrets.

## 2026-06-09 → 14  UX polish, single nav, reset auto-login, URL-driven lang, GitHub, staging
Worked in the **dev/working copy** (`/Users/amro/Downloads/Claude/numo_website`), then synced each change to the deployed copy `/Users/amro/odoo19/stack/extra-addons/numo_website` (mounted in **`web-numo-local`**, db **`odoo19_local`**, http://127.0.0.1:8169/), `-u numo_website` + restart, and **verified live before reporting** (curl + headless MS-Edge/Playwright via `channel:'msedge'`).

### Homepage (`static/src/home.html` — edit needs container restart, cache)
- Removed **قصّتنا** from the desktop nav (footer "قصّتنا" link later removed with the whole column).
- Added bilingual **awards subtitle** (`awardsSub`, AR+EN) under الإعتمادات title; styled `.awards__sub`.
- **Footer contact** (تواصل): address, `info@numo.sa` (mailto), two phones `920022136` + `+966500808104` (each its own `tel:` link, `footT4` added AR+EN).
- **Deleted the المجموعة footer column** (footC1 + قصّتنا/الإعتمادات/الوظائف/المركز الإعلامي); footer grid `1.4fr 1fr 1fr 1fr → 1.4fr 1fr 1fr`; removed dead i18n keys (footC1/footCareers/footPress).
- Footer copyright **2025 → 2026** (body + both dicts).
- **Scroll-reveal animations**: `[data-reveal]` fade+rise + IntersectionObserver in the inline JS, `prefers-reduced-motion` guard. Stagger is **row-based `(i%6)*60ms`** (capped ~300ms) so the 31-logo customers grid doesn't lag (was linear `i*90ms` ≈ 2.8s).

### ONE shared navbar (single source of truth)
- New QWeb template **`numo_website.numo_nav`** in `views/login_templates.xml`. Used by: home (controller renders it to a string and splices it at the `<!--NUMO_NAV-->` placeholder in home.html, cached **per language** in `_CACHE['en']`/`['ar']`), login/reset (`<t t-call>` from `numo_shell` with `nav_home=True`), and any future QWeb page.
- Uses **`logo.png`** everywhere now → **`login-logo.png` is unused** (only referenced in docs).
- CTA is context-aware: **"الرئيسية/Home"** on auth pages (`nav_home`), **"تسجيل الدخول/Sign in"** elsewhere.

### Reset-password flow (`controllers/login.py` + templates)
- Odoo 19 sets the new password but does NOT log in (`do_signup(do_login=False)`). Override **auto-logs-in after a *successful* token reset** (only when `super()` set `message` and no `error`; resolves login from token via `_signup_retrieve_info` BEFORE super), then shows a branded **`numo_reset_done`** interstitial ("Password changed successfully / تم تغيير كلمة المرور بنجاح") that **auto-forwards to `/odoo`** via an **HTTP `Refresh` response header** (inline `<script>` is stripped by Odoo's website sanitizer — confirmed). Redirect target sanitized to a local path.
- **Invalid/expired token**: friendly message ("…انتهت صلاحية الرابط… / This reset link has expired or was already used. Enter your email…"), shows the email field (`t-if="not token or invalid_token"`), clears the bad token on resubmit, button label switches to "Send reset link".
- Test user `reset_demo@numo.sa`; reset links are single-use (token embeds login_date → invalidated after the reset logs the user in). Generate via `partner.signup_prepare(signup_type="reset")` + `partner._generate_signup_token()` (Odoo 19 tokens are signed, not a stored field).

### Login page bug fixes
- **Phantom horizontal scroll / huge empty side area** (RTL only): Odoo JS injects an off-screen probe `#sar-font-canary` at `position:absolute; left:-9999px` (containing block = viewport) → expanded scrollWidth to ~11000px. Fix: `body:has(.numo-page) #sar-font-canary{left:0!important;top:0!important}` (still `visibility:hidden`). `overflow:clip`/`hidden` on html/body did NOT work (clip doesn't propagate from root; element re-applies inline pos).
- Hero **quote centered** on RTL (`[dir="rtl"] .numo-page .quote{align-items:center;text-align:center}`).

### URL-driven language (major refactor — URL is the single source of truth)
- **`/` = English (default, no prefix), `/ar` = Arabic** for home, login, reset, interstitial. Removed the old `numo_lang`/`numo_login_lang` cookie override (it was forcing content language to disagree with the URL — caused `/ar` showing English, reset-done in wrong lang).
- `login.py` now just syncs `request.update_context(lang=request.lang.code)` (request.lang is set correctly from the URL prefix even though `/web/login` isn't a website route — verified: `/ar/...` → ar_001, `/...` → en_US; `/en/...` redirects to no-prefix).
- `numo_nav` derives `ar`/`prefix`/`lang_switch` from `request.lang`; all hrefs are language-aware; the **language pill switches the whole page to the other-language URL**.
- ⚠️ **Gotcha:** Odoo's website auto-localizes `<a href>` (re-prepends the current lang) and was breaking the language switcher → added **`data-no-post-process="1"`** to every nav anchor (opt-out in `website/models/ir_qweb._post_processing_att`). Without it the English pill on `/ar` got forced back to `/ar`.
- `home.html` JS now picks language from `location.pathname` (`/^\/ar(\/|$)/`); removed the cookie + `#langBtn` toggle (the pill is a server-rendered link now). Home root path arrives stripped (`/`), but the lang prefix is NOT stripped at the bare root in `numo_nav`'s path calc → strip `/ar`|`/en` explicitly when building `lang_switch`.

### GitHub
- Created **`Numo-Group/numo_website`** (initial commit, `.gitignore` ignores .DS_Store/.idea/.claude-flow/__pycache__; 57 files incl. 46 img assets; no secrets). Now **PUBLIC** (per request). ⚠️ Repo includes CLAUDE.md/MEMORY.md with internal infra refs (erp.numo.sa, container/db names) — no creds; offered to strip them.

### Staging deploy (`stg_erp_001` / `web-stg-erp-001` / db container `db-stg-erp-001`)
- `numo_website` **updated cleanly** on staging (loaded 0.28s, assets cleared, web restarted, running).
- The deploy pipeline's only **FAIL** = fetching obsolete repo **`numo_odoo_login`** (the old separate login module — merged into `numo_website` on 06-09; does NOT exist in Numo-Group). **Fix: remove `numo_odoo_login` from the deploy script's repo list** on the staging/prod host. Deploy script is NOT in the local stack — it's on the server (host likely `contabo` 84.247.189.212; staging = staging-erp.numo.sa). Not yet done.

### Prod rollout (command provided, NOT executed)
- Container **`web-vm`** @ erp.numo.sa. Steps: sync code → backup (`pg_dump -Fc`) → `docker exec web-vm odoo -d <PROD_DB> -u numo_website --stop-after-init --no-http` → `docker restart web-vm` → if SCSS stale, clear `ir.attachment` `url like /web/assets/%` + restart → validate curls.
- **Still to confirm before prod:** `<PROD_DB>` name (local is odoo19_local), prod Postgres container, code-sync method, and whether the **merged module is already on prod** (if prod still runs old separate `numo_login`+`numo_website`, do the full merge rollout first).

### Asset / cache gotchas
- SCSS changes: a clean `odoo -u numo_website --stop-after-init` + restart rebuilds the bundle (hash changes). If a change doesn't show, **delete `ir.attachment` where `url =like '/web/assets/%'` + restart** (manually deleting attachments mid-session once failed to regenerate; a clean `-u` is reliable). Debug-render uncompiled assets via `?debug=assets`.
- `home.html` is read once into module-global `_CACHE` (now per-lang) → **edits need `docker restart web-numo-local`**.


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
