# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

@AGENTS.md

`AGENTS.md` is the short entry point: what this repo owns, conventions, and the
command set. Everything below is the al-folio v1 architecture that those rules
assume but don't spell out.

## What this repo is

**Guohao Zhang's personal academic homepage** (<https://colehank.github.io>),
built on al-folio v1.x. It is a _consumer_ of the al-folio plugin ecosystem, not
the template repo — the demo content, visual-regression tests, and upstream
contributor tooling that ship with the starter have been removed.

This repo owns content + wiring. **All runtime — layouts, includes, Sass, Liquid
tags and filters, feature JS — lives in versioned gems** published on RubyGems.
`docs/BOUNDARIES.md` is the authoritative area→gem ownership table.

The biggest recurring mistake is editing runtime here. If a change is
layout/include/tag/filter/feature behavior, it belongs in the owning gem (see
the table below), or must be a deliberate, tracked local override.

## The plugin ecosystem

**`al_folio_core` is the hub.** `_config.yml` sets `theme: al_folio_core`; the
gem ships every base `_layouts/*.liquid` and `_includes/*.liquid`, the base theme
JS/CSS, and the `details`/`file_exists` tags + `hideCustomBibtex`/`remove_accents`
filters. Its `_includes/plugins/*.liquid` are **thin wrappers that call custom
Liquid tags defined by sibling gems**. A feature renders only when _both_ (a) its
gem is in the plugin list, and (b) the relevant flag is on:

| Wrapper / call site | Tag                                                 | Gem                                                        |
| ------------------- | --------------------------------------------------- | ---------------------------------------------------------- |
| search assets       | `al_search_assets`                                  | `al_search` (Cmd-K palette; index built at build time)     |
| comments            | `al_comments`                                       | `al_comments` (Giscus + Disqus, front-matter gated)        |
| cookie banner       | `al_cookie_styles` / `al_cookie_scripts`            | `al_cookie` (consent-mode gating of analytics)             |
| icon `<link>`s      | `al_icons_styles`                                   | `al_icons` (FontAwesome/Academicons/Scholar Icons via CDN) |
| analytics           | `al_analytics_scripts`                              | `al_analytics` (GA/Cronitor/Pirsch/OpenPanel)              |
| math                | `al_math_styles` / `al_math_scripts`                | `al_math` (MathJax, pseudocode.js, TikZJax)                |
| charts              | `al_charts_scripts`                                 | `al_charts` (Mermaid/Chart.js/ECharts/Plotly/Vega/Leaflet) |
| image tools         | `al_img_tools_styles` / `al_img_tools_scripts`      | `al_img_tools` (zoom, lightbox, sliders, galleries)        |
| newsletter          | `al_newsletter_form` / `al_newsletter_scripts`      | `al_newsletter` (Loops.so signup)                          |
| `layout: cv`        | `al_folio_cv_render`                                | `al_folio_cv` (RenderCV YAML + JSONResume) — **used here** |
| `layout: distill`   | `al_folio_distill_render`                           | `al_folio_distill` (vendored, hash-pinned distillpub)      |
| citation badges     | `google_scholar_citations` / `inspirehep_citations` | `al_citations` — **used here**                             |
| external posts      | (generator, no tag)                                 | `al_ext_posts` (RSS/URL ingestion → synthetic posts)       |
| legacy Bootstrap    | (opt-in assets)                                     | `al_folio_bootstrap_compat`                                |
| upgrade/audit CLI   | `bundle exec al-folio …`                            | `al_folio_upgrade`                                         |

The gems are developed as sibling repos at `~/Documents/dev/al-org/<repo>` (repo
dir uses hyphens, `al-folio-core`; gem id uses underscores, `al_folio_core`). To
test a gem fix against this site: `gem "al_folio_core", path: "../al-folio-core"`
in the `Gemfile`, then `bundle install`.

Architectural facts:

- **Feature gating is two-layered.** Site-wide config flags (`search_enabled`,
  `enable_math`, `enable_cookie_consent`, `enable_darkmode`,
  `al_folio.features.cv.enabled`, `al_folio.features.distill.enabled`) _and_
  per-page front matter (`images:`, `tikzjax`, `chart.*`, `mermaid.*`,
  `giscus_comments`, `layout: distill|cv`). A tag emits an empty string when its
  gem/flag is absent — **features fail silently, not loudly.**
- **Most feature gems are `AssetsGenerator`s** that inject JS/CSS as Jekyll
  static files at build time only when enabled. Several use pinned-CDN URLs +
  SRI hashes from `_config.yml`'s `third_party_libraries:` block.
