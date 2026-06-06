from mcp.server.fastmcp import FastMCP

from sources.player.gems import get_gem_detail, search_gem
from sources.player.items import get_item_detail, search_item
from sources.player.passives import get_passive_detail, search_passive
from sources.mods.item_mods import search_mods
from sources.crafting.craftofexile import (
    craftofexile_cache_status,
    update_craftofexile_cache,
    search_craft_mods,
    get_craft_base_items,
    get_craft_tiers,
    get_fossil_info,
    get_essence_mods,
)
from sources.env import env_detail, env_search
from sources.economy import currency_overview, price_check
from sources.wiki import fetch_wiki_page
from sources.player.pob import parse_pob
from sources.youtube import fetch_youtube_description, fetch_youtube_transcript
from sources.reddit import fetch_reddit_post

mcp = FastMCP("PoeMCP")

# --- Player domain ---
mcp.tool()(search_gem)
mcp.tool()(get_gem_detail)
mcp.tool()(search_item)
mcp.tool()(get_item_detail)
mcp.tool()(search_passive)
mcp.tool()(get_passive_detail)

# --- Mods domain ---
mcp.tool()(search_mods)

# --- Craft of Exile ---
mcp.tool()(craftofexile_cache_status)
mcp.tool()(update_craftofexile_cache)
mcp.tool()(search_craft_mods)
mcp.tool()(get_craft_base_items)
mcp.tool()(get_craft_tiers)
mcp.tool()(get_fossil_info)
mcp.tool()(get_essence_mods)

# --- Env domain ---
mcp.tool()(env_search)
mcp.tool()(env_detail)

# --- Economy domain ---
mcp.tool()(price_check)
mcp.tool()(currency_overview)

# --- Universal ---
mcp.tool()(fetch_wiki_page)

# --- PoB ---
mcp.tool()(parse_pob)

# --- YouTube ---
mcp.tool()(fetch_youtube_description)
mcp.tool()(fetch_youtube_transcript)

# --- Reddit ---
mcp.tool()(fetch_reddit_post)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
