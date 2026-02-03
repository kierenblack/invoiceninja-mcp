from mcp.server.fastmcp import FastMCP

# Import tool registration functions from modules
from tools import clients, invoices, products, system, projects, tasks, payments, expenses, reports, documents

# Initialize the Server
mcp = FastMCP(
    "InvoiceNinja-Production",
    host="0.0.0.0",
    port=8000
)

# Register all tools from each module
clients.register_tools(mcp)
invoices.register_tools(mcp)
products.register_tools(mcp)
system.register_tools(mcp)
projects.register_tools(mcp)
tasks.register_tools(mcp)
payments.register_tools(mcp)
expenses.register_tools(mcp)
reports.register_tools(mcp)
documents.register_tools(mcp)


if __name__ == "__main__":
    mcp.run(transport="sse")
