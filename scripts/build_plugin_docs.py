#!/usr/bin/env python
"""Generate reference markdown pages from MolModa plugin manifests.

Reads every `docs/img/auto/<plugin_id>/manifest.json` and emits:

  - One page per plugin under `docs/plugins/reference/` (alphabetical flat
    list, the canonical location for plugin pages).
  - A parallel directory tree under `docs/plugins/by-menu/` that mirrors
    the MolModa menu hierarchy. Each leaf `.pages` file references the
    canonical pages in `reference/` via relative paths, so there is no
    content duplication.
  - A grouped index at `docs/plugins/index.md`.
  - `.pages` files at every level so `mkdocs-awesome-pages-plugin` orders
    everything per the menu's `[N]` sort hints.

Output is gitignored; regenerate via `make plugin-docs` (run automatically
by `make serve` and `make docs`).

Hand-written supplemental prose can live at
`docs/plugins/_overrides/<plugin_id>.md` and is appended verbatim to the
matching reference page.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFESTS_DIR = REPO_ROOT / "docs" / "img" / "auto"
PLUGINS_DIR = REPO_ROOT / "docs" / "plugins"
REFERENCE_DIR = PLUGINS_DIR / "reference"
BY_MENU_DIR = PLUGINS_DIR / "by-menu"
OVERRIDES_DIR = PLUGINS_DIR / "_overrides"

# Plugins whose manifest data is malformed or that should not appear in the
# reference. Empty by default; populate if a problematic manifest appears.
SKIP_PLUGINS: set[str] = set()

# Path from a reference page (docs/plugins/reference/X.md) to the image dir.
# IMG_REL_PREFIX = "../../img/auto"

# Sort key applied to menu entries with no `[N]` prefix. High so they sink.
DEFAULT_SORT_KEY = 9999

MENU_PREFIX_RE = re.compile(r"^\[(\d+)\]\s*")

# Trailing punctuation we strip from menu labels for display and slugging.
TRAILING_PUNCT = "._… "

SLUG_RE = re.compile(r"[^a-z0-9]+")
# Directory under docs/ that holds plugin screenshots. Used to compute the
# relative image-path prefix that goes into each generated markdown file,
# based on where that file ends up on disk.
DOCS_DIR = REPO_ROOT / "docs"
IMAGES_SUBPATH = "img/auto"

class UserArg(TypedDict, total=False):
    """Subset of fields read from each user_args entry."""

    id: str
    label: str
    description: str
    type: str
    val: Any
    options: list[dict[str, Any]]
    alertType: str
    placeHolder: str
    enabled: bool


@dataclass
class MenuSegment:
    """One node in the parsed menu path.

    `sort_key` is the integer extracted from a `[N]` prefix (used to order
    siblings); `label` is the human-facing text with the prefix stripped.
    """

    sort_key: int
    label: str
    slug: str


@dataclass
class PluginRecord:
    """One plugin's parsed manifest, with derived display fields."""

    plugin_id: str
    title: str
    intro: str
    details: str
    menu_segments: list[MenuSegment]
    menu_path_display: str
    menu_group: str
    hotkey: str | None
    widget_image: str | None
    menu_image: str | None
    user_args: list[UserArg]
    captured_at: str
    # Sort key for the plugin's own position among its menu siblings.
    leaf_sort_key: int = DEFAULT_SORT_KEY
    leaf_label: str = ""


@dataclass
class MenuNode:
    """One node in the by-menu tree.

    Either an internal node (has `children`, no `plugins`) or a leaf
    grouping (may have both children and plugins; the script handles
    mixed cases by listing plugins after children in the nav).
    """

    sort_key: int
    label: str
    slug: str
    children: dict[str, "MenuNode"] = field(default_factory=dict)
    plugins: list[PluginRecord] = field(default_factory=list)


