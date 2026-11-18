# Video-to-Build Plugin Rules

When the `video-to-build` workflow is invoked:

1. **Workspace isolation**: Never generate a new target web project inside an unrelated existing repository unless the user explicitly asks to integrate into it. If the current workspace already has an unrelated project, ask or create a dedicated target subfolder / new workspace path first.
2. **Evidence over guessing**: Always inspect the extracted `metadata.json`, `transcript.txt`, and representative frames from `extract_video.py` before writing `blueprint.json`.
3. **Tool preference**:
   - Use connected MCP servers first (`higgsfield`, `blender`).
   - Fall back to `@higgsfield/cli` (if authenticated) or `HKUDS/CLI-Anything` harnesses (`cli-anything-blender`, `cli-anything-browser`, etc.), or headless Blender resolved cross-platform via `BLENDER_BIN` / `blender` on `PATH` / `skills/tool-resolver/scripts/resolve_blender.py` (`<blender> -b --python ...`).
4. **3D geometry & landscape fidelity (avoid burning tokens on manual `bpy` sculpting)**:
   - For organic terrain, monuments, landmarks, or detailed hero assets, do NOT hand-code thousands of lines of procedural `bpy` boxes/cones. Instead, generate an **isolated 1:1 studio diorama reference image** via Higgsfield (`gpt_image_2_6` on a pure neutral/white studio backdrop with **no sky, no clouds, and no cropped background mountains**) and convert it to a clean 360° `.glb` using **`tripo_h3_1_image_to_3d`** or **`meshy_v7_image_to_3d`** (`generate_3d` MCP or `higgsfield generate create ... < /dev/null`).
   - Always run `skills/web3d-builder/scripts/optimize_glb.py` in headless Blender to bake centered bounds/orientation, downscale 4K textures to 2K WebP (~3–5 MB), and render an audit PNG before wiring into Three.js.
   - Reserve procedural Blender `bpy` scripts for simple mechanical objects with named articulated sub-parts (e.g., drone rotors/wheels) or `.glb` normalization.
   - For narrative scroll tours across real-world scenes or interiors, pair Higgsfield **Seedance 2.5** (`start_image` → `end_image`) scroll-scrubbed cinema video (preloaded as a Blob URL) with the Tripo/Meshy `.glb` in free Explore 3D mode.
5. **CLI execution on Windows**: Invoke `higgsfield` with `< /dev/null` (prevents Go CLI stdin hang) and use Git Bash (`bash.exe`) or `.cmd` shims (`npm.cmd`, `npx.cmd`) instead of PowerShell `.ps1` wrappers.
6. **Mandatory verification**: Before reporting completion, run `npm run build` (or project build/test commands) and visually verify the live app (WebGL canvas, console errors, scroll/interaction states) via `/browser` or Playwright.
