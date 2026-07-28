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
| CV                 | `_data/cv.yml` (RenderCV) → PDF rebuilt by the CV workflow                   |
| Music page         | `_data/music.yml` (auto-generated — don't hand-edit)                         |
| Site config        | `_config.yml`                                                                |

Blog posts go in `_posts/`, projects in `_projects/`. Both are currently empty;
their pages (`/blog/`, `/projects/`) exist and are hidden from the navbar
(`nav: false`) until there is something to show.

Site-wide CSS overrides live in one place: the `footer_text` block in
`_config.yml`, which renders on every page. Page-specific rules stay in the
page itself.

## Local preview

No Ruby toolchain is needed — use Docker:

```bash
docker compose up -d
open http://127.0.0.1:8080/
docker compose logs -f      # watch the rebuild
docker compose down
```

Formatting (the only lint kept in this repo):

```bash
npm ci
npm run lint:prettier       # check
npm run format              # fix
```

## Automation

Two jobs pull content in from outside and commit the result; each triggers a
redeploy only when something actually changed.

| Workflow                  | Trigger                 | Fetches from | Writes                                           |
| ------------------------- | ----------------------- | ------------ | ------------------------------------------------ |
| `update-publications.yml` | Mon 01:00 UTC           | OpenAlex     | `_bibliography/papers.bib` + preview images      |
| `update-music.yml`        | 1st of month, 02:00 UTC | NetEase      | `_data/music.yml`                                |
| `deploy.yml`              | push to `main`          | —            | Jekyll build → purgecss → translate → `gh-pages` |
| `render-cv.yml`           | **manual only**         | —            | `_data/cv.yml` → CV PDF                          |
| `update-citations.yml`    | **manual only**         | —            | see below                                        |
| `prune-deployments.yml`   | daily 03:30 UTC         | —            | trims old deployment records                     |

`render-cv.yml` is deliberately manual: the PDF is normally rendered locally and
committed together with the CV edit, which avoids a second commit-and-redeploy
cycle. Run it from the Actions tab if you edit `_data/cv.yml` on GitHub directly.

`_data/music.yml` is workflow-owned — never hand-edit it, the next run
overwrites whatever is there.

### Google Scholar citation counts

`update-citations.yml` is unscheduled because Google Scholar blocks datacenter
IPs: on a GitHub runner `scholarly` hangs on a CAPTCHA page until the timeout
kills it. Refresh the counts from your own machine instead:

```bash
python3 -m pip install --user --break-system-packages scholarly pyyaml
python3 bin/update_scholar_citations.py
git add _data/citations.yml && git commit -m "Update Google Scholar citations" && git push
```

If `_data/citations.yml` is absent the Scholar count just does not render; the
Altmetric and Dimensions badges are client-side and unaffected.

## License

[MIT](LICENSE) — theme by [al-folio](https://github.com/alshedivat/al-folio); site content © Guohao Zhang.
