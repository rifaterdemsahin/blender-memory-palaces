# Blender Director (free)

One-line idea in, a 10-second grey Blender clip with a real camera move out. Then Google Flow's free daily credits turn it into a cinematic shot. Total cost: $0.

What's inside:
- `SKILL.md`: the skill your AI agent follows (works in OpenCode and Claude Code).
- `scripts/director.py`: the helper it runs inside Blender (clay scene, 5 camera moves, MP4 output).
- `flow-prompts.md`: 10 Flow prompt templates.
- `credit-planner.md`: how to spend the 50 free credits a day.

## Setup (once, about 10 minutes)
1. **Blender** (free): download from blender.org and open it once.
2. **uv** (runs the Blender connector):
   - Mac: `brew install uv` (or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
3. **OpenCode** (free AI agent in your terminal): see opencode.ai for the install command, e.g. `brew install opencode` or `npm i -g opencode-ai`.
4. **The Blender connector** (MCP for Blender, formerly blender-mcp):
   `uvx mcp-for-blender setup`
   It puts the add-on into Blender and adds the connector to the AI apps it finds, OpenCode included.
   Doing it by hand instead: `uvx mcp-for-blender install-addon`, then add this to `opencode.json` in your project folder:
   ```json
   { "mcp": { "blender": { "type": "local", "command": ["uvx", "mcp-for-blender"], "enabled": true } } }
   ```
5. In Blender: Edit > Preferences > Add-ons, turn on **MCP for Blender**. Press N in the 3D view, open the **MCP for Blender** tab and make sure the server is running.
6. **This skill:** copy the `blender-director` folder into `~/.config/opencode/skills/` (or `.opencode/skills/` inside your project). Claude Code users: `~/.claude/skills/`.
7. Start OpenCode in your project folder (`opencode`), type `/models` and pick a free model (we used **DeepSeek V4.1 Flash Free**). Free models change over time; pick any one marked Free.

## Use it
In OpenCode:
> Use the blender-director skill: a sports car racing through a desert at sunset, chase shot.

When it asks permission to use Blender, allow it and pick the "always" option. It builds, looks at the result through the camera, fixes things, and saves `shot.blend`. Render the clip with Ctrl+F12 in Blender, or the terminal line it gives you.

## In Flow (free)
1. Go to Google Flow (labs.google/flow) and sign in with a Google account. Free accounts get 50 credits a day.
2. Upload `shot_clay.mp4` (3 to 10 seconds).
3. Choose **Omni Flash** and paste a prompt from `flow-prompts.md`.
4. Make a **360p** test first (about 10 credits for 10 s). If the camera move and look are right, make the **720p** version (about 30 credits).
5. Download.

Good to know:
- Free accounts can be blocked from making video during busy hours (roughly 13:00 to 16:00 UTC).
- Google adds an invisible SynthID watermark to every AI video.
