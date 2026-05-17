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

## Wiki

| Tool | Description |
|------|-------------|
| `fetch_wiki_page` | Fetch clean content from a poewiki.net page (navigation/noise stripped) |

---

## Path of Building

| Tool | Description |
|------|-------------|
| `parse_pob` | Parse a PoB export code or share URL (pobb.in / pastebin) and return a build summary |