def parse_menu_segment(raw: str) -> MenuSegment:
    """Parse one menu segment, extracting sort key and human label."""
    decoded = html.unescape(raw).strip()
    match = MENU_PREFIX_RE.match(decoded)
    if match:
        sort_key = int(match.group(1))
        label = decoded[match.end():].strip()
    else:
        sort_key = DEFAULT_SORT_KEY
        label = decoded
    label = label.rstrip(TRAILING_PUNCT).strip()
    return MenuSegment(sort_key=sort_key, label=label, slug=slugify(label))


def slugify(text: str) -> str:
    """Produce a filesystem-safe slug from a menu label."""
    lower = text.lower()
    slug = SLUG_RE.sub("-", lower).strip("-")
    return slug or "untitled"


def parse_menu_path(raw: str) -> list[MenuSegment]:
    """Split a menu_path into segments. Last segment is the plugin itself.

    Segments that resolve to an empty label after stripping the `[N]`
    sort prefix are silently dropped: the MolModa menu data uses entries
    like `MolModa/[9]/[9] Quit` where the middle `[9]` is a pure sort
    hint with no label and should not produce its own submenu level.
    """
    if not raw:
        return []
    segments: list[MenuSegment] = []
    for raw_seg in raw.split("/"):
        if not raw_seg.strip():
            continue
        seg = parse_menu_segment(raw_seg)
        if not seg.label:
            # Bare `[N]` sort hint with no label; not a real menu level.
            continue
        segments.append(seg)
    return segments

def display_menu_path(segments: list[MenuSegment]) -> str:
    """Render a parsed path as `A → B → C` for display."""
    return " → ".join(s.label for s in segments if s.label)


def format_hotkey(hotkey: Any) -> str | None:
    """Render a hotkey value as one or more `<kbd>` spans, or None."""
    if hotkey is None:
        return None
    if isinstance(hotkey, list):
        keys = [str(k) for k in hotkey if k]
    else:
        keys = [str(hotkey)]
    return " / ".join(f"<kbd>{html.escape(k)}</kbd>" for k in keys) or None


def is_displayable_default(val: Any) -> bool:
    """Filter out defaults that would be noise (IDs, sentinels, empties).

    Internal molecule IDs, MoleculeInput placeholders, empty strings, and
    None all add nothing for a reader and are skipped.
    """
    if val is None:
        return False
    if isinstance(val, str):
        if val == "":
            return False
        if val.startswith("id_"):
            return False
        return True
    if isinstance(val, dict):
        # Things like {"__class__": "MoleculeInput"} are internal sentinels.
        if "__class__" in val:
            return False
        return bool(val)
    if isinstance(val, (list, tuple)):
        return len(val) > 0
    if isinstance(val, bool):
        return True
    if isinstance(val, (int, float)):
        return True
    return True


def format_default(val: Any) -> str:
    """Format an arg default for the parameters table."""
    if isinstance(val, bool):
        return "Yes" if val else "No"
    if isinstance(val, (int, float)):
        return f"`{val}`"
    if isinstance(val, str):
        return f"`{val}`"
    if isinstance(val, (list, tuple)):
        if all(isinstance(x, (str, int, float, bool)) for x in val):
            return ", ".join(f"`{x}`" for x in val)
        return "—"
    return "—"


