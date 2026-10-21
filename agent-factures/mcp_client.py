import logging
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client, create_mcp_http_client

log = logging.getLogger("agent-factures")

ALLOWED_TOOLS = frozenset({"get-customers", "create-contact", "create-organization", "get-billings", "get-billing-by-id"})

def is_allowed(name: str) -> bool:
    return name in ALLOWED_TOOLS


def filter_tools(names):
    return [n for n in names if is_allowed(n)]


def to_anthropic_tools(mcp_tools) -> list[dict]:
    return [
        {"name": t.name, "description": t.description or "", "input_schema": t.input_schema}
        for t in mcp_tools
        if is_allowed(t.name)
    ]


@asynccontextmanager
async def abby_session():
    from config import ABBY_MCP_URL, ABBY_MCP_TOKEN

    http_client = create_mcp_http_client(headers={"Authorization": f"Bearer {ABBY_MCP_TOKEN}"})
    async with http_client:
        async with streamable_http_client(ABBY_MCP_URL, http_client=http_client) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                yield session


async def list_allowed_tools(session) -> list[dict]:
    result = await session.list_tools()
    return to_anthropic_tools(result.tools)


async def call_tool(session, name: str, arguments: dict) -> tuple[str, bool]:
    if not is_allowed(name):
        log.warning("Outil refusé : %s", name)
        return f"Outil non autorisé : {name}", True
    try:
        result = await session.call_tool(name, arguments)
    except Exception as e:
        log.error("Erreur Abby sur %s : %s", name, e)
        return f"Erreur Abby : {e}", True
    text = "\n".join(c.text for c in result.content if getattr(c, "text", None))
    return text or "(réponse vide)", bool(result.is_error)
