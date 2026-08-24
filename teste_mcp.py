from mcp.server.mcpserver import MCPServer

mcp = MCPServer("teste")

print("Servidor criado!")
print("Tem tool:", hasattr(mcp, "tool"))