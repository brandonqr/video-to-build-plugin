#!/usr/bin/env python3
"""Extract metadata, captions/transcript, and optional keyframes from a YouTube URL or local video."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def clean_vtt_to_text(vtt_path: Path) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    tag_re = re.compile(r"<[^>]+>")
    ts_re = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}")
    for raw in vtt_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if (
            not line
            or line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or ts_re.match(line)
            or line.isdigit()
        ):
            continue
        cleaned = html.unescape(tag_re.sub("", line)).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            lines.append(cleaned)
    return "\n".join(lines)


def fallback_youtube_metadata(url: str) -> dict:
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
    meta: dict = {"url": url, "extractor": "fallback_oembed"}
    with urllib.request.urlopen(req, timeout=15) as resp:
        meta.update(json.loads(resp.read().decode("utf-8", "ignore")))

    page_req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}
    )
    page_html = urllib.request.urlopen(page_req, timeout=15).read().decode("utf-8", "ignore")
    desc_match = re.search(r'"shortDescription":"(.*?)","isCrawlable"', page_html)
    if desc_match:
        meta["description"] = json.loads('"' + desc_match.group(1) + '"')
    return meta


def extract_with_ytdlp(url: str, out_dir: Path, download_video: bool, lang: str) -> Path | None:
    base_cmd = ["yt-dlp"]
    if shutil.which("node"):
        base_cmd.extend(["--js-runtimes", "node"])

    info_res = run([*base_cmd, "--dump-single-json", "--no-playlist", url])
    compact: dict
    if info_res.returncode == 0 and info_res.stdout.strip():
        raw_info = json.loads(info_res.stdout)
        compact = {
            "id": raw_info.get("id"),
            "title": raw_info.get("title"),
            "uploader": raw_info.get("uploader"),
            "duration": raw_info.get("duration"),
            "webpage_url": raw_info.get("webpage_url"),
            "description": raw_info.get("description"),
            "chapters": raw_info.get("chapters"),
            "tags": raw_info.get("tags"),
            "extractor": "yt-dlp",
        }
    else:
        compact = fallback_youtube_metadata(url)
        compact["yt_dlp_error"] = info_res.stderr.strip()

    sub_tpl = str(out_dir / "subs.%(ext)s")
    sub_res = run(
        [
            *base_cmd,
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            f"{lang},en,es",
            "--sub-format",
            "vtt",
            "-o",
            sub_tpl,
            "--no-playlist",
            url,
        ]
    )

    vtt_files = sorted(out_dir.glob("*.vtt"))
    if vtt_files:
        transcript = clean_vtt_to_text(vtt_files[0])
        (out_dir / "transcript.txt").write_text(transcript, encoding="utf-8")
    elif sub_res.stderr.strip():
        compact["subtitle_warning"] = sub_res.stderr.strip()

    (out_dir / "metadata.json").write_text(
        json.dumps(compact, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if download_video:
        vid_tpl = str(out_dir / "video.%(ext)s")
        dl = run(
            [
                *base_cmd,
                "-f",
                "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b",
                "--merge-output-format",
                "mp4",
                "-o",
                vid_tpl,
                "--no-playlist",
                url,
            ]
        )
        if dl.returncode == 0:
            mp4s = sorted(out_dir.glob("video*.mp4"))
            if mp4s:
                return mp4s[0]
    return None


def extract_frames(video_path: Path, frames_dir: Path, interval_sec: int, max_frames: int) -> list[str]:
    if not shutil.which("ffmpeg"):
        return []
    frames_dir.mkdir(parents=True, exist_ok=True)
    out_pattern = str(frames_dir / "frame_%03d.jpg")
    # Prefer scene-change + periodic fallback capped at max_frames
    vf = f"fps=1/{max(1, interval_sec)},scale=1280:-1"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            vf,
            "-frames:v",
            str(max_frames),
            "-q:v",
            "3",
            out_pattern,
        ]
    )
    return [str(p) for p in sorted(frames_dir.glob("frame_*.jpg"))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract video metadata, transcript, and keyframes.")
    parser.add_argument("--url", help="YouTube or video URL")
    parser.add_argument("--video-file", help="Optional local video file path")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--lang", default="en", help="Preferred subtitle language (default: en)")
    parser.add_argument("--download-video", action="store_true", help="Download MP4 (up to 720p)")
    parser.add_argument("--extract-frames", action="store_true", help="Extract keyframes with ffmpeg")
    parser.add_argument("--interval-sec", type=int, default=20, help="Frame sampling interval in seconds")
    parser.add_argument("--max-frames", type=int, default=16, help="Maximum keyframes to save")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    video_path: Path | None = Path(args.video_file).resolve() if args.video_file else None

    if args.url:
        if shutil.which("yt-dlp"):
            video_path = extract_with_ytdlp(args.url, out_dir, args.download_video, args.lang)
        else:
            meta = fallback_youtube_metadata(args.url)
            meta["warning"] = "yt-dlp not found on PATH; install via `uv tool install yt-dlp` for transcripts/video."
            (out_dir / "metadata.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )
    elif video_path and video_path.exists():
        (out_dir / "metadata.json").write_text(
            json.dumps({"video_file": str(video_path), "extractor": "local_file"}, indent=2),
            encoding="utf-8",
        )
    else:
        print("Provide either --url or an existing --video-file", file=sys.stderr)
        return 2

    frames: list[str] = []
    if args.extract_frames and video_path and video_path.exists():
        frames = extract_frames(video_path, out_dir / "frames", args.interval_sec, args.max_frames)

    summary = {
        "out_dir": str(out_dir),
        "metadata": str(out_dir / "metadata.json"),
        "transcript": str(out_dir / "transcript.txt") if (out_dir / "transcript.txt").exists() else None,
        "frames_count": len(frames),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
