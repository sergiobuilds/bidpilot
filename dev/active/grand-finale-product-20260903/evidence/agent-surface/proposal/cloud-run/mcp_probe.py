"""MCP Streamable HTTP client transcript: initialize, tools/list, tools/call."""
import asyncio, json, sys
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def main(url: str, tool: str, args: dict) -> None:
    transcript = {"url": url}
    async with streamable_http_client(url) as (read, write, *_):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            transcript["initialize"] = init.model_dump(mode="json", exclude_none=True)
            tools = await session.list_tools()
            transcript["tools/list"] = [t.name for t in tools.tools]
            result = await session.call_tool(tool, args)
            transcript["tools/call"] = {"name": tool, "arguments": args, "result": result.model_dump(mode="json", exclude_none=True)}
    print(json.dumps(transcript, ensure_ascii=False, indent=2))

url, tool = sys.argv[1], sys.argv[2]
args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
asyncio.run(main(url, tool, args))
