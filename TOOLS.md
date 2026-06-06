# POEMCP — Tool Reference

MCP server for Path of Exile wiki, economy, and game data lookups. All tools are prefixed `mcp__poemcp__` in the Claude context.
Entry point: `server.py`.

---

## Player Knowledge

| Tool | Description |
|------|-------------|
| `search_gem` | Search for gems by name or description keyword |
| `get_gem_detail` | Detailed info for a specific gem |
| `search_item` | Search for unique items by name, base type, or mod keyword (fuzzy matching) |
| `get_item_detail` | Detailed info for a specific unique item |
| `search_passive` | Search passive tree nodes by name or stat keyword; filter by type (keystone, notable, mastery, ascendancy) |
| `get_passive_detail` | Detailed info for a passive node including stats, connections, and mastery effects |

---

## Item Mods

| Tool | Description |
|------|-------------|
| `search_mods` | Search item modifiers (prefix/suffix) by item type, optionally filtered by keyword |

---

## Crafting Research (Craft of Exile)

Data is downloaded from craftofexile.com on first use and cached locally (gitignored). Call `update_craftofexile_cache` first if the cache is empty.

| Tool | Description |
|------|-------------|
| `craftofexile_cache_status` | Show which data files are cached and when they were last checked for updates |
| `update_craftofexile_cache` | Download or refresh Craft of Exile data files (checks for version updates via the site's `?v=` timestamps) |
| `search_craft_mods` | Search the full mod pool by keyword; optionally filter by item class |
| `get_craft_base_items` | Look up base items with drop levels; confirm exact base name before crafting |
| `get_craft_tiers` | Full tier breakdown for a mod on a specific item class — min iLvl, value range, and spawn weight per tier |
| `get_fossil_info` | Fossil mod type affinities: which categories it boosts, reduces, or blocks |
| `get_essence_mods` | Guaranteed mod an essence provides on each item slot; filterable by slot |

---

## Environment (Maps & Scarabs)

| Tool | Description |
|------|-------------|
| `env_search` | Search maps and scarabs by name or keyword; filter by category |
| `env_detail` | Detailed info for a specific map or scarab |

---

## Economy

| Tool | Description |
|------|-------------|
| `price_check` | Current poe.ninja price for any item or currency |
| `currency_overview` | Top currency exchange rates for quick reference |

---

## Wiki & External Content

| Tool | Description |
|------|-------------|
| `fetch_wiki_page` | Fetch clean content from a poewiki.net page (navigation/noise stripped) |
| `fetch_reddit_post` | Fetch a Reddit post and its top comments |
| `fetch_youtube_transcript` | Fetch the transcript of a YouTube video |
| `fetch_youtube_description` | Fetch the description of a YouTube video |

---

## Path of Building

| Tool | Description |
|------|-------------|
| `parse_pob` | Parse a PoB export code or share URL (pobb.in / pastebin) and return a build summary |
