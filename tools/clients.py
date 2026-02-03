import requests
from typing import Optional
from .config import NINJA_URL, HEADERS


def register_tools(mcp):
    """Register all client-related tools with the MCP server."""

    @mcp.tool()
    def get_clients(limit: int = 10) -> str:
        """Fetch a list of clients with their balances."""
        try:
            url = f"{NINJA_URL}/clients?per_page={limit}&status=active"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            clients = response.json().get('data', [])

            if not clients:
                return "No clients found."

            output = [f"--- Found {len(clients)} Clients ---"]
            for c in clients:
                output.append(f"- {c['display_name']} (ID: {c['id']}) | Balance: ${c['balance']}")

            return "\n".join(output)
        except Exception as e:
            return f"Error fetching clients: {str(e)}"

    @mcp.tool()
    def get_client_details(client_name: str) -> str:
        """Search for a specific client and return their balance and contact info."""
        try:
            url = f"{NINJA_URL}/clients?name={client_name}&status=active"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            clients = response.json().get('data', [])

            if not clients:
                return f"No client found matching '{client_name}'."

            c = clients[0]
            return (f"Client: {c['display_name']}\n"
                    f"ID: {c['id']}\n"
                    f"Current Balance: ${c['balance']}\n"
                    f"Total Paid to Date: ${c['paid_to_date']}")
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def create_client(
        name: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        address1: Optional[str] = None,
        city: Optional[str] = None,
        postal_code: Optional[str] = None
    ) -> str:
        """Create a new client with full company and contact details."""
        url = f"{NINJA_URL}/clients"

        # Contact info (The Person)
        contact = {}
        if email: contact["email"] = email
        if first_name: contact["first_name"] = first_name
        if last_name: contact["last_name"] = last_name
        if phone: contact["phone"] = phone

        # Client info (The Company)
        payload = {
            "name": name,
            "website": website,
            "phone": phone,
            "address1": address1,
            "city": city,
            "postal_code": postal_code,
            "contacts": [contact] if contact else []
        }

        try:
            response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                client_id = response.json().get('data', {}).get('id')
                return f"Success! Created '{name}' (ID: {client_id}) with full details."
            else:
                return f"Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Request failed: {str(e)}"