def md_escape_cell(text: str) -> str:
    """Escape pipe characters and collapse newlines for a Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def arg_label(arg: UserArg) -> str:
    """Best human label for an arg: label, then placeholder, then id."""
    label = (arg.get("label") or "").strip()
    if label:
        return label
    placeholder = (arg.get("placeHolder") or "").strip()
    if placeholder:
        return placeholder.rstrip(".") + "…"
    return f"`{arg.get('id', '')}`"


def render_alert(arg: UserArg) -> str:
    """Render an alert-type arg as an MkDocs admonition."""
    alert_type = (arg.get("alertType") or "info").lower()
    kind_map = {"info": "info", "warning": "warning", "danger": "danger"}
    kind = kind_map.get(alert_type, "note")
    val = arg.get("val")
    text = val if isinstance(val, str) else ""
    text = text.strip()
    if not text:
        return ""
    indented = "\n".join(f"    {line}" for line in text.splitlines())
    return f'!!! {kind} ""\n{indented}\n'


def render_param_rows(args: list[UserArg]) -> list[str]:
    """Render flat (non-group, non-alert) args as table rows."""
    rows: list[str] = []
    for arg in args:
        atype = arg.get("type", "")
        if atype == "UserArgType.Alert":
            continue
        if atype == "UserArgType.Group":
            continue
        label = md_escape_cell(arg_label(arg))
        default = md_escape_cell(
            format_default(arg.get("val")) if is_displayable_default(arg.get("val")) else "—"
        )
        description = md_escape_cell((arg.get("description") or "").strip() or "—")
        rows.append(f"| {label} | {default} | {description} |")
    return rows


def render_parameters_section(args: list[UserArg]) -> str:
    """Render the full Parameters section, including alerts and groups."""
    if not args:
        return ""

    out: list[str] = ["## Parameters", ""]

    # Top-level alerts surface before the main table.
    for arg in args:
        if arg.get("type") == "UserArgType.Alert":
            block = render_alert(arg)
            if block:
                out.append(block)

    main_rows = render_param_rows(args)
    if main_rows:
        out.append("| Parameter | Default | Description |")
        out.append("| --- | --- | --- |")
        out.extend(main_rows)
        out.append("")

    # Groups are rendered as their own sub-section, with nested rows.
    for arg in args:
        if arg.get("type") != "UserArgType.Group":
            continue
        group_label = arg_label(arg) or "Advanced parameters"
        out.append(f"### {group_label}")
        out.append("")
        nested = arg.get("val")
        nested_args: list[UserArg] = nested if isinstance(nested, list) else []
        for sub in nested_args:
            if sub.get("type") == "UserArgType.Alert":
                block = render_alert(sub)
                if block:
                    out.append(block)
        nested_rows = render_param_rows(nested_args)
        if nested_rows:
            out.append("| Parameter | Default | Description |")
            out.append("| --- | --- | --- |")
            out.extend(nested_rows)
            out.append("")

    return "\n".join(out)


def load_manifest(path: Path) -> PluginRecord | None:
    """Parse one manifest.json into a PluginRecord. Returns None if invalid."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        print(f"warning: could not read {path}: {err}", file=sys.stderr)
        return None

    info = data.get("plugin_info") or {}
    plugin_id = data.get("plugin_id") or info.get("plugin_id")
    if not plugin_id or plugin_id in SKIP_PLUGINS:
        return None

    raw_menu_path = info.get("menu_path") or ""
    segments = parse_menu_path(raw_menu_path)

    # Last segment is the plugin's own entry under its parent menu; remember
    # its sort key so siblings are ordered correctly.
    leaf_sort_key = segments[-1].sort_key if segments else DEFAULT_SORT_KEY
    leaf_label = segments[-1].label if segments else (info.get("title") or plugin_id)

    return PluginRecord(
        plugin_id=plugin_id,
        title=(info.get("title") or plugin_id).strip(),
        intro=(info.get("intro") or "").strip(),
        details=(info.get("details") or "").strip(),
        menu_segments=segments,
        menu_path_display=display_menu_path(segments),
        menu_group=segments[0].label if segments else "Other",
        hotkey=format_hotkey(info.get("hotkey")),
        widget_image=data.get("image"),
        menu_image=data.get("menu_image"),
        user_args=list(info.get("user_args") or []),
        captured_at=(data.get("captured_at") or "")[:10],
        leaf_sort_key=leaf_sort_key,
        leaf_label=leaf_label,
    )

