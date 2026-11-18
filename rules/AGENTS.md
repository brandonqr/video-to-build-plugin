# Video-to-Build Plugin Rules

When the `video-to-build` workflow is invoked:

1. **Workspace isolation**: Never generate a new target web project inside an unrelated existing repository unless the user explicitly asks to integrate into it. If the current workspace already has an unrelated project, ask or create a dedicated target subfolder / new workspace path first.
2. **Evidence over guessing**: Always inspect the extracted `metadata.json`, `transcript.txt`, and representative frames from `extract_video.py` before writing `blueprint.json`.
3. **Tool preference**:
   - Use connected MCP servers first (`higgsfield`, `blender`).
   - Fall back to `@higgsfield/cli` (if authenticated) or `HKUDS/CLI-Anything` harnesses (`cli-anything-blender`, `cli-anything-browser`, etc.), or headless Blender resolved cross-platform via `BLENDER_BIN` / `blender` on `PATH` / `skills/tool-resolver/scripts/resolve_blender.py` (`<blender> -b --python ...`).
4. **3D geometry consistency**: When building interactive 3D web experiences, do NOT rely solely on AI-generated video for hero objects that require consistent camera/scroll angles. Build or refine the hero 3D mesh in Blender with clean origin, proper scale, named animated parts (e.g., rotors/wheels), and export `.glb`.
5. **Mandatory verification**: Before reporting completion, run `npm run build` (or project build/test commands) and visually verify the live app (WebGL canvas, console errors, scroll/interaction states) via `/browser` or Playwright.
