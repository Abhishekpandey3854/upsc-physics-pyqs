# UPSC Physics Optional PYQs Topic Wise

Static GitHub Pages site for UPSC Physics Optional previous year questions arranged topic-wise and subtopic-wise.

Target search phrases:

- UPSC Physics Optional PYQs
- UPSC Physics previous year questions
- UPSC topic wise physics PYQs
- UPSC optional physics questions
- UPSC Physics Optional topic wise

## Local Preview

```powershell
python scripts/build_github_pages_site.py
python -m http.server 8008 --directory docs
```

Open:

```text
http://127.0.0.1:8008/
```

## GitHub Pages Deployment

1. Push this repository to GitHub.
2. Go to repository **Settings** -> **Pages**.
3. Under **Build and deployment**, choose:
   - Source: `Deploy from a branch`
   - Branch: `main`
   - Folder: `/docs`
4. Save.

GitHub will publish the site at:

```text
https://<your-username>.github.io/<repository-name>/
```

## Regenerate Site

If the cleaned PYQ CSV changes, rebuild:

```powershell
python scripts/build_github_pages_site.py
```

The generated site lives in `docs/`.
