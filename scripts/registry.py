#!/usr/bin/env python3
"""
AO3 Skins Registry Manager
Manages skins, frontmatter metadata, individual SVG pages, and registry catalog.
"""

from __future__ import annotations

import argparse
import datetime
import http.server
import json
import os
import re
import shutil
import socketserver
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Tuple

import markdown
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


def render_liquid_simple(template: str, context: Dict[str, Any], content: str) -> str:
    """Lightweight Liquid template renderer for local HTML previewing."""
    html = template
    page_title = context.get("title", "")
    page_url = context.get("url", "/")
    site_title = context.get("site_title", "Fjord's resources")
    site_desc = context.get("site_description", "")
    page_desc = context.get("description", site_desc)

    title_tag_content = f"{page_title} | {site_title}" if page_title else site_title
    html = re.sub(
        r"\{%\s*if\s+page\.title\s*%\}.*?\{%\s*endif\s*%\}",
        title_tag_content,
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"\{%\s*if\s+page\.description\s*%\}.*?\{%\s*endif\s*%\}",
        page_desc,
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r"\{%\s*if\s+site\.description\s*%\}(.*?)\{%\s*endif\s*%\}",
        rf"\1" if site_desc else "",
        html,
        flags=re.DOTALL,
    )

    # Evaluate page.url active nav conditions
    def eval_url_condition(match: re.Match) -> str:
        condition = match.group(1).strip()
        body = match.group(2)
        if "page.url == '/'" in condition or "page.url == '/index.html'" in condition:
            if page_url in ("/", "/index.html", ""):
                return body
        if "contains '/skins'" in condition:
            if "/skins" in page_url:
                return body
        if "contains '/resources'" in condition:
            if "/resources" in page_url:
                return body
        return ""

    html = re.sub(
        r"\{%\s*if\s+(page\.url\s+[^%]+)\s*%\}(.*?)\{%\s*endif\s*%\}",
        eval_url_condition,
        html,
        flags=re.DOTALL,
    )

    html = html.replace("{{ site.title }}", site_title)
    html = html.replace("{{ site.description }}", site_desc)
    html = html.replace("{{ page.title }}", page_title)
    html = html.replace("{{ page.description }}", page_desc)
    html = html.replace("{{ 'now' | date: \"%Y\" }}", str(datetime.datetime.now().year))

    relative_root = context.get("relative_root", ".")

    def rel_url_sub(match: re.Match) -> str:
        raw_path = match.group(1).strip("'\"")
        if raw_path.startswith("/"):
            if raw_path == "/":
                return f"{relative_root}/index.html" if relative_root != "." else "./index.html"
            sub = raw_path.lstrip("/")
            if sub.endswith("/"):
                sub += "index.html"
            elif not sub.endswith(".html") and not sub.endswith(".css") and not sub.endswith(".json") and not sub.endswith(".svg"):
                sub += ".html"
            return f"{relative_root}/{sub}"
        return raw_path

    html = re.sub(r"\{\{\s*(['\"][^'\"]+['\"])\s*\|\s*relative_url\s*\}\}", rel_url_sub, html)
    html = html.replace("{{ content }}", content)
    return html


