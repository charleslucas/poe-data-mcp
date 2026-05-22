import re
import shutil
import subprocess

# Links worth extracting from a build guide description
_LINK_PATTERNS = {
    "pobb.in": re.compile(r"https?://pobb\.in/\S+"),
    "poedb.tw": re.compile(r"https?://poedb\.tw/\S+PathOfBuilding\?id=\S+"),
    "pastebin": re.compile(r"https?://pastebin\.com/\S+"),
    "mobalytics": re.compile(r"https?://mobalytics\.gg/poe/\S+"),
    "maxroll": re.compile(r"https?://maxroll\.gg/poe/\S+"),
    "poe_forum": re.compile(r"https?://www\.pathofexile\.com/forum/view-thread/\d+"),
}


def fetch_youtube_description(url: str) -> str:
    """Fetch the title and description from a YouTube video URL using yt-dlp.

    Extracts any Path of Building links (pobb.in, poedb.tw, pastebin) and
    common guide site links (Mobalytics, Maxroll) found in the description.
    Requires yt-dlp to be installed (pip install yt-dlp).

    Args:
        url: YouTube video URL (e.g. https://www.youtube.com/watch?v=...)
    """
    if shutil.which("yt-dlp") is None:
        return (
            "yt-dlp is not installed. Install it with: pip install yt-dlp\n"
            "Alternatively, paste the video description text directly."
        )

    try:
        title_result = subprocess.run(
            ["yt-dlp", "--get-title", "--no-warnings", url],
            capture_output=True, text=True, timeout=30
        )
        desc_result = subprocess.run(
            ["yt-dlp", "--get-description", "--no-warnings", url],
            capture_output=True, text=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        return f"Timed out fetching YouTube description for: {url}"
    except Exception as e:
        return f"Failed to run yt-dlp: {e}"

    if desc_result.returncode != 0:
        err = desc_result.stderr.strip()
        return f"yt-dlp failed for {url}: {err or 'unknown error'}"

    title = title_result.stdout.strip()
    description = desc_result.stdout.strip()

    # Extract links
    found: dict[str, list[str]] = {}
    for label, pattern in _LINK_PATTERNS.items():
        matches = [m.rstrip(".,)") for m in pattern.findall(description)]
        if matches:
            found[label] = list(dict.fromkeys(matches))  # dedupe, preserve order

    lines = []
    if title:
        lines.append(f"# {title}")
        lines.append("")

    if found:
        lines.append("## Extracted Links")
        for label, links in found.items():
            for link in links:
                lines.append(f"- **{label}:** {link}")
        lines.append("")

    lines.append("## Description")
    lines.append(description)

    return "\n".join(lines)
