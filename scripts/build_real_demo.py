"""Build the final gemini-vertex-search-agent demo video.

Composition:
  - intro slide with TTS narration (Vertex AI Search + Algolia track framing)
  - real Cloud Run footage from record_real_demo.py
  - outro slide with TTS narration

Under the typical 3-minute hackathon video limit. The centerpiece is real
footage showing the deployed Streamlit dashboard answering "how do I
rotate the production database credentials" with byte-for-byte verbatim
quotes from the runbook indexed in Vertex AI Search.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1920, 1080
FG = "#0f172a"
FG_MUTED = "#475569"
ACCENT = "#4285f4"          # Google blue
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


def draw_intro(img, d):
    d.rectangle([(0, 0), (W, H)], fill=BG)
    d.rectangle([(0, H - 56), (W, H)], fill=PANEL)
    d.text((48, H - 44),
           "github.com/MukundaKatta/gemini-vertex-search-agent",
           font=font(22), fill=FG_MUTED)
    d.text((W - 270, H - 44), "Apache 2.0", font=font(22), fill=FG_MUTED)
    d.text((96, 220), "gemini-vertex-search-agent", font=font(92), fill=FG)
    d.rectangle([(96, 340), (340, 352)], fill=ACCENT)
    d.text((96, 390),
           "Plain-English questions over enterprise docs,",
           font=font(40), fill=FG_MUTED)
    d.text((96, 450),
           "byte-for-byte verbatim citations from the index.",
           font=font(40), fill=FG_MUTED)
    d.text((96, 580),
           "HackerNoon Intelligent Search & Retrieval",
           font=font(32), fill=FG)
    d.text((96, 625),
           "(Algolia track) + Foundational Tech + Neo4j",
           font=font(32), fill=FG_MUTED)
    d.text((96, 740),
           "What follows is real footage of the deployed",
           font=font(28, italic=True), fill=FG_MUTED)
    d.text((96, 780),
           "Cloud Run dashboard answering a live question.",
           font=font(28, italic=True), fill=FG_MUTED)


def draw_outro(img, d):
    d.rectangle([(0, 0), (W, H)], fill=BG)
    d.text((96, 180), "gemini-vertex-search-agent", font=font(64), fill=FG)
    d.rectangle([(96, 270), (340, 282)], fill=ACCENT)
    d.text((96, 320),
           "github.com/MukundaKatta/gemini-vertex-search-agent",
           font=font(28, mono=True), fill=ACCENT_2)
    d.text((96, 390),
           "gemini-vertex-search-agent-1029931682737.us-central1.run.app",
           font=font(26, mono=True), fill=ACCENT_2)
    d.text((96, 510),
           "Google Cloud Agent Builder (ADK)",
           font=font(32), fill=FG_MUTED)
    d.text((96, 560),
           "+ Gemini 2.5 Flash on Vertex AI",
           font=font(32), fill=FG_MUTED)
    d.text((96, 610),
           "+ Vertex AI Search (Discovery Engine)",
           font=font(32), fill=FG_MUTED)
    d.text((96, 660),
           "+ GenAI App Builder credits",
           font=font(32), fill=FG_MUTED)
    d.text((96, 770),
           "Every command and number is byte-for-byte from",
           font=font(26, italic=True), fill=FG_MUTED)
    d.text((96, 810),
           "the runbook indexed in Vertex AI Search. Nothing fabricated.",
           font=font(26, italic=True), fill=FG_MUTED)
    d.text((96, 880),
           "Apache 2.0. Mukunda Katta, independent.",
           font=font(28, italic=True), fill=FG_MUTED)


INTRO_NARRATION = (
    "Gemini vertex search agent. An enterprise document Q and A agent on "
    "Google Cloud Agent Builder, wired to Vertex A I Search, also known as "
    "Discovery Engine. Submission for the Hacker Noon Intelligent Search "
    "and Retrieval track sponsored by Algolia, plus the Foundational Tech "
    "and Neo4j tracks. What follows is real footage of the deployed Cloud "
    "Run dashboard answering a live question, with byte for byte verbatim "
    "quotes from the indexed runbook."
)


OUTRO_NARRATION = (
    "The commands you just saw, rotate prod db creds dot s h, jumpbox prod "
    "one, wait 15 minutes, health check db dot s h, all came byte for byte "
    "from the runbook indexed in Vertex A I Search. The agent never "
    "fabricates. Built on the A D K with Gemini two point five Flash, wired "
    "to Discovery Engine, burning Gen A I App Builder credits as designed. "
    "Apache two point zero. Thank you."
)


def render_slide(name, draw_fn, outdir):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    draw_fn(img, d)
    p = outdir / f"{name}.png"
    img.save(p, "PNG", optimize=True)
    return p


def say_to_m4a(text, outpath):
    aiff = outpath.with_suffix(".aiff")
    subprocess.run(
        ["say", "-v", "Samantha", "-r", "175", "-o", str(aiff), text],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff),
         "-c:a", "aac", "-b:a", "128k", str(outpath)],
        check=True,
    )
    aiff.unlink(missing_ok=True)


def make_slide_segment(png, m4a, out):
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(m4a)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    seg_dur = float(dur) + 0.5
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(png),
        "-i", str(m4a),
        "-af", "apad=pad_dur=0.5",
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-r", "30", "-t", f"{seg_dur:.2f}",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", str(out),
    ], check=True)
    return out, seg_dur


def main():
    outdir = Path("/Users/ubl/gemini-vertex-search-agent/.video-build")
    outdir.mkdir(parents=True, exist_ok=True)

    real = outdir / "real_footage.mp4"
    if not real.exists():
        sys.exit(f"missing real footage at {real}; run record_real_demo.py first")

    for needed in ("ffmpeg", "ffprobe", "say"):
        if shutil.which(needed) is None:
            sys.exit(f"missing tool: {needed}")

    print("[1/4] slides...")
    intro_png  = render_slide("01_intro",  draw_intro,  outdir)
    outro_png  = render_slide("99_outro",  draw_outro,  outdir)
    print(f"  rendered {intro_png.name}")
    print(f"  rendered {outro_png.name}")

    print("[2/4] audio...")
    intro_m4a = outdir / "01_intro.m4a"
    outro_m4a = outdir / "99_outro.m4a"
    say_to_m4a(INTRO_NARRATION, intro_m4a)
    print(f"  spoke {intro_m4a.name}")
    say_to_m4a(OUTRO_NARRATION, outro_m4a)
    print(f"  spoke {outro_m4a.name}")

    print("[3/4] segments...")
    intro_seg, intro_dur = make_slide_segment(intro_png, intro_m4a, outdir / "seg_01_intro.mp4")
    outro_seg, outro_dur = make_slide_segment(outro_png, outro_m4a, outdir / "seg_99_outro.mp4")
    real_dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(real)],
        capture_output=True, text=True, check=True,
    ).stdout.strip())
    print(f"  intro {intro_dur:.1f}s · real {real_dur:.1f}s · outro {outro_dur:.1f}s")

    print("[4/4] concat...")
    list_file = outdir / "concat.txt"
    list_file.write_text("\n".join([
        f"file '{intro_seg.resolve()}'",
        f"file '{real.resolve()}'",
        f"file '{outro_seg.resolve()}'",
    ]) + "\n")

    final = outdir / "demo.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "128k",
        str(final),
    ], check=True)

    size_mb = final.stat().st_size / (1024 * 1024)
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(final)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"\nDONE: {final}  ({size_mb:.1f} MB, {float(dur):.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