def image_prefix_for(page_dir: Path) -> str:
    """Compute the relative path from `page_dir` to `docs/img/auto/`.

    Used so each generated copy of a plugin page renders correct image
    paths for its own location on disk, regardless of nesting depth.
    """
    target = DOCS_DIR / IMAGES_SUBPATH
    return str(_relative(page_dir, target).as_posix())

def render_plugin_page(rec: PluginRecord, page_dir: Path) -> str:
    """Render the full reference page for one plugin.

    `page_dir` is the directory where this copy of the page will be
    written; image links are computed relative to it.
    """
    img_prefix = image_prefix_for(page_dir)
    out: list[str] = [f"# {rec.title}", ""]
    if rec.intro:
        out.append(rec.intro)
        out.append("")
    if rec.menu_path_display:
        out.append(f"**Menu:** {rec.menu_path_display}")
        out.append("")
    if rec.hotkey:
        out.append(f"**Hotkey:** {rec.hotkey}")
        out.append("")
    if rec.details and rec.details != rec.intro:
        out.append(rec.details)
        out.append("")
    if rec.menu_image:
        out.append("## Where to find it")
        out.append("")
        out.append(f"![Menu location for {rec.title}]({img_prefix}/{rec.plugin_id}/{rec.menu_image})")
        out.append("")
    if rec.widget_image:
        out.append("## Dialog")
        out.append("")
        out.append(f"![Dialog for {rec.title}]({img_prefix}/{rec.plugin_id}/{rec.widget_image})")
        out.append("")
    params = render_parameters_section(rec.user_args)
    if params:
        out.append(params)
    override_path = OVERRIDES_DIR / f"{rec.plugin_id}.md"
    if override_path.is_file():
        out.append("## Notes")
        out.append("")
        out.append(override_path.read_text(encoding="utf-8").strip())
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_index(root: MenuNode) -> str:
    """Render the plugins landing page.

    Walks the same menu tree used to build the by-menu nav so categories,
    subcategories, and plugin ordering all match. Top-level menus become
    `## headings`, nested submenus become `### headings`, etc.
    """
    out: list[str] = [
        "# Plugins",
        "",
        (
            "This section is an auto-generated reference for every MolModa "
            "plugin, organized by where each lives in the menu. For "
            "step-by-step walkthroughs, see the tutorials under "
            "[Docking](../docking/index.md) and other sections."
        ),
        "",
    ]
    top_children = sorted(
        root.children.values(), key=lambda n: (n.sort_key, n.label.lower())
    )
    for child in top_children:
        _render_index_node(child, depth=2, out=out)
    return "\n".join(out).rstrip() + "\n"


def _render_index_node(node: MenuNode, depth: int, out: list[str]) -> None:
    """Append one menu node's heading, plugins, and children to the index.

    Plugins at this level are listed before deeper subcategories so each
    section reads top-down: "here's what this menu does, and here are its
    submenus". Mirrors how the menu itself is structured.
    """
    heading = "#" * min(depth, 6)
    out.append(f"{heading} {node.label}")
    out.append("")
    # Plugins at this level, in their menu order.
    plugins_sorted = sorted(
        node.plugins, key=lambda r: (r.leaf_sort_key, (r.leaf_label or r.title).lower())
    )
    for rec in plugins_sorted:
        summary = (rec.intro or rec.details or "").strip()
        link = f"[{rec.title}](reference/{rec.plugin_id}.md)"
        if summary:
            out.append(f"- {link} — {summary}")
        else:
            out.append(f"- {link}")
    if plugins_sorted:
        out.append("")
    # Then subcategories, in their menu order.
    children_sorted = sorted(
        node.children.values(), key=lambda n: (n.sort_key, n.label.lower())
    )
    for child in children_sorted:
        _render_index_node(child, depth=depth + 1, out=out)

def render_plugins_root_pages() -> str:
    """`.pages` for docs/plugins/. Order: landing, by-menu tree, alpha list."""
    return (
        "nav:\n"
        "  - index.md\n"
        "  - By menu: by-menu\n"
        "  - Reference: reference\n"
    )


