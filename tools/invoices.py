import requests
from typing import Literal
from .config import NINJA_URL, HEADERS


def register_tools(mcp):
    """Register all invoice-related tools with the MCP server."""

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
            base_url = f"{NINJA_URL}/invoices?status=active&per_page={limit}&include=client"

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
                inv_id = inv.get('id')
                due_date = inv.get('due_date', 'No Due Date')
                balance = inv.get('balance', 0.0)
                status_tag = "PAID" if float(balance) <= 0 else f"Pending: ${balance}"
                output.append(f"[{num}] (ID: {inv_id}) {client} | {status_tag} | Due: {due_date}")

            return "\n".join(output)
        except Exception as e:
            return f"Error fetching invoices: {str(e)}"

    @mcp.tool()
    def get_invoice_summary(invoice_number: str) -> str:
        """Returns the details and payment status for a specific invoice number."""
        try:
            url = f"{NINJA_URL}/invoices?number={invoice_number}&include=client"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json().get('data', [])

            if not data:
                return f"Invoice #{invoice_number} not found."

            inv = data[0]
            client = inv.get('client', {}).get('display_name', 'N/A')
            amount = inv.get('amount', 0.0)
            balance = inv.get('balance', 0.0)
            status = "PAID" if float(balance) <= 0 else "UNPAID"
            due_date = inv.get('due_date', 'N/A')

            return (
                f"Summary for Invoice #{invoice_number}:\n"
                f"- Invoice ID: {inv.get('id')}\n"
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
            if not due_date:
                payload.pop("due_date")

            response = requests.post(f"{NINJA_URL}/invoices", headers=HEADERS, json=payload)
            response.raise_for_status()
            inv = response.json().get('data', {})
            return f"Successfully created Invoice #{inv.get('number')} (ID: {inv.get('id')}) for total ${inv.get('amount')}. Due: {inv.get('due_date')}"
        except Exception as e:
            return f"Failed to create invoice: {str(e)}"

    @mcp.tool()
    def send_reminder(invoice_id: str) -> str:
        """Send an invoice email to the client using the official bulk action route."""
        url = f"{NINJA_URL}/invoices/bulk"

        payload = {
            "email_type": "reminder1",
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
