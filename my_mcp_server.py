import asyncio, subprocess, os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

ENV = os.environ.copy()
ENV["MCPORTER_CONFIG"] = os.path.expanduser("~/AgentReachProject/config/mcporter.json")
ENV["GH_CONFIG_DIR"] = os.path.expanduser("~/AgentReachProject/config/gh")
ENV["YT_DLP_CONFIG"] = os.path.expanduser("~/AgentReachProject/config/yt-dlp.conf")

def sh(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=ENV)
        out = (r.stdout or "").strip() or (r.stderr or "").strip()
        return out[:8000] if out else "(empty)"
    except subprocess.TimeoutExpired:
        return "ERROR: timeout"
    except Exception as e:
        return f"ERROR: {e}"

server = Server("agent-reach-tools")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="read",
             description="Fetch any web page or RSS/Atom feed as clean text/markdown via Jina Reader. Works for RSS feeds and regular pages.",
             inputSchema={"type": "object", "properties": {"url": {"type": "string", "description": "URL of page or RSS feed"}}, "required": ["url"]}),
        Tool(name="transcribe",
             description="Transcribe YouTube video or local audio file (Whisper via Groq/OpenAI).",
             inputSchema={"type": "object", "properties": {"url": {"type": "string", "description": "YouTube URL or local audio file path"}}, "required": ["url"]}),
        Tool(name="status",
             description="Get Agent Reach status: which channels are installed and active.",
             inputSchema={"type": "object", "properties": {}}),
    ]

@server.call_tool()
async def call_tool(name, arguments):
    if name == "read":
        url = arguments["url"]
        out = sh(f'curl -sL "https://r.jina.ai/{url}"')
    elif name == "transcribe":
        out = sh(f'agent-reach transcribe "{arguments["url"]}"')
    elif name == "status":
        out = sh('agent-reach doctor')
    else:
        out = f"Unknown tool: {name}"
    return [TextContent(type="text", text=out)]

async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

asyncio.run(main())
