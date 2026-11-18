"""Reusable Antigravity run_workflow script for Video-to-Build 3D web execution."""

from pathlib import Path

target_dir = args["target_dir"]
blueprint_path = args["blueprint_path"]
bindings_path = args["bindings_path"]
product_brief = args.get("product_brief", "Build the interactive 3D website from the blueprint.")

blueprint_text = Path(blueprint_path).read_text(encoding="utf-8")
bindings_text = Path(bindings_path).read_text(encoding="utf-8")

phase("1. Architecture & Asset Manifest")
spec = await agent(
    prompt=f"""You are the Lead Architect.
Target directory: {target_dir}
Product brief: {product_brief}

Blueprint:
{blueprint_text}

Tool bindings:
{bindings_text}

Define the exact file structure, 3D hero asset spec (with named animated nodes, e.g. propellers/parts, and output path under {target_dir}/public/models/hero.glb), media asset list (under {target_dir}/public/media/), and frontend Three.js/Vite component plan.
Return strictly matching the schema.""",
    role="Lead 3D Web Architect",
    schema={
        "type": "object",
        "properties": {
            "project_name": {"type": "string"},
            "hero_glb_path": {"type": "string"},
            "animated_nodes": {"type": "array", "items": {"type": "string"}},
            "media_assets": {"type": "array", "items": {"type": "string"}},
            "frontend_modules": {"type": "array", "items": {"type": "string"}},
            "architecture_notes": {"type": "string"},
        },
        "required": ["project_name", "hero_glb_path", "animated_nodes", "frontend_modules", "architecture_notes"],
    },
)
log("Spec ready:", spec["project_name"])

phase("2. Parallel Production (3D/Media Assets + Three.js Frontend)")

async def build_assets():
    return await agent(
        prompt=f"""You are the 3D & Generative Media Engineer.
Target directory: {target_dir}
Spec: {spec}
Tool bindings: {bindings_text}

1. Using the bound media tools (Higgsfield MCP / `@higgsfield/cli` with `< /dev/null` if available, otherwise procedural/Blender renders), generate required reference images and Seedance 2.5 transition videos (`--mode omni_reference --start-image ... --end-image ...`) into {target_dir}/public/media/, stitched with `ffmpeg` (`-g 3 -movflags +faststart`) for smooth Blob-URL scroll scrubbing.
2. For complex landmarks/environments/organic heroes, first generate an **isolated 1:1 studio diorama reference image** (`gpt_image_2_6` on a clean white/neutral studio backdrop with NO clouds, NO sky, and NO cropped distant mountains), convert it to a textured `.glb` using Higgsfield `tripo_h3_1_image_to_3d` / `meshy_v7_image_to_3d`, and run `optimize_glb.py` in headless Blender (`resolve_blender.py`) to normalize scale/origin, downscale 4K textures to 2K WebP (~3-5 MB), and render an audit PNG. Reserve procedural `bpy` scripts for simple articulated mechanical models.
3. Verify the exported .glb file exists, is under ~6 MB, has clean visual geometry in the preview PNG, and check orientation (`+Z` front in Three.js).
Return a summary of generated files and any fallback used.""",
        role="3D & Assets Agent",
        schema={"type": "string"},
    )

async def build_frontend():
    return await agent(
        prompt=f"""You are the Three.js / WebGL Frontend Engineer.
Target directory: {target_dir}
Spec: {spec}
Blueprint: {blueprint_text}

1. Scaffold a clean Vite + React + TypeScript + Three.js (or @react-three/fiber + @react-three/drei) application inside {target_dir} (do not touch unrelated folders).
2. Implement scroll-driven camera/object choreography, continuous hovering, independent animation for {spec['animated_nodes']} when loading {spec['hero_glb_path']} (with graceful procedural fallback geometry while/if GLB is loading), plus responsive HUD/sections inspired by the blueprint.
3. Run `npm install` and verify TypeScript compilation (`npx tsc --noEmit`).
Return a summary of created modules and build status.""",
        role="Frontend 3D Agent",
        schema={"type": "string"},
    )

assets_result, frontend_result = await parallel([build_assets, build_frontend], lambda fn: fn())
log("Assets agent:", assets_result)
log("Frontend agent:", frontend_result)

phase("3. Integration & Visual QA")
qa_report = await agent(
    prompt=f"""You are the Integration & Visual QA Engineer.
Target directory: {target_dir}
Spec: {spec}
Assets report: {assets_result}
Frontend report: {frontend_result}

1. Verify {spec['hero_glb_path']} and media files are correctly referenced in the frontend code.
2. Run `npm run build` in {target_dir} and ensure exit code 0.
3. Start the local preview/dev server briefly, inspect the rendered 3D page (via Playwright / headless browser or browser tool), verify zero console/WebGL errors, and check interactive scroll/controls.
4. Fix any integration bug you find and re-run `npm run build`.
Return the final QA report.""",
    role="QA & Integration Agent",
    schema={
        "type": "object",
        "properties": {
            "build_passed": {"type": "boolean"},
            "runtime_checked": {"type": "boolean"},
            "issues_fixed": {"type": "array", "items": {"type": "string"}},
            "preview_command": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": ["build_passed", "runtime_checked", "preview_command", "summary"],
    },
)
log("QA Result:", qa_report)
qa_report