def render_reference_pages_file(records: list[PluginRecord]) -> str:
    """`.pages` for docs/plugins/reference/.

    Alphabetical by plugin title; uses titles as nav labels so the sidebar
    reads naturally instead of showing raw plugin IDs.
    """
    lines = ["nav:"]
    for rec in sorted(records, key=lambda r: r.title.lower()):
        lines.append(f"  - {rec.title}: {rec.plugin_id}.md")
    return "\n".join(lines) + "\n"


def build_menu_tree(records: list[PluginRecord]) -> MenuNode:
    """Build a nested MenuNode tree from all plugins' menu paths.

    The final segment of each plugin's path is the plugin entry itself,
    so it's attached to its parent node's `plugins` list. All earlier
    segments become intermediate `children`.
    """
    root = MenuNode(sort_key=-1, label="", slug="")
    for rec in records:
        if not rec.menu_segments:
            continue
        # Walk all but the last segment, creating nodes as needed.
        node = root
        for seg in rec.menu_segments[:-1]:
            child = node.children.get(seg.slug)
            if child is None:
                child = MenuNode(sort_key=seg.sort_key, label=seg.label, slug=seg.slug)
                node.children[seg.slug] = child
            else:
                # Keep the lowest sort_key seen for this slug — same slug
                # appearing with different prefixes in different paths
                # should still order predictably.
                if seg.sort_key < child.sort_key:
                    child.sort_key = seg.sort_key
            node = child
        node.plugins.append(rec)
    return root


def relpath_to_reference(node_dir: Path, plugin_id: str) -> str:
    """Compute the relative path from a by-menu dir back to a reference file."""
    target = REFERENCE_DIR / f"{plugin_id}.md"
    # Use os.path.relpath via Path semantics; PurePath doesn't help here.
    return str(Path(_relative(node_dir, target)).as_posix())


def _relative(start: Path, target: Path) -> Path:
    """Compute a relative path from `start` (a dir) to `target` (a file).

    Path.relative_to doesn't work across sibling trees, so we do this by
    hand: count how many `..` steps go up to the common ancestor, then
    descend into the target.
    """
    start = start.resolve()
    target = target.resolve()
    # Find common ancestor.
    start_parts = start.parts
    target_parts = target.parts
    common = 0
    for s, t in zip(start_parts, target_parts):
        if s != t:
            break
        common += 1
    ups = [".."] * (len(start_parts) - common)
    downs = list(target_parts[common:])
    return Path(*ups, *downs)

def _make_symlink(link_path: Path, target_path: Path) -> bool:
    """Create or refresh a symlink at `link_path` pointing to `target_path`.

    Uses a relative target so the docs tree remains portable across
    machines and checkouts. Returns True if the link was created or
    updated, False if it was already correct.
    """
    rel_target = _relative(link_path.parent, target_path)
    if link_path.is_symlink():
        # Compare existing link target to the desired one; refresh if drift.
        if Path(link_path.readlink()) == rel_target:
            return False
        link_path.unlink()
    elif link_path.exists():
        # A real file is sitting where we want a symlink — replace it.
        link_path.unlink()
    link_path.symlink_to(rel_target)
    return True


def write_by_menu_tree(root: MenuNode) -> int:
    """Write the by-menu tree of `.pages` files and symlinks.

    Each internal node becomes a directory with a `.pages` file listing
    its children and plugin entries in menu order. Plugin entries are
    backed by symlinks to the canonical pages under `reference/`, since
    awesome-pages does not resolve cross-directory file references.
    """
    if BY_MENU_DIR.exists():
        shutil.rmtree(BY_MENU_DIR)
    BY_MENU_DIR.mkdir(parents=True, exist_ok=True)

    writes = 0

    # Top-level .pages for by-menu/ itself.
    top_children = sorted(root.children.values(), key=lambda n: (n.sort_key, n.label.lower()))
    top_lines = ["nav:"]
    for child in top_children:
        top_lines.append(f"  - {child.label}: {child.slug}")
    write_if_changed(BY_MENU_DIR / ".pages", "\n".join(top_lines) + "\n")
    writes += 1

    # Recurse into children.
    for child in top_children:
        writes += _write_node(child, BY_MENU_DIR / child.slug)

    return writes


