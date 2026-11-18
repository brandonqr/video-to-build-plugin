---
name: video-blueprint
description: >-
  Use this skill when the user provides a YouTube tutorial URL (or local video file)
  and wants to extract its methodology, tools, assets, and architecture into an
  actionable blueprint.json for multi-agent execution.
---

# Video Blueprint Extractor

Turns a YouTube tutorial or local walkthrough video into a structured `blueprint.json` that downstream agents can execute.

## Steps

1. **Extract metadata, transcript, and keyframes** into a scratch/artifacts directory (for example `./.video-build/<video_id>`):
   ```powershell
   python "<PLUGIN_DIR>/skills/video-blueprint/scripts/extract_video.py" --url "<YOUTUBE_URL>" --out "<OUT_DIR>"
   ```
   * Note: Locate `extract_video.py` relative to this `SKILL.md` at [extract_video.py](./scripts/extract_video.py).
   * Pass `--download-video --extract-frames` when you need visual keyframes via `ffmpeg` (requires `yt-dlp` and `ffmpeg` on PATH). Without `--download-video`, it still extracts full metadata and subtitles fast.

2. **Inspect extracted artifacts**:
   * Read `<OUT_DIR>/metadata.json` for title, description, chapters, and links.
   * Read `<OUT_DIR>/transcript.txt` (if subtitles exist) for exact tool names, prompts, and workflow decisions.
   * If keyframes were extracted in `<OUT_DIR>/frames/`, inspect key frames with `read_file` to capture UI layouts, visual style, color palette, and 3D scene structure.

3. **Synthesize `<OUT_DIR>/blueprint.json`** with this structure:
   ```json
   {
     "source_url": "...",
     "title": "...",
     "goal_summary": "...",
     "stack": {
       "frontend": ["vite", "react", "three", "@react-three/fiber"],
       "assets_3d": ["blender", "glb"],
       "media_ai": ["higgsfield"]
     },
     "required_tools": [
       {"name": "higgsfield", "purpose": "concept art and video backdrops", "preferred": "mcp|cli"},
       {"name": "blender", "purpose": "consistent hero 3D model + animations -> GLB", "preferred": "mcp|cli"}
     ],
     "phases": [
       {"id": "assets", "tasks": ["..."]},
       {"id": "frontend", "tasks": ["..."]},
       {"id": "qa", "tasks": ["..."]}
     ],
     "verification_checklist": [
       "GLB loads without errors and animated sub-nodes rotate/hover smoothly",
       "npm run build exits 0",
       "Zero WebGL/console errors in browser check"
     ]
   }
   ```

4. **Validate** that `blueprint.json` is valid JSON and covers every concrete requirement before handing off to `tool-resolver` and `web3d-builder`.
