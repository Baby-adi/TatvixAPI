from langchain_mcp_adapters.client import MultiServerMCPClient
from app.settings import settings

class McpClient():
    def __init__(self):
        self.mcp_client = None
        self.tools = None

    async def _init_tools(self):
        """ Method to get mcp client object and pass tools co-routine instance. """
        self.mcp_client = MultiServerMCPClient(
            {
                #Retrieval client
                "retrieval": {
                    "transport": "streamable_http",
                    "url": settings.MCP_SERVER, #http endpoint of mcp server.
                }
            }
        )
        
        self.tools = await self.mcp_client.get_tools()
        return self.tools


