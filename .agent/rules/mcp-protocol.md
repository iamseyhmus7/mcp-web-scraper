# MCP Protocol Configuration
- Server communicates over stdio following JSON-RPC 2.0.
- All 7 tools must be implemented accurately and strictly document their types according to FastMCP specification.
- Long-running async processes like Queue Workers and Watched pollings persist using `asyncio` Task lifecycles locally instead of locking up the stdio tool replies.
