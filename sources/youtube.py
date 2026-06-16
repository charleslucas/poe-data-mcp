import json
import os
import re
import shutil
import subprocess
import tempfile

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
            ["yt-dlp", "--get-title", "--socket-timeout", "20", "--no-warnings", url],
            capture_output=True, text=True, timeout=30
        )
        desc_result = subprocess.run(
            ["yt-dlp", "--get-description", "--socket-timeout", "20", "--no-warnings", url],
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


def fetch_youtube_transcript(url: str, include_timestamps: bool = False) -> str:
    """Fetch the auto-generated transcript from a YouTube video using yt-dlp.

    Returns the full spoken transcript as clean text, optionally with
    timestamps. Useful for extracting build theory reasoning that creators
    explain verbally but don't write in the description.

    Chapter markers from the video description are shown at the top so you
    can navigate to specific sections (gear, passive tree, skill gems, etc.).

    Args:
        url: YouTube video URL (e.g. https://www.youtube.com/watch?v=...)
        include_timestamps: If True, include time markers (MM:SS) inline.
                            Default False returns clean readable prose.
    """
    if shutil.which("yt-dlp") is None:
        return (
            "yt-dlp is not installed. Install it with: pip install yt-dlp\n"
            "Alternatively, use the YouTube transcript feature in your browser."
        )

    # Get title and chapter list from description first (lightweight)
    try:
        title_result = subprocess.run(
            ["yt-dlp", "--get-title", "--socket-timeout", "20", "--no-warnings", url],
            capture_output=True, text=True, timeout=15
        )
        desc_result = subprocess.run(
            ["yt-dlp", "--get-description", "--socket-timeout", "20", "--no-warnings", url],
            capture_output=True, text=True, timeout=15
        )
        title = title_result.stdout.strip()
        description = desc_result.stdout.strip()
    except Exception:
        title = ""
        description = ""

    # Extract chapter timestamps from description
    chapters = re.findall(r'(\d+:\d+(?::\d+)?)\s+(.+)', description)

    # Download transcript to temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "transcript")
        # --socket-timeout makes a stalled connection fail fast instead of
        # blocking forever; bounded --retries then recovers. Without these,
        # yt-dlp's defaults (no socket timeout, 10 retries) can hang past the
        # wrapper timeout on an intermittently stalled timedtext download.
        try:
            result = subprocess.run(
                ["yt-dlp", "--write-auto-subs", "--sub-lang", "en",
                 "--sub-format", "json3", "--skip-download", "--no-warnings",
                 "--socket-timeout", "20", "--retries", "3",
                 "-o", out_path, url],
                capture_output=True, text=True, timeout=120
            )
        except subprocess.TimeoutExpired:
            return (
                f"Timed out fetching YouTube transcript for: {url}\n"
                "yt-dlp stalled on the subtitle download (usually a transient "
                "stalled connection, not a missing transcript). Try again."
            )
        if result.returncode != 0:
            err = result.stderr.strip()
            return f"yt-dlp failed to fetch transcript: {err or 'unknown error'}"

        # Find the downloaded file
        import glob
        files = glob.glob(os.path.join(tmpdir, "*.json3"))
        if not files:
            return "No transcript available for this video (auto-captions may be disabled)."

        with open(files[0], encoding="utf-8") as f:
            data = json.load(f)

    # Parse json3 events into text segments with optional timestamps
    segments = []
    for event in data.get("events", []):
        t_ms = event.get("tStartMs", 0)
        text = "".join(s.get("utf8", "") for s in event.get("segs", [])).strip()
        if text and text != "\n":
            segments.append((t_ms, text))

    if not segments:
        return "Transcript was empty or could not be parsed."

    # Build output
    lines = []
    if title:
        lines.append(f"# {title}")
        lines.append("")

    if chapters:
        lines.append("## Chapters")
        for ts, name in chapters:
            lines.append(f"- {ts} — {name}")
        lines.append("")

    lines.append("## Transcript")

    if include_timestamps:
        for t_ms, text in segments:
            secs = int(t_ms / 1000)
            mm, ss = divmod(secs, 60)
            lines.append(f"[{mm:02d}:{ss:02d}] {text}")
    else:
        # Join into clean prose, deduplicating overlapping auto-caption fragments
        words = []
        prev = ""
        for _, text in segments:
            text = re.sub(r'\s+', ' ', text).strip()
            if text and text != prev:
                words.append(text)
                prev = text
        lines.append(" ".join(words))

    total_chars = sum(len(t) for _, t in segments)
    lines.append(f"\n*Transcript: ~{total_chars:,} characters*")

    return "\n".join(lines)
