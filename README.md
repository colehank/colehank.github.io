# colehank.github.io

Personal academic homepage of **Guohao Zhang** — PhD student in Psychology at Beijing Normal University, working on NeuroAI, human vision, LLM agent memory, and decentralized science.

🔗 <https://colehank.github.io>

Built on [al-folio](https://github.com/alshedivat/al-folio) v1.x (Jekyll + the `al_folio_*` plugin gems).

## Editing content

| What               | Where                                                                        |
| ------------------ | ---------------------------------------------------------------------------- |
| Bio / landing page | `_pages/about.md`                                                            |
| Publications       | `_bibliography/papers.bib` (+ previews in `assets/img/publication_preview/`) |
| News items         | `_news/`                                                                     |
| Projects           | your **pinned repos on GitHub** — auto-generated, see below                  |
| CV                 | `_data/cv.yml` (RenderCV) → PDF rebuilt by the CV workflow                   |
| Music page         | `_data/music.yml` (auto-generated — don't hand-edit)                         |
| Site config        | `_config.yml`                                                                |

Blog posts go in `_posts/`, which is still empty, so `/blog/` is hidden from the
navbar (`nav: false`) until there is something to show.

### Projects

`/projects/` is **generated, not hand-written**. `scripts/update_projects.py`
reads the repositories pinned on the GitHub profile and rewrites `_projects/`,
one card per repo, in pin order. It runs weekly as part of `update-content.yml`.

**To change what appears, change your pins on GitHub** — the site follows on the
next run (or trigger `update-content.yml` manually). Card text comes from the
repo's GitHub **description**; if that is empty, the script falls back to the
first real line of the README. So the best way to fix a card's wording is to set
the repo description on GitHub.

Every generated file carries `generated: true`. The script deletes only those, so
a hand-written card dropped into `_projects/` without that marker survives and
appears alongside the pinned ones.

Pinned repos are only exposed through GitHub's GraphQL API, which always needs a
token. To run it locally:

```bash
GITHUB_TOKEN=$(gh auth token) python3 scripts/update_projects.py
```

Notes on the card template: `collections.projects.output` is `false`, so no
per-project pages are generated — with `redirect:` set they would be empty
orphans in the sitemap. The page renders one flat list, because GitHub exposes
nothing to derive a category from. And do **not** use `github_stars:` — no
shipped JS fills it in, so it renders a star icon with no number.

Site-wide CSS overrides live in one place: the `footer_text` block in
`_config.yml`, which renders on every page. Page-specific rules stay in the
page itself.

## Local preview

The system Ruby on macOS is too old, so use the Homebrew Ruby that matches CI.
One-time setup:

```bash
brew install ruby@3.3
export PATH="/opt/homebrew/opt/ruby@3.3/bin:/opt/homebrew/lib/ruby/gems/3.3.0/bin:$PATH"
gem install bundler -v 4.0.6          # the version Gemfile.lock pins
bundle config set --local path vendor/bundle
bundle install
```

Then, with that `PATH` exported:

```bash
bundle exec jekyll serve                          # http://127.0.0.1:4000/
JEKYLL_ENV=production bundle exec jekyll build    # one-shot, into _site/
```

A build takes a couple of seconds. Run one before pushing changes to
`_config.yml`, the `Gemfile`, or any layout — plugin and Liquid errors break the
build outright and nothing else catches them.

A Docker setup (`docker compose up -d`, port 8080) is also committed if you
prefer it, but Docker is not currently installed on this machine.

Formatting (the only lint kept in this repo):

```bash
npm ci
npm run lint:prettier       # check
npm run format              # fix
```

## Automation

| Workflow                | Trigger         | Does                                                                             |
| ----------------------- | --------------- | -------------------------------------------------------------------------------- |
| `update-content.yml`    | Mon 01:00 UTC   | OpenAlex → `papers.bib`, NetEase → `_data/music.yml`, GitHub pins → `_projects/` |
| `deploy.yml`            | push to `main`  | Jekyll build → purgecss → translate → `gh-pages`                                 |
| `render-cv.yml`         | **manual only** | `_data/cv.yml` → CV PDF                                                          |
| `prune-deployments.yml` | daily 03:30 UTC | trims old deployment records                                                     |

`update-content.yml` handles all three external sources in one run: it commits
whatever moved as a single commit and triggers exactly one redeploy. The fetches
are independent — each is `continue-on-error`, and only a source that fetched
cleanly gets staged, so a flaky upstream can neither block the others nor
overwrite good data with a truncated file.

`_bibliography/papers.bib`, `_data/music.yml` and the generated files in
`_projects/` are workflow-owned — never hand-edit them, the next run overwrites
whatever is there.

`render-cv.yml` is deliberately manual: the PDF is normally rendered locally and
committed together with the CV edit, which avoids a second commit-and-redeploy
cycle. Run it from the Actions tab if you edit `_data/cv.yml` on GitHub directly.

### Why there is no Google Scholar automation

Google Scholar blocks datacenter IPs, so `scholarly` running on a GitHub runner
hangs on a CAPTCHA page until the job times out — reproduced at both 90s and
300s, each consuming the full budget. The workflow that tried to do this failed
on every run since the repo was created and has been removed, along with
`_data/citations.yml` and the `google_scholar` publication badge.

The Altmetric and Dimensions badges are client-side and still work, so
publications keep their citation metrics. If you ever want Scholar counts back,
the only reliable route is running the fetch from your own machine, where the IP
is not blocked, and committing `_data/citations.yml` by hand — then flip
`enable_publication_badges.google_scholar` back to `true`.

## License

[MIT](LICENSE) — theme by [al-folio](https://github.com/alshedivat/al-folio); site content © Guohao Zhang.
