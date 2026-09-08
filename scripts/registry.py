#!/usr/bin/env python3
"""
AO3 Skins Registry Manager
Manages skins, frontmatter metadata, individual SVG pages, and registry catalog.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKINS_DIR = REPO_ROOT / "skins"
REGISTRY_JSON = REPO_ROOT / "registry.json"
BASE_URL = "https://hoopyfrood42.github.io"


def slugify(text: str) -> str:
    """Converts a string to a clean URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def parse_frontmatter(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """Extracts YAML frontmatter and markdown body from a file."""
    if not file_path.exists():
        return {}, ""

    content = file_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_raw = parts[1]
    body = parts[2].lstrip("\n")

    try:
        data = yaml.safe_load(frontmatter_raw) or {}
    except Exception as e:
        print(f"Warning: Failed to parse YAML frontmatter in {file_path}: {e}")
        data = {}

    return data, body


def write_frontmatter_file(file_path: Path, frontmatter: Dict[str, Any], body: str) -> None:
    """Writes YAML frontmatter and markdown body to a file."""
    yaml_str = yaml.dump(frontmatter, sort_keys=False, default_flow_style=False).strip()
    content = f"---\n{yaml_str}\n---\n\n{body.lstrip()}\n"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def get_all_skins() -> List[Dict[str, Any]]:
    """Scans skins/ directory and loads all skin metadata."""
    skins: List[Dict[str, Any]] = []

    if not SKINS_DIR.exists():
        return skins

    for item in sorted(SKINS_DIR.iterdir()):
        if not item.is_dir() or item.name.startswith("."):
            continue

        index_file = item / "index.md"
        if not index_file.exists():
            continue

        frontmatter, body = parse_frontmatter(index_file)
        skin_id = frontmatter.get("id", item.name)
        title = frontmatter.get("title", item.name.replace("-", " ").title())

        # Auto-detect all .svg files in the skin folder
        existing_svg_files = [f.name for f in item.glob("*.svg")]

        # Declared SVGs in frontmatter
        svgs_meta = frontmatter.get("svgs") or []
        declared_files = {s.get("file") for s in svgs_meta if isinstance(s, dict) and s.get("file")}

        # If there are SVG files on disk not declared yet in frontmatter, register them
        updated = False
        for svg_filename in sorted(existing_svg_files):
            if svg_filename not in declared_files:
                svg_stem = Path(svg_filename).stem
                svgs_meta.append({
                    "id": slugify(svg_stem),
                    "title": svg_stem.replace("-", " ").replace("_", " ").title(),
                    "file": svg_filename,
                    "description": f"{title} {svg_stem.replace('-', ' ')} asset",
                })
                updated = True

        if updated:
            frontmatter["svgs"] = svgs_meta
            write_frontmatter_file(index_file, frontmatter, body)

        skins.append({
            "dir": item,
            "id": skin_id,
            "title": title,
            "frontmatter": frontmatter,
            "body": body,
            "svg_files_on_disk": existing_svg_files,
        })

    return skins


def generate_svg_pages(skin: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generates an individual markdown page for each SVG in the skin."""
    skin_dir: Path = skin["dir"]
    skin_id: str = skin["id"]
    skin_title: str = skin["title"]
    svgs: List[Dict[str, Any]] = skin["frontmatter"].get("svgs") or []

    svg_pages_dir = skin_dir / "svgs"
    svg_pages_dir.mkdir(exist_ok=True)

    generated_svgs: List[Dict[str, Any]] = []

    for svg in svgs:
        if not isinstance(svg, dict):
            continue

        svg_id = svg.get("id") or slugify(Path(svg.get("file", "asset")).stem)
        svg_title = svg.get("title", svg_id.replace("-", " ").title())
        svg_file = svg.get("file", f"{svg_id}.svg")
        description = svg.get("description", f"SVG asset for {skin_title}.")

        raw_url = f"{BASE_URL}/skins/{skin_id}/{svg_file}"
        page_rel = f"svgs/{svg_id}.html"
        page_url = f"{BASE_URL}/skins/{skin_id}/{page_rel}"
        css_class = f"{skin_id}-{svg_id}"

        file_exists = (skin_dir / svg_file).exists()

        preview_block = (
            f"![{svg_title}](../{svg_file})"
            if file_exists
            else "> *SVG asset file not yet uploaded to repository. Place `"
            + svg_file
            + "` in `"
            + f"skins/{skin_id}/"
            + "`.*"
        )

        svg_page_content = f"""# {svg_title}

*Part of the [**{skin_title}**](../) AO3 skin collection.*

{description}

---

### Visual Preview
{preview_block}

---

### Direct SVG Asset URL
Use this URL directly in your browser or within AO3 work skins:
```text
{raw_url}
```

### AO3 CSS Usage Snippet
```css
#workskin .{css_class} {{
  display: block;
  background-image: url("{raw_url}");
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
}}
```

---

[← Back to {skin_title}](../) | [All Skins](/skins/)
"""
        svg_page_file = svg_pages_dir / f"{svg_id}.md"
        svg_page_fm = {
            "layout": "default",
            "title": f"{svg_title} ({skin_title})",
            "skin_id": skin_id,
            "skin_title": skin_title,
            "svg_id": svg_id,
            "svg_file": svg_file,
            "raw_url": raw_url,
        }
        write_frontmatter_file(svg_page_file, svg_page_fm, svg_page_content)

        generated_svgs.append({
            "id": svg_id,
            "title": svg_title,
            "file": svg_file,
            "description": description,
            "raw_url": raw_url,
            "page_rel_url": f"./svgs/{svg_id}",
            "page_url": page_url,
            "exists_on_disk": file_exists,
        })

    return generated_svgs


def generate_registry_index(skins_data: List[Dict[str, Any]]) -> None:
    """Auto-generates the master skins/index.md registry catalog."""
    index_file = SKINS_DIR / "index.md"

    rows: List[str] = []
    for s in skins_data:
        fm = s["frontmatter"]
        skin_id = s["id"]
        title = s["title"]
        desc = fm.get("description", "Custom AO3 skin.")
        cat = fm.get("category", "workskin").capitalize()
        tags = fm.get("tags") or []
        tags_str = ", ".join(f"`{t}`" for t in tags) if tags else "—"
        svg_count = len(s.get("svgs", []))

        svg_links = []
        for svg in s.get("svgs", []):
            svg_links.append(f"[{svg['title']}](./{skin_id}/svgs/{svg['id']})")
        svg_links_str = ", ".join(svg_links) if svg_links else "*No SVGs yet*"

        row = (
            f"### [{title}](./{skin_id}/)\n\n"
            f"- **Type:** {cat}\n"
            f"- **Description:** {desc}\n"
            f"- **Tags:** {tags_str}\n"
            f"- **SVG Pages ({svg_count}):** {svg_links_str}\n"
        )
        rows.append(row)

    catalog_body = "\n---\n\n".join(rows) if rows else "*No skins registered yet.*"

    content = f"""# AO3 Skins Registry

Welcome to the central registry of free skins and styles for Archive of Our Own (AO3).
Each skin includes ready-to-use CSS, HTML guides, and individual SVG asset pages.

---

{catalog_body}

---

[← Back to Home](/)
"""

    frontmatter = {
        "layout": "default",
        "title": "AO3 Skins Registry",
    }
    write_frontmatter_file(index_file, frontmatter, content)


def generate_registry_json(skins_data: List[Dict[str, Any]]) -> None:
    """Generates a machine-readable registry.json file."""
    data = {
        "registry_version": "1.0.0",
        "site_url": BASE_URL,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_skins": len(skins_data),
        "skins": [
            {
                "id": s["id"],
                "title": s["title"],
                "url": f"{BASE_URL}/skins/{s['id']}/",
                "category": s["frontmatter"].get("category", "workskin"),
                "version": s["frontmatter"].get("version", "1.0.0"),
                "description": s["frontmatter"].get("description", ""),
                "tags": s["frontmatter"].get("tags", []),
                "svgs": [
                    {
                        "id": svg["id"],
                        "title": svg["title"],
                        "file": svg["file"],
                        "description": svg["description"],
                        "page_url": svg["page_url"],
                        "raw_url": svg["raw_url"],
                        "exists_on_disk": svg["exists_on_disk"],
                    }
                    for svg in s.get("svgs", [])
                ],
            }
            for s in skins_data
        ],
    }

    REGISTRY_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")


def cmd_build() -> None:
    """Builds and synchronizes the entire registry."""
    print("Scanning skins...")
    skins = get_all_skins()

    for skin in skins:
        print(f"-> Processing skin: {skin['title']} ({skin['id']})")
        svgs_processed = generate_svg_pages(skin)
        skin["svgs"] = svgs_processed

    print("Generating master registry catalog (skins/index.md)...")
    generate_registry_index(skins)

    print("Generating machine-readable registry.json...")
    generate_registry_json(skins)

    print("Registry build complete!")


def cmd_new(name: str, category: str = "workskin") -> None:
    """Scaffolds a new skin in skins/."""
    skin_id = slugify(name)
    target_dir = SKINS_DIR / skin_id

    if target_dir.exists():
        print(f"Error: Skin directory already exists at {target_dir}")
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "svgs").mkdir(exist_ok=True)

    frontmatter = {
        "layout": "default",
        "id": skin_id,
        "title": name,
        "description": f"Custom {category} for AO3.",
        "category": category,
        "version": "1.0.0",
        "tags": [],
        "svgs": [],
    }

    body = f"""# {name}

Custom {category} for Archive of Our Own (AO3).

---

## SVG Assets
Add your `.svg` files to `skins/{skin_id}/` and run `uv run python scripts/registry.py build` to automatically register them and generate dedicated SVG pages.

---

## AO3 CSS Code

Copy and paste this CSS into your AO3 Work Skin:

```css
#workskin .{skin_id} {{
  /* Add your custom styles here */
}}
```

---

[← Back to Skins Registry](/skins/) | [Home](/)
"""

    write_frontmatter_file(target_dir / "index.md", frontmatter, body)
    print(f"Created new skin scaffold at skins/{skin_id}/index.md")

    # Rebuild registry
    cmd_build()


def cmd_validate() -> None:
    """Validates skin frontmatter and SVG file integrity."""
    skins = get_all_skins()
    errors = 0
    warnings = 0

    print(f"Validating {len(skins)} skin(s)...")
    for s in skins:
        skin_id = s["id"]
        svgs = s["frontmatter"].get("svgs") or []
        for svg in svgs:
            if not isinstance(svg, dict) or not svg.get("file"):
                print(f"[ERROR] Skin '{skin_id}': Invalid SVG entry in frontmatter: {svg}")
                errors += 1
                continue
            svg_path = s["dir"] / svg["file"]
            if not svg_path.exists():
                print(f"[WARN] Skin '{skin_id}': SVG file '{svg['file']}' does not exist on disk yet.")
                warnings += 1

    print(f"Validation finished: {errors} error(s), {warnings} warning(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="AO3 Skins Registry CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build
    subparsers.add_parser("build", help="Build/sync all SVG pages, registry catalog, and registry.json")

    # new
    new_parser = subparsers.add_parser("new", help="Scaffold a new skin")
    new_parser.add_argument("name", help="Name of the new skin (e.g. 'Cyberpunk Glow')")
    new_parser.add_argument("--category", choices=["workskin", "siteskin"], default="workskin", help="Skin type")

    # validate
    subparsers.add_parser("validate", help="Validate frontmatter and SVG assets")

    args = parser.parse_args()

    if args.command == "build":
        cmd_build()
    elif args.command == "new":
        cmd_new(args.name, args.category)
    elif args.command == "validate":
        cmd_validate()


if __name__ == "__main__":
    main()
