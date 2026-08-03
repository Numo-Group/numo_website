# MEMORY.md — numo_website work history

Newest first. Captured from the build/deploy session (2026-06-08 → 09).

## 2026-08-03  2FA (TOTP) screen redesigned into the numo shell — v19.0.2.1.0 → .1.2
Reported from staging with a screenshot: `/web/login/totp` was still **stock Odoo** — purple button, bare Bootstrap `form-control`, an odoo.com "Learn More" link, and (because nothing on the page carried `.numo-page`) the **website marketing header + footer leaking in** around it. A 2FA sign-in therefore went numo → Odoo → numo.

### What changed
- **`views/login_templates.xml`** — new template **`numo_totp`** inheriting `auth_totp.auth_totp_form` at **`priority="100"`**, replacing `div.oe_login_form` with `numo_shell` + `<div class="form-inner numo-totp">` holding **three sibling forms** (code submit / re-send e-mail / logout-cancel — native has three too, and nested `<form>` is invalid HTML). Bilingual AR-RTL + EN off the same `ar` flag as `numo_login`. Branches on `user._mfa_type()` for the `totp_mail` variant (e-mail wording + address + "Re-send code"). Dropped Odoo's odoo.com docs link as off-brand.
- **`static/src/scss/login.scss`** (+~30 lines, inside the existing `/*rtl:begin:ignore*/`) — `.numo-totp*` block; the brand circle badge reuses the `numo-done__check` rule via a comma list rather than duplicating it.
- **`__manifest__.py`** — `auth_totp` added to `depends` (needed for `inherit_id`; stock community, already installed local/staging/prod), version `19.0.2.0.0` → **`19.0.2.1.0`**.

### Load-bearing details (do not "simplify")
- **`priority="100"`.** `auth_totp_mail` is installed and also inherits `auth_totp.auth_totp_form` at default priority 16, xpathing `//form/div[1]`, `//form[1]`, `//div[hasclass('border-top')]` — all inside the div we replace. Views apply in priority order, so at 100 its xpaths resolve first and only then get replaced. Lower it and **auth_totp_mail fails to load**. It is the only other view inheriting that template (checked across community + enterprise).
- **No `maxlength`, no `pattern` on the code input.** Authenticator apps render `123 456` and people paste that; the controller strips whitespace before `int()`, but `maxlength="6"` truncates the paste to `123 45` and `pattern="[0-9]*"` rejects it. Native Odoo omits both too. Added `autocomplete="one-time-code"` (OS autofill, native omits it) + `dir="ltr"`. ⚠️ **On its own this left the field with no constraint at all** (letters and unlimited length went in) — see the *Follow-up same day* section below, where an `oninput` sanitiser became the single length/charset control.
- **`letter-spacing` needs a matching `text-indent`.** CSS appends the letter-space *after* the last glyph, so a centred code sits visibly left of centre. `.45em` / `.45em` cancels it (13.5px at 30px font).
- **Selector must be `.input.numo-totp__code input` (0,3,1)**, not `.numo-totp__code input` (0,2,1) — the latter only *ties* `.numo-page .input input` and would win on source order alone.
- **No controller override.** `/web/login/totp` is `website=True`, so it already tracks the URL/negotiated language; `_numo_sync_lang()` exists only because `/web/login` and `/web/reset_password` are *not* website routes. Verified: in one browser, login and 2FA render the same language.

### Verified on local (odoo19_local, container `web-numo-local`)
- Combined `ir.ui.view` arch: apply order `auth_totp_mail(16) → numo_totp(100)`, `oe_login_form` and the odoo.com link gone, one `totp_token` input with no `maxlength`/`pattern`, 3 forms, remember input immediately followed by `span.box`.
- **62/62 browser checks** (CDP, headless Chrome) across desktop-AR 1440×900, desktop-EN, mobile-AR 390×844: shell renders, website header/footer compute to `display:none`, badge 74px gradient circle, code field 64px/30px/700/centred with `ls == indent == 13.5px`, paste of `123 456` survives, submit is `rgb(42,91,200)` (not Odoo purple), remember box white→brand with the check appearing, hero/trust/nav-links hidden at 390, **no element crossing the viewport edge**, 0 exceptions, 0 console errors.
- **26/26 functional** (curl + `odoo shell`, throwaway TOTP user, deleted after): login → 2FA redirect; wrong code re-renders 200 with the numo danger alert in Arabic (native `auth_totp/i18n/ar.po`, no hand-mapping); **a real computed TOTP code logs in** → 303 `/odoo` + `td_id` cookie + one `auth_totp.device` row; `totp_mail` branch shows the address (`dir=ltr`) + "Re-send code" + 3 csrf tokens; `/web/login` and `/web/reset_password` unregressed.
- Real overflow measured properly: `documentElement.scrollWidth == innerWidth` (1440 and 390), `scrollLeft 0`. Only 1px item is Odoo's own `o_skip_to_content` skip link.

