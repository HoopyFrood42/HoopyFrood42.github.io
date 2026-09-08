# AO3 Skins & Resources Registry

A repository and registry of free, custom work skins, site skins, and SVG assets for [Archive of Our Own (AO3)](https://archiveofourown.org/).

- **Live Site:** [https://hoopyfrood42.github.io/](https://hoopyfrood42.github.io/)
- **Skins Directory:** [https://hoopyfrood42.github.io/skins/](https://hoopyfrood42.github.io/skins/)
- **API Registry:** [registry.json](https://hoopyfrood42.github.io/registry.json)

---

## Overview

This site is built with GitHub Pages and Jekyll, managed as a data-driven registry where:
- **Frontmatter is the source of truth:** Each skin defines its title, tags, description, and SVG assets in YAML frontmatter.
- **Dedicated SVG Pages:** Every SVG asset gets its own web page with visual previews, copy-paste AO3 CSS snippets, and direct asset URLs.
- **Raw SVG Asset Hosting:** Raw `.svg` files are served directly over HTTPS so AO3 work skins can load them in `background-image: url(...)` rules.
- **Automated CLI:** A Python CLI managed with `uv` synchronizes frontmatter, auto-detects SVGs, generates SVG pages, and updates the catalog.

---

## Directory Structure

```text
HoopyFrood42.github.io/
├── skins/
│   ├── index.md                 # Auto-generated catalog of all skins
│   └── wild-west-vibes/         # Example skin directory
│       ├── index.md             # Skin page & frontmatter metadata
│       ├── svgs/                # Auto-generated dedicated SVG showcase pages
│       │   ├── divider.md
│       │   └── icon.md
│       ├── divider.svg          # Raw SVG asset (once uploaded)
│       └── icon.svg             # Raw SVG asset (once uploaded)
├── scripts/
│   └── registry.py              # Registry management CLI
├── registry.json                # Auto-generated machine-readable registry
├── pyproject.toml               # Python environment config (uv)
└── _config.yml                  # Jekyll theme and site config
```

---

## How Individual SVG Pages Work

Every SVG asset in the registry gets **two distinct endpoints**:

| Endpoint Type | Example URL | Purpose |
|---|---|---|
| **Raw Asset File** | `.../wild-west-vibes/divider.svg` | The raw graphic file served directly over HTTPS. This is the URL used in **AO3 CSS** rules (`background-image: url(...)`). |
| **Dedicated Showcase Page** | `.../wild-west-vibes/svgs/divider` | A user-facing webpage generated from `svgs/divider.md` for visitors browsing the registry. |

### What is on an SVG Showcase Page?

Each generated `.md` page (e.g. `skins/<skin>/svgs/<svg-id>.md`) includes:
1. **Visual Preview:** Displays the rendered graphic directly in the browser.
2. **Direct Asset URL:** A copyable HTTPS URL pointing to the raw `.svg` file.
3. **Pre-filled AO3 CSS Snippet:** Ready-to-paste CSS block configured with the direct URL and classes.
4. **Breadcrumb Links:** Quick navigation back to the skin's overview page and the master registry.

### Automatic Generation
You never need to manually author the files in `svgs/`. When you drop `.svg` files into a skin folder and run `uv run python scripts/registry.py build`, the script reads the skin's frontmatter and automatically creates or updates each SVG showcase page.

---

## Environment Setup (`uv`)

This project uses [`uv`](https://docs.astral.sh/uv/) to manage the Python environment and dependencies.

Install dependencies into the virtual environment:

```bash
uv sync
```

---

## Registry CLI Commands

The registry CLI is located at `scripts/registry.py` and run via `uv`:

### 1. Build and Sync the Registry
Scans all skin folders, auto-detects newly added `.svg` files, generates individual SVG pages, updates `skins/index.md`, and refreshes `registry.json`:

```bash
uv run python scripts/registry.py build
```

### 2. Scaffold a New Skin
Creates a new directory in `skins/<slug>/` with boilerplate frontmatter, placeholder CSS, and SVG folders:

```bash
uv run python scripts/registry.py new "Skin Name" --category workskin
```
*(Options for `--category`: `workskin` or `siteskin`)*

### 3. Validate Frontmatter and Assets
Verifies that all frontmatter is valid and checks whether declared SVG files exist on disk:

```bash
uv run python scripts/registry.py validate
```

---

## Frontmatter Schema

Each skin folder contains an `index.md` with YAML frontmatter defining its metadata:

```yaml
---
layout: default
id: wild-west-vibes
title: Wild West Vibes
description: Western-themed AO3 work skin featuring custom SVG assets and vintage typography.
category: workskin # workskin | siteskin
version: 1.0.0
tags:
  - western
  - vintage
  - decorative
svgs:
  - id: divider
    title: Chapter Divider
    file: divider.svg
    description: Thematic Western rope & cactus chapter divider
  - id: icon
    title: Corner Accent Icon
    file: icon.svg
    description: Western star badge accent
---
```

---

## Workflow: Adding or Updating a Skin

1. **Scaffold or Open a Skin:**
   - For a new skin:
     ```bash
     uv run python scripts/registry.py new "Neon Nights"
     ```
   - For an existing skin, navigate to `skins/<skin-id>/`.

2. **Add Your SVG Files:**
   Drop your `.svg` files directly into `skins/<skin-id>/` (e.g. `skins/wild-west-vibes/divider.svg`).

3. **Rebuild the Registry:**
   ```bash
   uv run python scripts/registry.py build
   ```
   *The script will auto-detect the SVG files, register them in frontmatter, and generate their individual showcase pages.*

4. **Add AO3 CSS & Instructions:**
   Edit `skins/<skin-id>/index.md` to add your CSS code and installation steps.

5. **Commit and Deploy:**
   ```bash
   git add .
   git commit -m "Update skin assets and rebuild registry"
   git push origin main
   ```
   GitHub Pages will automatically build and publish the updates.
