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


# ============================================================
# MCP Resources
# ============================================================

@mcp.resource("config://rate_card")
def get_rate_card() -> str:
    """Returns the current hourly rate card for freelance services."""
    return """
=== RATE CARD ===

Standard Hourly Rate: $50/hr

This rate applies to all services including:
- Development
- Consulting
- Project work
- Support

All time is tracked and billed in 15-minute increments.
"""


# ============================================================
# MCP Prompts
# ============================================================

@mcp.prompt()
def daily_briefing() -> str:
    """
    Morning briefing prompt - checks running timers, overdue invoices,
    outstanding balances, unbilled hours, and tasks due soon.
    """
    return """
Please give me my daily business briefing. Check and report on:

1. **Running Timers**: Are there any tasks with timers currently running? (I may have forgotten to stop them)

2. **Overdue Invoices**: List any invoices that are past their due date and still unpaid.

3. **Outstanding Balances**: Show me which clients owe money and how much.

4. **Unbilled Hours**: Summarize any time I've logged that hasn't been invoiced yet.

5. **Active Projects**: Show my current active projects and their status (hours used vs budgeted).

Format this as a clear morning summary I can quickly scan. Highlight anything urgent that needs my attention today.
"""


if __name__ == "__main__":
    mcp.run(transport="sse")
