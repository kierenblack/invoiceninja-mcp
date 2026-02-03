import requests
from typing import Literal, Optional
from .config import NINJA_URL, HEADERS


def register_tools(mcp):
    """Register all payment-related tools with the MCP server."""

    @mcp.tool()
    def get_payments(
        client_id: Optional[str] = None,
        status: Literal["all", "pending", "completed", "refunded"] = "all",
        limit: int = 20
    ) -> str:
        """
        Fetch payments with optional filters.
        - client_id: Filter by client
        - status: Filter by payment status
        """
        try:
            url = f"{NINJA_URL}/payments?status=active&per_page={limit}&include=client,invoices"

            if client_id:
                url += f"&client_id={client_id}"

            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            payments = response.json().get('data', [])

            if not payments:
                return "No payments found."

            output = [f"--- Found {len(payments)} Payments ---"]
            for p in payments:
                pay_id = p.get('id')
                amount = float(p.get('amount', 0))
                date = p.get('date', 'N/A')
                client = p.get('client', {}).get('display_name', 'Unknown') if p.get('client') else 'Unknown'
                payment_type = p.get('type', {}).get('name', 'Unknown') if p.get('type') else 'Unknown'

                # Get invoice numbers if available
                invoices = p.get('invoices', [])
                invoice_nums = ', '.join([inv.get('number', 'N/A') for inv in invoices[:3]])
                if not invoice_nums:
                    invoice_nums = 'N/A'

                output.append(f"- ${amount:.2f} from {client} (ID: {pay_id}) | Date: {date} | Invoices: {invoice_nums}")

            return "\n".join(output)
        except Exception as e:
            return f"Error fetching payments: {str(e)}"

    @mcp.tool()
    def get_payment_details(payment_id: str) -> str:
        """Get detailed information about a specific payment."""
        try:
            url = f"{NINJA_URL}/payments/{payment_id}?include=client,invoices"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            p = response.json().get('data', {})

            if not p:
                return f"Payment {payment_id} not found."

            amount = float(p.get('amount', 0))
            date = p.get('date', 'N/A')
            client = p.get('client', {}).get('display_name', 'Unknown') if p.get('client') else 'Unknown'
            transaction_ref = p.get('transaction_reference', 'None')
            private_notes = p.get('private_notes', 'None') or 'None'

            # Get applied invoices
            invoices = p.get('invoices', [])
            invoice_lines = []
            for inv in invoices:
                inv_num = inv.get('number', 'N/A')
                inv_amount = float(inv.get('amount', 0))
                invoice_lines.append(f"  - Invoice #{inv_num}: ${inv_amount:.2f}")

            output = (
                f"Payment Details:\n"
                f"- ID: {payment_id}\n"
                f"- Amount: ${amount:.2f}\n"
                f"- Date: {date}\n"
                f"- Client: {client}\n"
                f"- Transaction Ref: {transaction_ref}\n"
                f"- Notes: {private_notes[:100]}"
            )

            if invoice_lines:
                output += "\n- Applied to Invoices:\n" + "\n".join(invoice_lines)

            return output
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def record_payment(
        client_id: str,
        amount: float,
        invoice_ids: list[str] = None,
        date: str = "",
        payment_type: str = "",
        transaction_reference: str = "",
        notes: str = ""
    ) -> str:
        """
        Record a payment from a client.
        - client_id: The client making the payment
        - amount: Payment amount
        - invoice_ids: List of invoice IDs to apply payment to (optional)
        - date: Payment date YYYY-MM-DD (defaults to today)
        - payment_type: e.g., 'Bank Transfer', 'Credit Card', 'Cash'
        - transaction_reference: External reference number
        - notes: Private notes about the payment
        """
        try:
            payload = {
                "client_id": client_id,
                "amount": amount
            }

            if invoice_ids:
                # Format invoices for the API
                payload["invoices"] = [{"invoice_id": inv_id, "amount": amount / len(invoice_ids)} for inv_id in invoice_ids]
            if date:
                payload["date"] = date
            if transaction_reference:
                payload["transaction_reference"] = transaction_reference
            if notes:
                payload["private_notes"] = notes

            response = requests.post(f"{NINJA_URL}/payments", headers=HEADERS, json=payload, timeout=10)

            if response.status_code in [200, 201]:
                pay = response.json().get('data', {})
                return f"Success! Recorded payment of ${amount:.2f} (ID: {pay.get('id')}) from client {client_id}."
            else:
                return f"Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Request failed: {str(e)}"

    @mcp.tool()
    def apply_payment_to_invoice(
        invoice_id: str,
        amount: float,
        date: str = "",
        notes: str = ""
    ) -> str:
        """
        Quick way to record a payment directly against an invoice.
        Automatically uses the invoice's client.
        """
        try:
            # First get the invoice to find the client
            inv_response = requests.get(f"{NINJA_URL}/invoices/{invoice_id}", headers=HEADERS)
            inv_response.raise_for_status()
            invoice = inv_response.json().get('data', {})

            if not invoice:
                return f"Invoice {invoice_id} not found."

            client_id = invoice.get('client_id')
            invoice_balance = float(invoice.get('balance', 0))

            if amount > invoice_balance:
                return f"Warning: Payment amount ${amount:.2f} exceeds invoice balance ${invoice_balance:.2f}. Use record_payment for overpayments."

            payload = {
                "client_id": client_id,
                "amount": amount,
                "invoices": [{"invoice_id": invoice_id, "amount": amount}]
            }

            if date:
                payload["date"] = date
            if notes:
                payload["private_notes"] = notes

            response = requests.post(f"{NINJA_URL}/payments", headers=HEADERS, json=payload, timeout=10)

            if response.status_code in [200, 201]:
                pay = response.json().get('data', {})
                new_balance = invoice_balance - amount
                return f"Success! Applied ${amount:.2f} to invoice {invoice_id}. New balance: ${new_balance:.2f}"
            else:
                return f"Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Request failed: {str(e)}"
