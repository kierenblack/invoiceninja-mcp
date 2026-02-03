import os
from mcp.server.fastmcp import FastMCP
import requests
from typing import Literal

# 1. Initialize the Server
mcp = FastMCP(
    "InvoiceNinja-Production",
    host="0.0.0.0", 
    port=8000
)

# 2. Setup your VPS Credentials
NINJA_URL = os.getenv("NINJA_URL")
NINJA_TOKEN = os.getenv("NINJA_TOKEN")

# Standard headers required by Invoice Ninja v5
HEADERS = {
    "X-Api-Token": NINJA_TOKEN,
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json"
}

@mcp.tool()
def get_invoices(
    status: Literal["paid", "unpaid", "overdue", "all"] = "all",
    limit: int = 10
) -> str:
    """
    Fetch invoices filtered by payment status. 
    Only retrieves 'active' invoices (ignores deleted/archived).
    """
    try:
        # 'status=active' ignores deleted/archived records
        base_url = f"{NINJA_URL}/invoices?status=active&per_page={limit}&include=client"
        
        # 'client_status' is the specific Ninja v5 filter for payment states
        if status != "all":
            base_url += f"&client_status={status}"
            
        response = requests.get(base_url, headers=HEADERS)
        response.raise_for_status()
        invoices = response.json().get('data', [])
        
        if not invoices:
            return f"No {status} invoices found."
            
        output = [f"--- Found {len(invoices)} {status} invoices ---"]
        for inv in invoices:
            client = inv.get('client', {}).get('display_name', 'N/A')
            num = inv.get('number')
            due_date = inv.get('due_date', 'No Due Date')
            balance = inv.get('balance', 0.0)
            # Add a visual indicator if it's fully paid
            status_tag = "✅ PAID" if float(balance) <= 0 else f"Pending: ${balance}"
            output.append(f"[{num}] {client} | {status_tag} | Due: {due_date}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching invoices: {str(e)}"

@mcp.tool()
def get_client_details(client_name: str) -> str:
    """Search for a specific client and return their balance and contact info."""
    try:
        url = f"{NINJA_URL}/clients?name={client_name}"
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
    email: str = None,
    first_name: str = None,
    last_name: str = None,
    phone: str = None,
    website: str = None,
    address1: str = None,
    city: str = None,
    postal_code: str = None
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
        
@mcp.tool()
def get_clients(limit: int = 10) -> str:
    """Fetch a list of clients with their balances."""
    try:
        url = f"{NINJA_URL}/clients?per_page={limit}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        clients = response.json().get('data', [])
        
        if not clients:
            return "No clients found."
        
        output = [f"--- Found {len(clients)} Clients ---"]
        for c in clients:
            output.append(f"- {c['display_name']} | Balance: ${c['balance']}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching clients: {str(e)}"

@mcp.tool()
def get_system_summary() -> str:
    """Get a high-level summary of total outstanding balances from the client list."""
    try:
        # Instead of the failing /totals, we'll calculate from the clients list
        # This is more reliable across different self-hosted versions
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
def get_invoice_summary(invoice_number: str) -> str:
    """
    Returns the details and payment status for a specific invoice number.
    """
    try:
        # We search specifically for the invoice number provided
        url = f"{NINJA_URL}/invoices?number={invoice_number}&include=client"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json().get('data', [])

        if not data:
            return f"Invoice #{invoice_number} not found."

        # Get the first match
        inv = data[0]
        client = inv.get('client', {}).get('display_name', 'N/A')
        amount = inv.get('amount', 0.0)
        balance = inv.get('balance', 0.0)
        status = "PAID" if float(balance) <= 0 else "UNPAID"
        due_date = inv.get('due_date', 'N/A')

        return (
            f"Summary for Invoice #{invoice_number}:\n"
            f"- Client: {client}\n"
            f"- Total Amount: ${amount}\n"
            f"- Remaining Balance: ${float(balance):,.2f}\n"
            f"- Status: {status}\n"
            f"- Due Date: {due_date}"
        )
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def create_invoice(
    client_id: str, 
    line_items: list[dict], 
    due_date: str = ""
) -> str:
    """
    Create a new draft invoice.
    line_items should be a list of dicts: [{"product_key": "Service", "notes": "Work", "cost": 50, "qty": 1}]
    due_date format: YYYY-MM-DD
    """
    try:
        payload = {
            "client_id": client_id,
            "line_items": line_items,
            "due_date": due_date
        }
        # Filter out empty due_date so Ninja uses its default if not provided
        if not due_date:
            payload.pop("due_date")

        response = requests.post(f"{NINJA_URL}/invoices", headers=HEADERS, json=payload)
        response.raise_for_status()
        inv = response.json().get('data', {})
        return f"Successfully created Invoice #{inv.get('number')} for total ${inv.get('amount')}. Due: {inv.get('due_date')}"
    except Exception as e:
        return f"Failed to create invoice: {str(e)}"
    
@mcp.tool()
def get_products() -> str:
    """Fetch and list all products/services available in Invoice Ninja."""
    try:
        response = requests.get(f"{NINJA_URL}/products", headers=HEADERS)
        response.raise_for_status()
        products = response.json().get('data', [])
        
        if not products:
            return "No products/services found."
        
        output = [f"--- Found {len(products)} Products/Services ---"]
        for prod in products:
            id = prod.get('id')
            name = prod.get('product_key', 'N/A')
            price = prod.get('price', 0.0)
            output.append(f"- {id}: {name}: ${price}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching products: {str(e)}"

@mcp.tool()
def send_reminder(invoice_id: str) -> str:
    """Send an invoice email to the client using the official bulk action route."""
    # Your setup prefers the direct route without /api/v1/
    url = f"{NINJA_URL}/invoices/bulk"
    
    payload = {
        "email_type": "reminder1",  # First reminder email
        "action": "send_email",
        "ids": [invoice_id]
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        
        if response.status_code == 200:
            return f"Successfully queued invoice {invoice_id} for emailing."
        else:
            return f"Failed to send email: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Request failed: {str(e)}"
    
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
    
@mcp.tool()
def help() -> str:
    """List available tools and their descriptions."""
    return (
        "Available Tools:\n"
        "- get_invoices(status: paid|unpaid|overdue|all, limit: int): Fetch invoices by status.\n"
        "- get_client_details(client_name: str): Get balance and info for a specific client.\n"
        "- create_client(name: str, email: str, first_name: str, last_name: str, phone: str): Create a new client.\n"
        "- get_clients(limit: int): List clients with their balances.\n"
        "- get_system_summary(): Get a financial snapshot of the system.\n"
        "- get_invoice_summary(invoice_number: str): Get details for a specific invoice.\n"
        "- get_products(): List all products/services in Invoice Ninja.\n"
        "- create_invoice(client_id: str, line_items: list, due_date: str): Create a new draft invoice.\n"
        "- send_reminder(invoice_id: str): Send a reminder email for a specific invoice.\n"
        "- ping(): Check connectivity to Invoice Ninja.\n"
        "- help(): List available tools."
    )


if __name__ == "__main__":
    # Start the server using stdio transport (standard for local dev)
    mcp.run(transport="sse")