def _write_node(node: MenuNode, node_dir: Path) -> int:
    """Write `.pages` for one node, render per-location plugin copies, recurse.

    Plugin pages are rendered fresh for each by-menu location with image
    paths recomputed for that directory's depth, avoiding symlinks and
    keeping every link resolvable in the built site.
    """
    node_dir.mkdir(parents=True, exist_ok=True)
    writes = 0

    lines = ["nav:"]

    # Combine children and plugins into a single ordered list. Plugins use
    # their leaf_sort_key; children use their sort_key. Stable ties broken
    # alphabetically.
    entries: list[tuple[int, str, str]] = []

    for child in node.children.values():
        # Entry: (sort_key, label, nav-line)
        entries.append((child.sort_key, child.label, f"  - {child.label}: {child.slug}"))

    for rec in node.plugins:
        page_path = node_dir / f"{rec.plugin_id}.md"
        page = render_plugin_page(rec, node_dir)
        if write_if_changed(page_path, page):
            writes += 1
        label = rec.leaf_label or rec.title
        entries.append((rec.leaf_sort_key, label, f"  - {label}: {rec.plugin_id}.md"))

    entries.sort(key=lambda e: (e[0], e[1].lower()))
    for _, _, line in entries:
        lines.append(line)

    write_if_changed(node_dir / ".pages", "\n".join(lines) + "\n")
    writes += 1

    for child in node.children.values():
        writes += _write_node(child, node_dir / child.slug)

    return writes


def write_if_changed(path: Path, content: str) -> bool:
    """Write `content` to `path` only if it differs. Returns True on write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def clean_stale_reference(records: list[PluginRecord]) -> None:
    """Remove generated reference files whose plugin no longer exists."""
    if not REFERENCE_DIR.is_dir():
        return
    kept = {f"{r.plugin_id}.md" for r in records}
    kept.add(".pages")
    for path in REFERENCE_DIR.iterdir():
        if path.is_file() and path.name not in kept:
            path.unlink()


def main() -> int:
    """Entry point: read all manifests, write the plugins reference tree."""
    if not MANIFESTS_DIR.is_dir():
        print(f"error: manifests dir not found: {MANIFESTS_DIR}", file=sys.stderr)
        return 1
    records: list[PluginRecord] = []
    for manifest_path in sorted(MANIFESTS_DIR.glob("*/manifest.json")):
        rec = load_manifest(manifest_path)
        if rec is not None:
            records.append(rec)
    if not records:
        print("warning: no plugin manifests found", file=sys.stderr)
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    OVERRIDES_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    # Canonical reference pages (alphabetical, deep-link target).
    for rec in records:
        page = render_plugin_page(rec, REFERENCE_DIR)
        if write_if_changed(REFERENCE_DIR / f"{rec.plugin_id}.md", page):
            written += 1
    # Tree is built once and reused for the landing index and the by-menu nav.
    tree = build_menu_tree(records)
    if write_if_changed(PLUGINS_DIR / "index.md", render_index(tree)):
        written += 1
    if write_if_changed(PLUGINS_DIR / ".pages", render_plugins_root_pages()):
        written += 1
    if write_if_changed(REFERENCE_DIR / ".pages", render_reference_pages_file(records)):
        written += 1
    written += write_by_menu_tree(tree)
    clean_stale_reference(records)
    print(f"plugin docs: {len(records)} plugins, {written} files written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