- **Two parallel lists must stay in sync:** `Gemfile` (pinned versions) and
  `_config.yml`'s `plugins:` list.
- **The v1 config contract** (`al_folio.api_version: 1`, `style_engine: tailwind`,
  `tailwind.{version,css_entry,preflight}`, `distill.{engine,source}`) is enforced
  as build-time warnings by `al_folio_core`'s `:after_init` hook and as blocking
  findings by `al-folio upgrade audit`. Don't remove these keys.
- **Local overrides are allowed but must be tracked.** A site may shadow a
  gem-owned `_layouts`/`_includes`/`_sass` file. When it does, run
  `bundle exec al-folio upgrade overrides audit` — it records owner gem, version,
  and upstream/local SHA256 in `.al-folio-overrides.yml`, which must be committed
  so future `bundle update`s can flag upstream drift. **This repo currently has
  no local overrides; keep it that way if you can.**
- **Bootstrap compat is opt-in and time-boxed.** `al_folio.compat.bootstrap.enabled`
  (default false, and false here). Supported through v1.2, deprecated v1.3,
  removed in v2.0.

## Customizing style

Site-wide CSS overrides live in **one** place: the `footer_text` block in
`_config.yml`, which renders on every page. It is a YAML folded scalar (`>`), so
newlines collapse into spaces — **every CSS rule must stay on a single line**.
Page-specific rules stay inline in that page's `<style>` block
(`about.md`, `publications.md`, `music.md`).

Do not copy a rule into multiple pages. Do not add `_sass/`, `_includes/`,
`_layouts/`, or a local Tailwind build — those paths are gem-owned, and adding
them here silently takes over ownership of a file that upstream keeps updating.

## Build and deploy

There is **no local Ruby toolchain on this machine** (system Ruby is 2.6; the
`Gemfile.lock` wants bundler 4.0.6). Two ways to build:

```bash
docker compose up -d                    # bind-mounts repo, serves on :8080
curl -fsS http://127.0.0.1:8080/ >/dev/null
docker compose logs --tail=80
docker compose down
```

`docker compose` runs `bin/entry_point.sh`, which serves with
`--force_polling --destination /tmp/_site`. Build output deliberately goes to
**container-local `/tmp/_site`, not the bind-mounted `_site`** — writing `_site`
back across the host bind mount caused write deadlocks. The container also
`inotifywait`s `_config.yml` and restarts Jekyll on change (config edits aren't
hot-reloaded by `--watch`). `docker-compose-slim.yml` pulls a prebuilt image.

The **authoritative** build is `.github/workflows/deploy.yml`: Jekyll build →
purgecss → `scripts/translate_site.py` (gpt-4o, `continue-on-error`) →
force-push to `gh-pages`. It also runs on pull requests (without deploying), so
**opening a PR is the cheapest way to verify a real build.**

`update-content.yml` (Mondays 01:00 UTC) is the single content-refresh job: it
runs `scripts/update_publications.py` (OpenAlex → `_bibliography/papers.bib` +
preview images) and `scripts/update_music.py` (NetEase → `_data/music.yml`),
commits whatever moved as **one** commit, and chains **one** deploy. Both
fetches are `continue-on-error` and only a cleanly-fetched source is staged, so
one flaky upstream cannot block the other or commit a truncated file. Both
scripts are stdlib-only. These two files are tool-owned — never hand-edit them.

`prune-deployments.yml` trims deployment records daily. `render-cv.yml`
(`_data/cv.yml` → PDF) is manual-only.

**Do not add Google Scholar automation back.** It was tried and removed:
Scholar blocks datacenter IPs, so `scholarly` hangs on a CAPTCHA page until the
runner kills it (exit 124, reproduced at both 90s and 300s, each burning the
full budget), and `workflow_dispatch` runs on the same IP ranges. The workflow
had failed on every run since the repo was created. `_data/citations.yml`, the
fetch script, and the `google_scholar` badge are all gone; `inspirehep` is off
too, since it only indexes high-energy physics. Altmetric and Dimensions are
client-side and unaffected. Reinstating any of this needs either a paid scraping
proxy or a human running the fetch locally and committing the result.

## Formatting

Prettier is the only lint kept in this repo (`npm run lint:prettier` /
`npm run format`), using `@shopify/prettier-plugin-liquid` with
`printWidth: 150`. **No CI workflow runs it** — it is a local convenience.
