---
name: tool-resolver
description: >-
  Use this skill after video-blueprint to verify which MCP servers, local CLIs,
  and HKUDS/CLI-Anything harnesses are ready on the machine, and map any missing
  external services to working alternatives before building.
---

# Tool & Capability Resolver

Checks what tools the `blueprint.json` requires and resolves each one to a working local or MCP integration.

## Resolution Priority

1. **Higgsfield (images, concepts, video footage, 3D generation)**:
   * **MCP option**: Check if the `higgsfield` MCP server (`https://mcp.higgsfield.ai/mcp`) is connected and authenticated.
   * **CLI option**: Check if `@higgsfield/cli` (`higgsfield`) is installed and logged in. On Windows, always pass `< /dev/null` when running `higgsfield generate ...` so stdin does not block, and prefer Git Bash (`bash.exe`) or `higgsfield.cmd`.
   * **3D & Video models inside Higgsfield**: Prefer `tripo_h3_1_image_to_3d` / `tripo_h3_1_multiview_to_3d` / `meshy_v7_image_to_3d` for detailed 3D `.glb` meshes from reference images, and `seedance_2_5` (`--mode omni_reference --start-image ... --end-image ...`) for cinematic scroll-transition video clips.
   * **Fallback**: If Higgsfield is unavailable or unauthenticated, generate procedural textures/SVG/shaders or local 3D geometry in Blender instead of failing.

2. **Blender (consistent 3D meshes, materials, animations -> `.glb`)**:
   * **MCP option**: Use the active `blender` MCP (`get_addon_status`, `execute_blender_code`, `look`, `generate_3d`) when Blender's addon bridge is running.
   * **CLI-Anything option**: Check `cli-anything-blender` (via `HKUDS/CLI-Anything` / `cli-hub install blender`).
   * **Headless Blender fallback**: Run [resolve_blender.py](./scripts/resolve_blender.py) (checks `BLENDER_BIN`, `PATH`, and OS install paths on Windows/macOS/Linux) and invoke `<blender_path> -b --python <script.py>` to generate scenes and export `.glb` + preview renders (`PNG`).

3. **Browser & Visual QA**:
   * Prefer Antigravity's built-in `/browser` subagent, `cli-anything-browser`, or `npx playwright` tests to verify the running web app, WebGL canvas rendering, and console errors.

4. **Other Desktop Software Mentioned in a Video**:
   * Check `cli-hub search <software>` (from `HKUDS/CLI-Anything`) to install an existing agent-native CLI harness + `SKILL.md` before writing ad-hoc wrappers.

## Output

Produce `<OUT_DIR>/tool_bindings.json` mapping each `required_tools` entry in `blueprint.json` to `active_mcp`, `cli_command`, or `fallback_strategy`.
