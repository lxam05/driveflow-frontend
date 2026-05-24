# DriveFlow content agent

Automated guide generation for driveflow.ie using Claude + your content plan.

## Files

| File | Purpose |
|------|---------|
| `site-knowledge.md` | Tone, HTML templates, internal links, guardrails (no em dashes; use practice/practicing) |
| `content-plan.csv` | What to write next (`status`: `planned` → `done`) |
| `generate_article.py` | Picks next **planned** row (by priority), calls API, saves HTML |
| `requirements.txt` | Python deps for local runs / CI |

## GitHub Actions (repo: `lxam05/driveflow-frontend`)

The live site repo is **`my-frontend-new`** (files at repo root on GitHub). The workflow must live here:

`my-frontend-new/.github/workflows/content-agent.yml`

It will **not** run if `.github` only exists in the parent `DrivingTestApp` folder.

### Setup

1. **Push from `my-frontend-new`** (where you run `git push` to driveflow-frontend)
2. **Secret:** GitHub → `driveflow-frontend` → Settings → Secrets → Actions → `ANTHROPIC_API_KEY`  
   (Same key as OpenClaw / `ANTHROPIC_API_KEY` in your shell)
3. **Model:** Workflow sets `ANTHROPIC_MODEL=claude-opus-4-7` (matches OpenClaw default)
4. **Manual test:** Actions → “Content Agent — Generate Article” → **Run workflow**

### What the bot generates

- Rows with `status` = `planned` and one of these **types**:
  `guide`, `article`, `fail-spots`, `pass-guide`, `roundabouts`, `checklist`, `comparison`, `city-guide`
- Picks **high** priority before **medium** before **low**
- Uses **`published_url`** from the CSV for the file path (e.g. `/guides/raheny-fail-spots.html` → `guides/raheny-fail-spots.html`)
- Updates `content-plan.csv` to `done` (keeps the same `published_url`)
- Adds SEO meta tags (robots, Open Graph, Twitter Card, Article JSON-LD) and appends the URL to `sitemap.xml`
- Appends the guide to **`guides-index.json`** so it appears on **`/guides.html`** (the hub linked from the homepage)

Centre **route-content** (`.txt` files on `*-routes.html` pages) is not in this plan — those stay manual.

### Local test (or OpenClaw)

```bash
cd my-frontend-new   # git root for driveflow-frontend
export ANTHROPIC_API_KEY="your-key"   # already set if OpenClaw works
export ANTHROPIC_MODEL="claude-opus-4-7"   # optional; this is the default
pip install -r _agent/requirements.txt
python _agent/generate_article.py
```

OpenClaw does **not** need GitHub Actions. It only needs read/write access to this repo and the same API key.

**Important:** The guides hub is driven by `guides-index.json`. If OpenClaw writes a guide HTML file by hand (without running `generate_article.py`), it must also add an entry to `guides-index.json` or the guide will not show on `/guides.html`.

## Next planned topic

First run picks the highest-priority `planned` row — currently: **Top 10 fail spots in Raheny driving test** (`fail-spots`, `/guides/raheny-fail-spots.html`).
