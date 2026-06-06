"""Craft of Exile data cache and crafting lookup tools.

Downloads JSON data from craftofexile.com on first use and caches it locally in
reference_data/craftofexile/ (gitignored — each user fetches their own copy).

Freshness: the homepage embeds ?v=<unix_timestamp> on every data file URL.
We compare stored timestamps against the current homepage on each process start
(at most once per CHECK_INTERVAL seconds to avoid hammering the site).
"""

import json
import re
import time
from pathlib import Path
from typing import Any

import httpx

SITE = "https://www.craftofexile.com"
CACHE_DIR = Path(__file__).parents[3] / "reference_data" / "craftofexile"
MANIFEST_FILE = CACHE_DIR / "manifest.json"

# Only re-check the homepage for version updates this often (12 hours)
CHECK_INTERVAL = 43200

# Polite pause between successive file downloads
DOWNLOAD_DELAY = 1.5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                  " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Local filename → URL path (without ?v=)
_DATA_FILES: dict[str, str] = {
    "poec_data.json":       "/json/data/main/poec_data.json",
    "poec_lang.us.json":    "/json/data/lang/poec_lang.us.json",
    "poec_prices.json":     "/json/data/prices/poec_prices.json",
    "poec_common.json":     "/json/data/poec_common.json",
    "poec_affinities.json": "/json/data/affinities/poec_affinities.json",
    "poec_exdata.json":     "/json/data/exdata/poec_exdata.json",
}

# In-memory cache of loaded JSON
_mem: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

