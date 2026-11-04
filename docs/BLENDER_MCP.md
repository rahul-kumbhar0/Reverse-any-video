# Live Blender via MCP (optional, local machine)

[ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) (MIT) lets Claude drive
a running Blender. Use it when you want to art-direct a hero shot interactively; the headless
`blender_kit.py` path stays the default for automated renders.

1. Install (sets up the Blender add-on and your AI app config):
   `curl -LsSf https://www.mcp-for-blender.com/install.sh | sh`
   or add the server manually to Claude Code:
   ```json
   { "mcpServers": { "blender": { "command": "uvx", "args": ["mcp-for-blender"] } } }
   ```
2. In Blender: sidebar → BlenderMCP → Connect.
3. Ask Claude to load `skills/create-video/scripts/blender_kit.py` inside Blender and build the
   scene there; the same helpers (rounded_slab, studio_rig, reflection_strips...) work live.
   Pair with the `blender-*` skills from `scripts/install_tools.sh` (EL4CTEO/blender-skills).
