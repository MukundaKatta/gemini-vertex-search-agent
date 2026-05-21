"""Drive the deployed gemini-vertex-search-agent Cloud Run app through Playwright,
record real screen footage of the agent functioning, save as MP4.

Output: ~60-90s WebM/MP4 showing the actual deployed Streamlit dashboard
loading, accepting a question, running the agent, and rendering the
verbatim NL→MongoDB answer. This is the "footage that shows the Project
functioning on the platform(s) for which it was built" the Devpost
moderator asked for.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


URL = "https://gemini-vertex-search-agent-1029931682737.us-central1.run.app/"
OUT_DIR = Path("/Users/ubl/gemini-vertex-search-agent/.video-build")
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_DIR = OUT_DIR / "playwright-videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    print("[1/4] launching Chromium (headed but offscreen)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        print(f"[2/4] navigating to {URL} ...")
        page.goto(URL, wait_until="networkidle", timeout=120_000)
        # Streamlit takes a beat to render after networkidle.
        page.wait_for_selector("text=gemini-vertex-search-agent", timeout=60_000)
        print("    dashboard rendered")
        time.sleep(2)

        # Make sure the sidebar question is what the demo narrates.
        question = "how do I rotate the production database credentials"
        # The Streamlit textarea is the first textarea on the page.
        textareas = page.locator("textarea")
        if textareas.count() > 0:
            textareas.first.fill(question)
            print(f"    question set: {question[:60]}...")
            time.sleep(1.5)

        # Click "Search docs" — Streamlit's buttons have a wrapping kind=primary.
        print("[3/4] clicking Search docs and waiting for the agent response...")
        page.locator("button", has_text="Search docs").first.click()
        # Wait for the spinner to disappear (means the agent finished).
        # Streamlit shows "Running Vertex AI Gemini..." while busy.
        page.wait_for_selector("text=Running Vertex AI", timeout=120_000)
        print("    agent started running")
        # Now wait for that text to go away (agent done).
        page.wait_for_selector("text=Running Vertex AI", state="detached", timeout=300_000)
        print("    agent finished")
        # Wait for the final NEXT STEP label to confirm full render.
        try:
            page.wait_for_selector("text=NEXT STEP", timeout=60_000)
        except Exception:
            page.wait_for_selector("text=ANSWER", timeout=30_000)
        print("    final answer rendered")
        # Dwell on the final result so the recording captures it clearly.
        time.sleep(5)
        # Scroll through the answer to show all sections.
        page.mouse.wheel(0, 200)
        time.sleep(2)
        page.mouse.wheel(0, 200)
        time.sleep(2)
        page.mouse.wheel(0, 300)
        time.sleep(2)
        page.mouse.wheel(0, 300)
        time.sleep(3)

        print("[4/4] closing context to flush the recording...")
        context.close()
        browser.close()

    # Find the recorded webm
    webms = sorted(VIDEO_DIR.glob("*.webm"), key=lambda p: p.stat().st_mtime)
    if not webms:
        sys.exit("no recording produced")
    webm = webms[-1]
    size = webm.stat().st_size / (1024 * 1024)

    # Transcode to MP4 with H.264 + AAC silence (so it concats cleanly later).
    mp4 = OUT_DIR / "real_footage.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(webm),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-shortest",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "128k",
        str(mp4),
    ], check=True)

    # Probe duration
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(mp4)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    print(f"\nDONE: {mp4}  ({size:.1f} MB webm, {float(dur):.1f}s mp4)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