def _load_manifest() -> dict:
    if MANIFEST_FILE.exists():
        try:
            return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_manifest(manifest: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Version detection
# ---------------------------------------------------------------------------

def _fetch_remote_versions() -> dict[str, str]:
    """Fetch craftofexile homepage and extract ?v= timestamps for each data file."""
    resp = httpx.get(SITE, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    html = resp.text

    versions: dict[str, str] = {}
    for filename, path in _DATA_FILES.items():
        # Homepage uses relative URLs (no leading slash)
        rel = path.lstrip("/")
        m = re.search(re.escape(rel) + r'\?v=(\d+)', html)
        if m:
            versions[filename] = m.group(1)
    return versions


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def _download_file(filename: str, version: str | None) -> None:
    path = _DATA_FILES[filename]
    url = SITE + path + (f"?v={version}" if version else "")
    resp = httpx.get(url, headers=HEADERS, timeout=60, follow_redirects=True)
    resp.raise_for_status()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / filename).write_bytes(resp.content)
    _mem.pop(filename, None)  # invalidate in-memory cache


def ensure_cache(force: bool = False) -> dict:
    """Download missing or outdated data files from craftofexile.com.

    Checks the homepage for updated ?v= timestamps at most every CHECK_INTERVAL
    seconds so we don't hammer the site. Pass force=True to skip the interval
    guard and re-check immediately.

    Returns a status dict with keys: checked (bool), downloaded (list[str]),
    skipped (list[str]), errors (dict[str, str]).
    """
    manifest = _load_manifest()
    last_check = manifest.get("_last_check", 0)
    now = time.time()

    result: dict = {"checked": False, "downloaded": [], "skipped": [], "errors": {}}

    all_present = all((CACHE_DIR / f).exists() for f in _DATA_FILES)
    due_for_check = (now - last_check) > CHECK_INTERVAL

    if not force and all_present and not due_for_check:
        result["skipped"] = list(_DATA_FILES)
        return result

    # Fetch remote versions
    try:
        remote = _fetch_remote_versions()
        result["checked"] = True
    except Exception as e:
        # If we can't reach the site and have local files, carry on
        if all_present:
            result["skipped"] = list(_DATA_FILES)
            result["errors"]["homepage"] = str(e)
            return result
        raise RuntimeError(
            f"Could not reach craftofexile.com to download data: {e}\n"
            "Check your internet connection and try again."
        ) from e

    time.sleep(DOWNLOAD_DELAY)

    for filename in _DATA_FILES:
        local = CACHE_DIR / filename
        remote_v = remote.get(filename)
        cached_v = manifest.get(filename)

        needs = force or not local.exists() or (remote_v and remote_v != cached_v)
        if not needs:
            result["skipped"].append(filename)
            continue

        try:
            _download_file(filename, remote_v)
            manifest[filename] = remote_v or "unknown"
            result["downloaded"].append(filename)
            # Polite gap between successive downloads
            if filename != list(_DATA_FILES)[-1]:
                time.sleep(DOWNLOAD_DELAY)
        except Exception as e:
            result["errors"][filename] = str(e)

    manifest["_last_check"] = now
    _save_manifest(manifest)
    return result


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

_JS_ASSIGN_RE = re.compile(r'^\s*[A-Za-z_]\w*\s*=\s*')


def _load(filename: str) -> Any:
    """Return parsed JSON for a cached file, triggering download if missing.

    craftofexile serves files as JS assignments (e.g. ``poecd={...}``) rather
    than bare JSON, so we strip the leading ``varname=`` before parsing.
    """
    if filename not in _mem:
        local = CACHE_DIR / filename
        if not local.exists():
            ensure_cache()
        text = (CACHE_DIR / filename).read_text(encoding="utf-8")
        text = _JS_ASSIGN_RE.sub("", text, count=1)
        _mem[filename] = json.loads(text)
    return _mem[filename]


def _lang() -> dict:
    return _load("poec_lang.us.json")


def _data() -> dict:
    return _load("poec_data.json")


def _common() -> dict:
    return _load("poec_common.json")


# ---------------------------------------------------------------------------
# Public MCP tools
# ---------------------------------------------------------------------------


def craftofexile_cache_status() -> str:
    """Show the status of the local Craft of Exile data cache.

    Reports which files are present, their version timestamps, and when the
    site was last checked for updates. Run this before crafting queries to
    confirm data is available, or to see if an update is needed.
    """
    manifest = _load_manifest()
    last_check = manifest.get("_last_check", 0)
    check_str = (
        f"{int((time.time() - last_check) / 60)} minutes ago"
        if last_check else "never"
    )

    lines = [
        f"## Craft of Exile Cache Status",
        f"Cache directory: `{CACHE_DIR}`",
        f"Last version check: {check_str}",
        "",
        "| File | Cached | Version |",
        "|------|--------|---------|",
    ]

    for filename in _DATA_FILES:
        local = CACHE_DIR / filename
        present = "yes" if local.exists() else "MISSING"
        version = manifest.get(filename, "—")
        lines.append(f"| {filename} | {present} | {version} |")

    if not any((CACHE_DIR / f).exists() for f in _DATA_FILES):
        lines += [
            "",
            "**No data cached yet.** Call `update_craftofexile_cache()` to download.",
        ]

    return "\n".join(lines)


def update_craftofexile_cache(force: bool = False) -> str:
    """Download or refresh Craft of Exile data files from craftofexile.com.

    On first call this downloads all files (~a few MB total). Subsequent calls
    only re-download files whose version has changed on the site (checked via
    the ?v= timestamps embedded in the craftofexile homepage).

    The site is checked for updates at most every 12 hours automatically.
    Pass force=True to bypass the interval and check immediately.

    Files are cached in reference_data/craftofexile/ which is gitignored —
    each user fetches their own copy and nothing is redistributed.

    Args:
        force: Re-check the site immediately even if checked recently.
    """
    result = ensure_cache(force=force)

    lines = ["## Craft of Exile Cache Update"]
    if result.get("checked"):
        lines.append("Checked craftofexile.com for updates.")
    else:
        lines.append("Skipped version check (checked recently; pass force=True to override).")

    if result["downloaded"]:
        lines.append(f"\n**Downloaded ({len(result['downloaded'])}):**")
        for f in result["downloaded"]:
            lines.append(f"  - {f}")
    if result["skipped"]:
        lines.append(f"\n**Already up to date ({len(result['skipped'])}):**")
        for f in result["skipped"]:
            lines.append(f"  - {f}")
    if result["errors"]:
        lines.append(f"\n**Errors:**")
        for f, e in result["errors"].items():
            lines.append(f"  - {f}: {e}")

    if not result["downloaded"] and not result["errors"]:
        lines.append("\nAll files are current.")

    return "\n".join(lines)


def search_craft_mods(query: str, item_class: str = "") -> str:
    """Search Craft of Exile mod data by keyword.

    Searches mod text for the given keyword and returns matching mods with
    their IDs and text. Optionally narrow by item class (e.g. 'helmet',
    'ring', 'bow').

    This data comes from craftofexile.com's mod pool — it reflects the full
    list of rollable mods with their weight groupings as craftofexile tracks
    them, which is more crafting-focused than raw game data.

    Args:
        query: Keyword to search mod text for (e.g. 'life', 'fire resistance',
               'attack speed', 'chaos').
        item_class: Optional item class filter to narrow results.
    """
    ensure_cache()
    lang = _lang()

    # poec_lang.us.json structure: top-level key "mod" mapping id -> text
    # (possibly nested under a game-version key — handle both)
    mod_map: dict = {}
    raw = lang
    if "mod" in raw:
        mod_map = raw["mod"]
    else:
        # Try one level of nesting (poe1 / poe2 keys)
        for v in raw.values():
            if isinstance(v, dict) and "mod" in v:
                mod_map = v["mod"]
                break

    if not mod_map:
        return "Could not parse mod data from cached poec_lang.us.json. Try `update_craftofexile_cache(force=True)`."

    q = query.lower()
    matches = []
    for mod_id, mod_entry in mod_map.items():
        # mod_entry may be a string or a dict with a "text" / "name" key
        if isinstance(mod_entry, str):
            text = mod_entry
        elif isinstance(mod_entry, dict):
            text = mod_entry.get("text") or mod_entry.get("name") or str(mod_entry)
        else:
            continue

        if q not in text.lower():
            continue

        if item_class and item_class.lower() not in str(mod_entry).lower():
            continue

        matches.append((mod_id, text))

    if not matches:
        qualifier = f" on '{item_class}'" if item_class else ""
        return f"No mods matching '{query}'{qualifier} found in Craft of Exile data."

    lines = [
        f"## Craft of Exile mods matching '{query}'"
        + (f" (filtered by '{item_class}')" if item_class else ""),
        f"Found {len(matches)} mod(s).\n",
    ]
    for mod_id, text in matches[:100]:
        lines.append(f"- **{mod_id}**: {text}")

    if len(matches) > 100:
        lines.append(f"\n*Showing first 100 of {len(matches)}. Narrow with a more specific query.*")

    return "\n".join(lines)


def get_craft_base_items(query: str = "", item_class: str = "") -> str:
    """Look up base items from Craft of Exile data.

    Returns base item names with their drop levels. Use this to find the
    exact base name to use when setting up a crafting scenario.

    Args:
        query: Optional name filter (e.g. 'sword', 'vaal', 'hubris').
        item_class: Optional class filter (e.g. 'helmet', 'ring', 'bow').
    """
    ensure_cache()
    data = _data()

    # poec_data.json structure: top-level may have poe1/poe2 split or direct bitems
    items_list: list = []
    raw = data
    if "bitems" in raw:
        items_list = raw["bitems"].get("seq", [])
    else:
        for v in raw.values():
            if isinstance(v, dict) and "bitems" in v:
                items_list = v["bitems"].get("seq", [])
                break

    if not items_list:
        return "Could not parse base item data from cached poec_data.json. Try `update_craftofexile_cache(force=True)`."

    q = query.lower()
    cls = item_class.lower()

    matches = []
    for item in items_list:
        name = item.get("name_bitem") or item.get("name") or ""
        if q and q not in name.lower():
            continue
        if cls and cls not in str(item).lower():
            continue
        drop = item.get("drop_level", "?")
        matches.append((name, drop))

    if not matches:
        qualifier = f" in '{item_class}'" if item_class else ""
        return f"No base items matching '{query}'{qualifier} found."

    lines = [
        f"## Craft of Exile base items" + (f" matching '{query}'" if query else ""),
        f"Found {len(matches)} item(s).\n",
        "| Base | Drop Level |",
        "|------|-----------|",
    ]
    for name, drop in sorted(matches, key=lambda x: str(x[0]))[:200]:
        lines.append(f"| {name} | {drop} |")

    if len(matches) > 200:
        lines.append(f"\n*Showing first 200 of {len(matches)}. Use a more specific query.*")

    return "\n".join(lines)
