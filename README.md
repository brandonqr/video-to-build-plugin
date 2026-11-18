# video-to-build-plugin

Plugin reutilizable para **Antigravity CLI (`agy`)** + **Toolbox Docker** que convierte tutoriales en video (por ejemplo de YouTube) en un **blueprint ejecutable**, resuelve las herramientas necesarias (**Higgsfield MCP/CLI**, **Blender**, **`HKUDS/CLI-Anything`**) y orquesta los agentes necesarios para construir y verificar el proyecto final (p. ej. una web 3D interactiva con Blender + Three.js).

---

## Opción 1: Instalación nativa en tu máquina (recomendada si ya usas `agy`)

1. **Instalar herramientas base:**
   ```bash
   uv tool install yt-dlp
   uv tool install cli-anything-hub
   ```
   *(Asegúrate también de tener `ffmpeg` y Blender instalados; `resolve_blender.py` detecta Blender automáticamente en Windows, macOS y Linux o mediante `BLENDER_BIN`).*

2. **Conectar tu cuenta de Higgsfield:**
   ```bash
   agy mcp add --type http higgsfield https://mcp.higgsfield.ai/mcp
   ```
   Y opcionalmente como respaldo CLI:
   ```bash
   npm install -g @higgsfield/cli
   higgsfield auth login
   ```

3. **Validar e instalar el plugin globalmente:**
   ```bash
   agy plugin validate . --strict
   agy plugin install .
   ```

---

## Opción 2: Docker Toolbox (cero dependencias locales)

Incluye en una sola imagen: **Python 3.12**, **Node.js 22**, **`yt-dlp`**, **`ffmpeg`**, **Blender (headless)**, **`cli-anything-hub`**, **`@higgsfield/cli`** y **Playwright + Chromium (con soporte OpenGL/Mesa/Xvfb)**.

```bash
docker compose build
docker compose run --rm toolbox
```

Dentro del contenedor:
* Tu carpeta `./workspace` queda montada en `/workspace`.
* Las credenciales/configuración de CLI se guardan en el volumen persistente `higgsfield_config`.
* Puedes probar la extracción de cualquier video directamente:
  ```bash
  python /opt/video-to-build-plugin/skills/video-blueprint/scripts/extract_video.py \
    --url "https://www.youtube.com/watch?v=dNGtwbfuQZ8" \
    --out /workspace/.video-build/demo \
    --download-video --extract-frames
  ```

---

## Uso en cualquier proyecto nuevo con `agy`

```bash
mkdir mi-proyecto-3d && cd mi-proyecto-3d
agy
```

Pídele al agente:
> *"Usa `video-to-build` (`video-blueprint`, `tool-resolver`, `web3d-builder`) con este tutorial `https://www.youtube.com/watch?v=dNGtwbfuQZ8` y créame una web 3D interactiva para [tu producto/idea]."*

*(Opcional)* Para ejecución remota desde otro dispositivo:
```bash
agy remote-control start
```
