import requests
from .config import NINJA_URL, HEADERS


def register_tools(mcp):
    """Register all system-related tools with the MCP server."""

    @mcp.tool()
    def get_system_summary() -> str:
        """Get a high-level summary of total outstanding balances from the client list."""
        try:
            response = requests.get(f"{NINJA_URL}/clients?status=active", headers=HEADERS)
            response.raise_for_status()
            clients = response.json().get('data', [])

            total_outstanding = sum(float(c.get('balance', 0)) for c in clients)
            total_revenue = sum(float(c.get('paid_to_date', 0)) for c in clients)

            return (
                f"Financial Snapshot:\n"
                f"- Active Clients: {len(clients)}\n"
                f"- Total Outstanding: ${total_outstanding:,.2f}\n"
                f"- Total Revenue: ${total_revenue:,.2f}"
            )
        except Exception as e:
            return f"Could not calculate summary: {str(e)}"

    @mcp.tool()
    def ping() -> str:
        """Simple health check to verify connectivity to Invoice Ninja."""
        try:
            response = requests.get(f"{NINJA_URL}/ping", headers=HEADERS)
            if response.status_code == 200:
                return "Successfully connected to Invoice Ninja!"
            else:
                return f"Failed to connect. Status Code: {response.status_code}"
        except Exception as e:
            return f"Connection error: {str(e)}"