def build_site_html() -> Path:
    """Compiles markdown pages into static HTML in _site/ directory for local previewing."""
    cmd_build()

    site_dir = REPO_ROOT / "_site"
    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir(parents=True, exist_ok=True)

    # Load site metadata
    config_file = REPO_ROOT / "_config.yml"
    config_data = {}
    if config_file.exists():
        config_data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}

    site_title = config_data.get("title", "Fjord's resources")
    site_desc = config_data.get("description", "")

    # Load layout
    layout_file = REPO_ROOT / "_layouts" / "default.html"
    layout_tmpl = layout_file.read_text(encoding="utf-8") if layout_file.exists() else "{{ content }}"

    # Copy assets
    assets_src = REPO_ROOT / "assets"
    if assets_src.exists():
        shutil.copytree(assets_src, site_dir / "assets")

    # Copy registry.json
    if REGISTRY_JSON.exists():
        shutil.copy2(REGISTRY_JSON, site_dir / "registry.json")

    # Copy all SVGs
    for svg_path in SKINS_DIR.rglob("*.svg"):
        rel = svg_path.relative_to(REPO_ROOT)
        target = site_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(svg_path, target)

    # Find and compile markdown files
    md_files = [
        REPO_ROOT / "index.md",
        REPO_ROOT / "resources.md",
        *SKINS_DIR.rglob("*.md"),
    ]

    for md_file in md_files:
        if not md_file.exists():
            continue

        frontmatter, body = parse_frontmatter(md_file)
        html_body = markdown.markdown(body, extensions=["fenced_code", "tables"])

        rel = md_file.relative_to(REPO_ROOT)
        if rel.name == "index.md":
            page_url = "/" if rel.parent == Path(".") else f"/{rel.parent}/"
            out_file = site_dir / rel.parent / "index.html"
            alt_out_file = None
        else:
            stem = rel.stem
            parent = rel.parent
            page_url = f"/{parent}/{stem}" if parent != Path(".") else f"/{stem}"
            out_file = site_dir / parent / f"{stem}.html"
            alt_out_file = site_dir / parent / stem / "index.html"

        # Calculate relative depth to site_dir for offline file:// protocol viewing
        depth = len(out_file.relative_to(site_dir).parent.parts)
        relative_root = "." if depth == 0 else "/".join([".."] * depth)

        ctx = {
            "title": frontmatter.get("title", ""),
            "description": frontmatter.get("description", ""),
            "site_title": site_title,
            "site_description": site_desc,
            "url": page_url,
            "relative_root": relative_root,
        }
        full_html = render_liquid_simple(layout_tmpl, ctx, html_body)

        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(full_html, encoding="utf-8")

        if alt_out_file:
            alt_depth = len(alt_out_file.relative_to(site_dir).parent.parts)
            alt_relative_root = "." if alt_depth == 0 else "/".join([".."] * alt_depth)
            ctx["relative_root"] = alt_relative_root
            alt_html = render_liquid_simple(layout_tmpl, ctx, html_body)
            alt_out_file.parent.mkdir(parents=True, exist_ok=True)
            alt_out_file.write_text(alt_html, encoding="utf-8")

    print(f"HTML compilation complete in: {site_dir}")
    return site_dir


def cmd_preview(port: int = 8000, serve: bool = True, open_browser: bool = True) -> None:
    """Builds HTML and starts a local web server to preview the site."""
    site_dir = build_site_html()

    if not serve:
        print(f"Preview built at: {site_dir / 'index.html'}")
        return

    os.chdir(site_dir)

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            # Suppress noisy GET log spam
            pass

    with socketserver.TCPServer(("", port), CustomHandler) as httpd:
        url = f"http://127.0.0.1:{port}"
        print(f"\n=======================================================")
        print(f"  Live Preview Running at: {url}")
        print(f"  Press Ctrl+C to stop the server.")
        print(f"=======================================================\n")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nPreview server stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="AO3 Skins Registry CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build
    subparsers.add_parser("build", help="Build/sync all SVG pages, registry catalog, and registry.json")

    # build-html
    subparsers.add_parser("build-html", help="Compile markdown into static HTML in _site/ without serving")

    # preview
    preview_parser = subparsers.add_parser("preview", help="Compile HTML and launch local preview server")
    preview_parser.add_argument("--port", type=int, default=8000, help="Port to run preview server on (default: 8000)")
    preview_parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")

    # new
    new_parser = subparsers.add_parser("new", help="Scaffold a new skin")
    new_parser.add_argument("name", help="Name of the new skin (e.g. 'Cyberpunk Glow')")
    new_parser.add_argument("--category", choices=["workskin", "siteskin"], default="workskin", help="Skin type")

    # validate
    subparsers.add_parser("validate", help="Validate frontmatter and SVG assets")

    args = parser.parse_args()

    if args.command == "build":
        cmd_build()
    elif args.command == "build-html":
        build_site_html()
    elif args.command == "preview":
        cmd_preview(port=args.port, serve=True, open_browser=not args.no_browser)
    elif args.command == "new":
        cmd_new(args.name, args.category)
    elif args.command == "validate":
        cmd_validate()


if __name__ == "__main__":
    main()
