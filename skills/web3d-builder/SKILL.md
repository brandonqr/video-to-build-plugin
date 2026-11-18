---
name: web3d-builder
description: >-
  Use this skill when you have blueprint.json and tool_bindings.json ready and
  want to orchestrate multi-agent execution (3D assets + Blender GLB + Three.js
  frontend + visual QA) to deliver the final interactive 3D website.
---

# Web 3D Multi-Agent Builder

Orchestrates specialized agents to turn `blueprint.json` + `tool_bindings.json` into a verified, runnable 3D web project.

## Steps

1. **Confirm target workspace**: Ensure `target_dir` is a dedicated project folder (not an unrelated repo).
2. **Run the multi-agent workflow** with `run_workflow` using [workflow.py](./scripts/workflow.py) and pass `Args`:
   ```json
   {
     "target_dir": "C:/dev/my-3d-site",
     "blueprint_path": "C:/dev/my-3d-site/.video-build/blueprint.json",
     "bindings_path": "C:/dev/my-3d-site/.video-build/tool_bindings.json",
     "product_brief": "Build the interactive 3D website following the video's architecture"
   }
   ```
3. **Optimize & audit 3D assets**: For Tripo/Meshy `.glb` outputs, run [optimize_glb.py](./scripts/optimize_glb.py) via headless Blender (`<blender> -b --python optimize_glb.py -- --input raw.glb --output public/models/hero.glb --preview hero-preview.png`) to normalize scale/origin, compress textures to 2K WebP, and visually inspect the rendered audit PNG.
4. **Review workflow output** (`Logs:` and `Output:`): verify the generated `.glb` assets, `npm run build` exit code, and visual QA report.
5. **Present the runnable app** (local dev/preview command, generated files, and any manual step such as Higgsfield OAuth if not yet signed in).