### Harness gotchas that cost time (all mine, not the product's)
- `subprocess.run(..., text=True)` enables **universal newlines**, so curl's `\r\n\r\n` header terminator arrives as `\n\n` — splitting on CRLF yields an **empty body**, and every POST then 400s on CSRF.
- Hand-seeding a Netscape cookie jar (or passing a `Cookie:` header) makes curl **drop the server's `session_id`** → CSRF 400. Let curl own the jar; set language via `Accept-Language`.
- curl writes httpOnly cookies as **`#HttpOnly_<domain>`**, so "skip lines starting with `#`" hides exactly `session_id` and `td_id`.
- **A real browser User-Agent is required for the remember/trusted-device path**: stock `auth_totp` names the device with `user_agent.browser.capitalize()`, and curl's UA parses to `browser=None` → `AttributeError` → **500 after the 2FA check already succeeded**. Odoo bug, not ours.
- The web worker **caches `ir.config_parameter`**, so flipping `auth_totp.policy` from `odoo shell` (to force `totp_mail`) is invisible until `docker restart`. Policy captured and restored afterwards; confirmed back to `False`.
- `Page.captureScreenshot(captureBeyondViewport=True)` frames the **wrong horizontal slice on an RTL page** — it looks like catastrophic overflow. Viewport-only capture (plus `scrollWidth` measurement) showed the layout is clean.
- Reading `getComputedStyle` immediately after toggling the checkbox reports the **mid-transition** value (`.box` has `transition:.15s`) — a false failure. Settle ~400ms first.

### Follow-up same day — code field accepted letters and had no length cap (v19.0.2.1.1)
Two defects reported with screenshots of the deployed page: **14 digits typed straight in** (no cap, overflowing the box) and **`zxczxczxc…` accepted**, spellcheck-underlined in red.
- **Cause:** `inputmode="numeric"` is only a mobile **keyboard hint** — it restricts nothing on desktop. Having deliberately dropped `maxlength`/`pattern` (to protect a pasted `123 456`), nothing constrained the field at all. That protected the paste case and left everything else unbounded.
- **Fix:** inline **`oninput` sanitiser** — `var v = this.value.replace(/[^0-9]/g,'').slice(0,6); if (v !== this.value) this.value = v;` — plus `spellcheck="false"`, `autocorrect="off"`, `autocapitalize="off"`. Inline handlers are already the pattern in this file (the password eye toggle uses `onclick`), and website pages only strip `<script>` **tags**, not handler attributes.
- **`maxlength` stays absent, and that is now a tested decision.** A first pass added `maxlength="12"` as a no-JS backstop; it **failed a real case** — attributes cap the value *before* `oninput` runs, so pasting `"Your code is 123456 please"` was truncated to `"Your code is"` and sanitised to `""`. Dropped it: the sanitiser is the single length control, and a no-JS backstop is worthless on a page that needs the JS bundle anyway. Same reason `pattern="[0-9]*"` stays out (it rejects a spaced paste).
- Only reassigns when the value actually changed, so typing valid digits does not shunt the caret to the end.
- **Verified 22/22** with real CDP key events (`Input.insertText` per char = one input event per keystroke, like typing): `zxczxczxczxczxc` → `""`; the reported `23123123123123` → `231231`; `1a2b3c4d5e6f7g8h` → `123456`; pastes of `123 456` / `123-456` / `"  123456  "` / `"Your code is 123456 please"` all → `123456`; autofill-style programmatic set + `input` event sanitised; caret stays at index 3 after typing `123`; field still 64px/30px with `ls == indent == 13.5px` and 6 digits neither overflow nor scroll inside it. Then **26/26 functional re-run** — a real computed TOTP code still logs in, so the sanitiser did not break submission.

### Follow-up 2 — log-in arrow was not mirrored in Arabic (v19.0.2.1.2)
Reported from staging: the arrow beside **تسجيل الدخول** still pointed **right** in the RTL page. A log-in arrow is a **directional** glyph — it has to point the way the language reads.
- **Cause:** the whole of `login.scss` sits inside `/*rtl:begin:ignore*/`, so **rtlcss mirrors nothing in this file** — every RTL difference is hand-written (`[dir="rtl"] .numo-page …`, already the convention at lines ~132-137). The arrow simply had no such rule, so it never flipped. Confirmed the ignore holds: the rule is byte-identical in `web.assets_frontend.css` and `web.assets_frontend.rtl.css`.
- **Fix:** one rule — `[dir="rtl"] .numo-page .btn .ic{transform:scaleX(-1)}`.
- **It was wrong on three buttons, not one.** The same arrow SVG appears in `numo_login` (Sign in, line ~238), `numo_reset_done` (line ~410) and `numo_totp` (line ~523), so the login page had the identical bug. One class-based rule fixes all three; fixing only the 2FA button would have left the login page inconsistent.
- **Scoped to `.ic` deliberately** so non-directional button icons are untouched — verified `none` on the password eye-toggle and the passkey glyph, and the 2FA re-send **envelope** must not flip either. Any future arrow/chevron needs `.ic`; symmetric icons must not have it.
- Targets the `svg`, not the button, so `.btn--primary:hover{transform:translateY(-1px)}` is unaffected (checked).
- **Verified 14/14**: RTL 2FA + RTL login arrow = `matrix(-1, 0, 0, 1, 0, 0)` and sits on the reading-end (left of the label); LTR both = `none` and sits right of the label; non-`.ic` button icons all `none`; arrow still 19×19 inside the button; 0 console errors. Close-up screenshots confirm ← in Arabic, → in English.
- ⚠️ **Test-selector trap:** `.numo-page .btn--primary` matches the **nav "الرئيسية" pill first** (`a.btn.btn--primary.btn--sm`, which has no icon) — a `querySelector` on it returns a button with no `svg.ic` and reads as "the fix didn't apply". Use `form button.btn--primary`.

### Still open
- **NOT deployed to staging/prod.** `stg-erp-001.numo.sa` still shows the stock page (the follow-up screenshots came from a neutralized DB — confirm which before assuming staging is current). Staging now has **9** pushed commits pending (the 5 listed below + the four from this session); SCSS/QWeb → `-u numo_website` + restart.

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
