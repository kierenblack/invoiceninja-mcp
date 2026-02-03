import requests
from typing import Optional
from .config import NINJA_URL, HEADERS


def register_tools(mcp):
    """Register all expense-related tools with the MCP server."""

    @mcp.tool()
    def get_expense_categories(limit: int = 50) -> str:
        """Fetch all expense categories."""
        try:
            url = f"{NINJA_URL}/expense_categories?per_page={limit}"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            categories = response.json().get('data', [])

            if not categories:
                return "No expense categories found."

            output = [f"--- Found {len(categories)} Expense Categories ---"]
            for cat in categories:
                cat_id = cat.get('id')
                name = cat.get('name', 'Unnamed')
                output.append(f"- {name} (ID: {cat_id})")

            return "\n".join(output)
        except Exception as e:
            return f"Error fetching expense categories: {str(e)}"

    @mcp.tool()
    def get_expenses(
        client_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
        category_id: Optional[str] = None,
        limit: int = 20
    ) -> str:
        """
        Fetch expenses with optional filters.
        - client_id: Filter by client (for billable expenses)
        - vendor_id: Filter by vendor
        - category_id: Filter by expense category
        """
        try:
            url = f"{NINJA_URL}/expenses?status=active&per_page={limit}&include=client,vendor,category"

            if client_id:
                url += f"&client_id={client_id}"
            if vendor_id:
                url += f"&vendor_id={vendor_id}"
            if category_id:
                url += f"&category_id={category_id}"

            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            expenses = response.json().get('data', [])

            if not expenses:
                return "No expenses found."

            output = [f"--- Found {len(expenses)} Expenses ---"]
            for e in expenses:
                exp_id = e.get('id')
                amount = float(e.get('amount', 0))
                date = e.get('date', 'N/A')
                category = e.get('category', {}).get('name', 'Uncategorized') if e.get('category') else 'Uncategorized'
                vendor = e.get('vendor', {}).get('name', 'No Vendor') if e.get('vendor') else 'No Vendor'
                client = e.get('client', {}).get('display_name', '') if e.get('client') else ''

                client_str = f" | Billable to: {client}" if client else ""
                output.append(f"- ${amount:.2f} | {category} | {vendor} | {date}{client_str} (ID: {exp_id})")

            return "\n".join(output)
        except Exception as e:
            return f"Error fetching expenses: {str(e)}"

    @mcp.tool()
    def get_expense_details(expense_id: str) -> str:
        """Get detailed information about a specific expense."""
        try:
            url = f"{NINJA_URL}/expenses/{expense_id}?include=client,vendor,category"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            e = response.json().get('data', {})

            if not e:
                return f"Expense {expense_id} not found."

            amount = float(e.get('amount', 0))
            date = e.get('date', 'N/A')
            category = e.get('category', {}).get('name', 'Uncategorized') if e.get('category') else 'Uncategorized'
            vendor = e.get('vendor', {}).get('name', 'No Vendor') if e.get('vendor') else 'No Vendor'
            client = e.get('client', {}).get('display_name', 'Not billable') if e.get('client') else 'Not billable'
            public_notes = e.get('public_notes', 'None') or 'None'
            private_notes = e.get('private_notes', 'None') or 'None'
            is_billable = 'Yes' if e.get('should_be_invoiced') else 'No'
            is_invoiced = 'Yes' if e.get('invoice_id') else 'No'

            return (
                f"Expense Details:\n"
                f"- ID: {expense_id}\n"
                f"- Amount: ${amount:.2f}\n"
                f"- Date: {date}\n"
                f"- Category: {category}\n"
                f"- Vendor: {vendor}\n"
                f"- Client: {client}\n"
                f"- Billable: {is_billable}\n"
                f"- Invoiced: {is_invoiced}\n"
                f"- Notes: {public_notes[:100]}"
            )
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def create_expense(
        amount: float,
        date: str,
        category_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
        client_id: Optional[str] = None,
        public_notes: str = "",
        private_notes: str = "",
        should_be_invoiced: bool = False
    ) -> str:
        """
        Create a new expense.
        - amount: Expense amount
        - date: Expense date (YYYY-MM-DD)
        - category_id: Expense category ID
        - vendor_id: Vendor ID (who you paid)
        - client_id: Client ID (if billable to a client)
        - public_notes: Description visible on invoices
        - private_notes: Internal notes
        - should_be_invoiced: Mark as billable to client
        """
        try:
            payload = {
                "amount": amount,
                "date": date,
                "should_be_invoiced": should_be_invoiced
            }

            if category_id:
                payload["category_id"] = category_id
            if vendor_id:
                payload["vendor_id"] = vendor_id
            if client_id:
                payload["client_id"] = client_id
            if public_notes:
                payload["public_notes"] = public_notes
            if private_notes:
                payload["private_notes"] = private_notes

            response = requests.post(f"{NINJA_URL}/expenses", headers=HEADERS, json=payload, timeout=10)

            if response.status_code in [200, 201]:
                exp = response.json().get('data', {})
                return f"Success! Created expense of ${amount:.2f} (ID: {exp.get('id')}) on {date}."
            else:
                return f"Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Request failed: {str(e)}"

    @mcp.tool()
    def get_expense_summary(
        start_date: str = "",
        end_date: str = ""
    ) -> str:
        """
        Get a summary of expenses grouped by category.
        - start_date: Filter from date (YYYY-MM-DD)
        - end_date: Filter to date (YYYY-MM-DD)
        """
        try:
            url = f"{NINJA_URL}/expenses?status=active&per_page=500&include=category"

            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            expenses = response.json().get('data', [])

            if not expenses:
                return "No expenses found."

            # Filter by date if provided
            filtered = []
            for e in expenses:
                exp_date = e.get('date', '')
                if start_date and exp_date < start_date:
                    continue
                if end_date and exp_date > end_date:
                    continue
                filtered.append(e)

            if not filtered:
                return "No expenses found in the specified date range."

            # Group by category
            by_category = {}
            total = 0

            for e in filtered:
                category = e.get('category', {}).get('name', 'Uncategorized') if e.get('category') else 'Uncategorized'
                amount = float(e.get('amount', 0))

                if category not in by_category:
                    by_category[category] = 0
                by_category[category] += amount
                total += amount

            # Sort by amount descending
            sorted_cats = sorted(by_category.items(), key=lambda x: x[1], reverse=True)

            output = [f"--- Expense Summary ---"]
            if start_date or end_date:
                date_range = f"{start_date or 'beginning'} to {end_date or 'now'}"
                output.append(f"Date Range: {date_range}")

            output.append(f"Total Expenses: ${total:,.2f}")
            output.append(f"Number of Expenses: {len(filtered)}")
            output.append("")
            output.append("By Category:")

            for cat, amt in sorted_cats:
                percent = (amt / total * 100) if total > 0 else 0
                output.append(f"- {cat}: ${amt:,.2f} ({percent:.1f}%)")

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"
