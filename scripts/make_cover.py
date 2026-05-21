"""Generate the hackathon submission cover image (1200x675, 16:9 thumb).

Reuses the same palette + typography as the intro slide so the cover and
the demo video read as one set.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1200, 675
FG = "#0f172a"
FG_MUTED = "#475569"
ACCENT = "#4285f4"        # Google blue
ACCENT_2 = "#1a56db"
BG = "#ffffff"
PANEL = "#f8fafc"

SF = "/System/Library/Fonts/SFNS.ttf"
SFI = "/System/Library/Fonts/SFNSItalic.ttf"
MONO = "/System/Library/Fonts/SFNSMono.ttf"
if not Path(MONO).exists():
    MONO = "/System/Library/Fonts/Menlo.ttc"


def font(size, mono=False, italic=False):
    path = MONO if mono else (SFI if italic else SF)
    return ImageFont.truetype(path, size)


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Footer band
    d.rectangle([(0, H - 40), (W, H)], fill=PANEL)
    d.text((24, H - 32),
           "github.com/MukundaKatta/gemini-vertex-search-agent",
           font=font(16), fill=FG_MUTED)
    d.text((W - 200, H - 32), "Apache 2.0", font=font(16), fill=FG_MUTED)

    # Title block
    d.text((60, 100), "gemini-vertex-search-agent", font=font(60), fill=FG)
    d.rectangle([(60, 188), (220, 196)], fill=ACCENT)

    d.text((60, 228),
           "Plain-English questions over enterprise docs,",
           font=font(28), fill=FG_MUTED)
    d.text((60, 268),
           "answered with byte-for-byte verbatim citations.",
           font=font(28), fill=FG_MUTED)

    d.text((60, 370),
           "Vertex AI Search + Gemini 2.5 ADK",
           font=font(24, mono=True), fill=ACCENT_2)
    d.text((60, 410),
           "(Discovery Engine + GenAI App Builder credits)",
           font=font(20), fill=FG_MUTED)

    d.text((60, 510),
           "HackerNoon Intelligent Search & Retrieval (Algolia)",
           font=font(22), fill=FG)
    d.text((60, 542),
           "+ Foundational Tech + Neo4j tracks  ·  Jun 5, 2026",
           font=font(20), fill=FG_MUTED)

    out = Path("/Users/ubl/gemini-vertex-search-agent/.video-build/cover.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    size = out.stat().st_size / 1024
    print(f"DONE: {out} ({size:.1f} KB)")


if __name__ == "__main__":
    main()
