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

| Workflow                  | Trigger                | Does                                             |
| ------------------------- | ---------------------- | ------------------------------------------------ |
| `deploy.yml`              | push to `main`         | Jekyll build → purgecss → translate → `gh-pages` |
| `render-cv.yml`           | `_data/cv.yml` changes | RenderCV → `assets/rendercv/rendercv_output/`    |
| `update-citations.yml`    | Mon/Wed/Fri            | Google Scholar counts → `_data/citations.yml`    |
| `update-publications.yml` | schedule               | refresh `_bibliography/papers.bib`               |
| `update-music.yml`        | schedule               | refresh `_data/music.yml` from NetEase           |

## License

[MIT](LICENSE) — theme by [al-folio](https://github.com/alshedivat/al-folio); site content © Guohao Zhang.
