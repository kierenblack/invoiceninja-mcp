import requests
from .config import NINJA_URL, HEADERS


def register_tools(mcp):
    """Register all reporting tools with the MCP server."""

    @mcp.tool()
    def get_outstanding_by_client() -> str:
        """
        Get a breakdown of outstanding balances by client.
        Shows who owes you money, ranked by amount.
        """
        try:
            response = requests.get(f"{NINJA_URL}/clients?status=active&per_page=100", headers=HEADERS)
            response.raise_for_status()
            clients = response.json().get('data', [])

            # Filter to clients with outstanding balance
            with_balance = [(c['display_name'], c['id'], float(c.get('balance', 0)))
                           for c in clients if float(c.get('balance', 0)) > 0]

            if not with_balance:
                return "No outstanding balances found."

            # Sort by balance descending
            with_balance.sort(key=lambda x: x[2], reverse=True)

            total_outstanding = sum(b[2] for b in with_balance)

            output = [
                f"--- Outstanding Balances by Client ---",
                f"Total Outstanding: ${total_outstanding:,.2f}",
                f"Clients with Balance: {len(with_balance)}",
                ""
            ]

            for name, client_id, balance in with_balance:
                percent = (balance / total_outstanding * 100) if total_outstanding > 0 else 0
                output.append(f"- {name}: ${balance:,.2f} ({percent:.1f}%)")

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def get_overdue_aging() -> str:
        """
        Get aging report for overdue invoices.
        Shows invoices grouped by how long they've been overdue (30/60/90+ days).
        """
        try:
            from datetime import datetime, timedelta

            url = f"{NINJA_URL}/invoices?status=active&client_status=overdue&per_page=100&include=client"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            invoices = response.json().get('data', [])

            if not invoices:
                return "No overdue invoices found."

            today = datetime.now().date()

            # Categorize by aging
            buckets = {
                '1-30 days': [],
                '31-60 days': [],
                '61-90 days': [],
                '90+ days': []
            }

            for inv in invoices:
                due_date_str = inv.get('due_date', '')
                if not due_date_str:
                    continue

                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    days_overdue = (today - due_date).days

                    if days_overdue <= 0:
                        continue  # Not actually overdue

                    balance = float(inv.get('balance', 0))
                    client = inv.get('client', {}).get('display_name', 'Unknown') if inv.get('client') else 'Unknown'
                    number = inv.get('number', 'N/A')

                    entry = {
                        'number': number,
                        'client': client,
                        'balance': balance,
                        'days': days_overdue
                    }

                    if days_overdue <= 30:
                        buckets['1-30 days'].append(entry)
                    elif days_overdue <= 60:
                        buckets['31-60 days'].append(entry)
                    elif days_overdue <= 90:
                        buckets['61-90 days'].append(entry)
                    else:
                        buckets['90+ days'].append(entry)
                except:
                    continue

            # Build output
            total_overdue = sum(sum(e['balance'] for e in entries) for entries in buckets.values())

            output = [
                f"--- Overdue Aging Report ---",
                f"Total Overdue: ${total_overdue:,.2f}",
                ""
            ]

            for bucket_name, entries in buckets.items():
                if entries:
                    bucket_total = sum(e['balance'] for e in entries)
                    output.append(f"{bucket_name}: ${bucket_total:,.2f} ({len(entries)} invoices)")
                    for e in entries[:5]:  # Show top 5 per bucket
                        output.append(f"  - [{e['number']}] {e['client']}: ${e['balance']:,.2f} ({e['days']} days)")
                    if len(entries) > 5:
                        output.append(f"  ... and {len(entries) - 5} more")
                    output.append("")

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def get_revenue_by_client(
        start_date: str = "",
        end_date: str = "",
        limit: int = 10
    ) -> str:
        """
        Get revenue breakdown by client from payments.
        - start_date: Filter from date (YYYY-MM-DD)
        - end_date: Filter to date (YYYY-MM-DD)
        - limit: Number of top clients to show
        Shows top clients by total paid amount.
        """
        try:
            # Get payments with client info for date filtering
            url = f"{NINJA_URL}/payments?status=active&per_page=500&include=client"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            payments = response.json().get('data', [])

            # Filter by date and aggregate by client
            client_revenue = {}

            for p in payments:
                pay_date = p.get('date', '')

                # Apply date filters
                if start_date and pay_date < start_date:
                    continue
                if end_date and pay_date > end_date:
                    continue

                amount = float(p.get('amount', 0))
                client = p.get('client', {})
                if not client:
                    continue

                client_name = client.get('display_name', 'Unknown')
                client_id = client.get('id', 'unknown')

                if client_id not in client_revenue:
                    client_revenue[client_id] = {'name': client_name, 'total': 0}
                client_revenue[client_id]['total'] += amount

            if not client_revenue:
                return "No revenue recorded in the specified period."

            # Sort by revenue descending
            sorted_clients = sorted(client_revenue.items(), key=lambda x: x[1]['total'], reverse=True)

            total_revenue = sum(c[1]['total'] for c in sorted_clients)

            output = [f"--- Revenue by Client ---"]

            if start_date or end_date:
                date_range = f"{start_date or 'beginning'} to {end_date or 'now'}"
                output.append(f"Date Range: {date_range}")

            output.extend([
                f"Total Revenue: ${total_revenue:,.2f}",
                f"Clients with Revenue: {len(sorted_clients)}",
                "",
                f"Top {min(limit, len(sorted_clients))} Clients:"
            ])

            for client_id, data in sorted_clients[:limit]:
                percent = (data['total'] / total_revenue * 100) if total_revenue > 0 else 0
                output.append(f"- {data['name']}: ${data['total']:,.2f} ({percent:.1f}%)")

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def get_revenue_report(
        start_date: str = "",
        end_date: str = "",
        group_by: str = "client"
    ) -> str:
        """
        Get detailed revenue report with date filtering.
        - start_date: Filter from date (YYYY-MM-DD)
        - end_date: Filter to date (YYYY-MM-DD)
        - group_by: 'client' or 'month'
        """
        try:
            from datetime import datetime

            url = f"{NINJA_URL}/payments?status=active&per_page=500&include=client"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            payments = response.json().get('data', [])

            # Filter by date
            filtered = []
            for p in payments:
                pay_date = p.get('date', '')
                if start_date and pay_date < start_date:
                    continue
                if end_date and pay_date > end_date:
                    continue
                filtered.append(p)

            if not filtered:
                return "No payments found in the specified period."

            total_revenue = sum(float(p.get('amount', 0)) for p in filtered)

            output = [f"--- Revenue Report ---"]

            if start_date or end_date:
                date_range = f"{start_date or 'beginning'} to {end_date or 'now'}"
                output.append(f"Date Range: {date_range}")

            output.extend([
                f"Total Revenue: ${total_revenue:,.2f}",
                f"Number of Payments: {len(filtered)}",
                ""
            ])

            if group_by == "month":
                # Group by month
                by_month = {}
                for p in filtered:
                    pay_date = p.get('date', '')
                    if pay_date:
                        month_key = pay_date[:7]  # YYYY-MM
                        if month_key not in by_month:
                            by_month[month_key] = 0
                        by_month[month_key] += float(p.get('amount', 0))

                output.append("By Month:")
                for month in sorted(by_month.keys(), reverse=True):
                    output.append(f"  {month}: ${by_month[month]:,.2f}")

            else:
                # Group by client
                by_client = {}
                for p in filtered:
                    client = p.get('client', {})
                    client_name = client.get('display_name', 'Unknown') if client else 'Unknown'
                    if client_name not in by_client:
                        by_client[client_name] = 0
                    by_client[client_name] += float(p.get('amount', 0))

                sorted_clients = sorted(by_client.items(), key=lambda x: x[1], reverse=True)

                output.append("By Client:")
                for name, amount in sorted_clients[:15]:
                    percent = (amount / total_revenue * 100) if total_revenue > 0 else 0
                    output.append(f"  {name}: ${amount:,.2f} ({percent:.1f}%)")

                if len(sorted_clients) > 15:
                    output.append(f"  ... and {len(sorted_clients) - 15} more clients")

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def get_profitability_summary() -> str:
        """
        Get a high-level profitability summary.
        Compares total revenue against total expenses.
        """
        try:
            # Get revenue from clients
            clients_resp = requests.get(f"{NINJA_URL}/clients?status=active&per_page=500", headers=HEADERS)
            clients_resp.raise_for_status()
            clients = clients_resp.json().get('data', [])

            total_revenue = sum(float(c.get('paid_to_date', 0)) for c in clients)
            total_outstanding = sum(float(c.get('balance', 0)) for c in clients)

            # Get expenses
            expenses_resp = requests.get(f"{NINJA_URL}/expenses?status=active&per_page=500", headers=HEADERS)
            expenses_resp.raise_for_status()
            expenses = expenses_resp.json().get('data', [])

            total_expenses = sum(float(e.get('amount', 0)) for e in expenses)

            # Calculate profit
            profit = total_revenue - total_expenses
            margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

            output = [
                f"--- Profitability Summary ---",
                f"",
                f"Revenue:",
                f"  Collected: ${total_revenue:,.2f}",
                f"  Outstanding: ${total_outstanding:,.2f}",
                f"  Total Billed: ${(total_revenue + total_outstanding):,.2f}",
                f"",
                f"Expenses:",
                f"  Total: ${total_expenses:,.2f}",
                f"",
                f"Profit (Collected - Expenses):",
                f"  Amount: ${profit:,.2f}",
                f"  Margin: {margin:.1f}%"
            ]

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def get_business_dashboard() -> str:
        """
        Get a comprehensive business dashboard with key metrics.
        Quick snapshot of your freelance business health.
        """
        try:
            # Gather all data
            clients_resp = requests.get(f"{NINJA_URL}/clients?status=active", headers=HEADERS)
            clients_resp.raise_for_status()
            clients = clients_resp.json().get('data', [])

            invoices_resp = requests.get(f"{NINJA_URL}/invoices?status=active&client_status=overdue&per_page=100", headers=HEADERS)
            invoices_resp.raise_for_status()
            overdue_invoices = invoices_resp.json().get('data', [])

            expenses_resp = requests.get(f"{NINJA_URL}/expenses?status=active&per_page=500", headers=HEADERS)
            expenses_resp.raise_for_status()
            expenses = expenses_resp.json().get('data', [])

            projects_resp = requests.get(f"{NINJA_URL}/projects?status=active", headers=HEADERS)
            projects_resp.raise_for_status()
            projects = projects_resp.json().get('data', [])

            tasks_resp = requests.get(f"{NINJA_URL}/tasks?status=active", headers=HEADERS)
            tasks_resp.raise_for_status()
            tasks = tasks_resp.json().get('data', [])

            # Calculate metrics
            total_revenue = sum(float(c.get('paid_to_date', 0)) for c in clients)
            total_outstanding = sum(float(c.get('balance', 0)) for c in clients)
            total_overdue = sum(float(inv.get('balance', 0)) for inv in overdue_invoices)
            total_expenses = sum(float(e.get('amount', 0)) for e in expenses)
            profit = total_revenue - total_expenses

            # Count running tasks
            import json
            running_tasks = 0
            for t in tasks:
                time_log = t.get('time_log', '[]')
                try:
                    logs = json.loads(time_log) if isinstance(time_log, str) else time_log
                    if logs and len(logs[-1]) == 1:
                        running_tasks += 1
                except:
                    pass

            output = [
                f"=== BUSINESS DASHBOARD ===",
                f"",
                f"MONEY",
                f"  Revenue (collected): ${total_revenue:,.2f}",
                f"  Outstanding: ${total_outstanding:,.2f}",
                f"  Overdue: ${total_overdue:,.2f}",
                f"  Expenses: ${total_expenses:,.2f}",
                f"  Profit: ${profit:,.2f}",
                f"",
                f"ACTIVITY",
                f"  Active Clients: {len(clients)}",
                f"  Active Projects: {len(projects)}",
                f"  Open Tasks: {len(tasks)}",
                f"  Running Timers: {running_tasks}",
                f"  Overdue Invoices: {len(overdue_invoices)}",
            ]

            # Add alerts
            alerts = []
            if total_overdue > 0:
                alerts.append(f"  ! ${total_overdue:,.2f} overdue")
            if running_tasks > 0:
                alerts.append(f"  ! {running_tasks} timer(s) running")

            if alerts:
                output.append("")
                output.append("ALERTS")
                output.extend(alerts)

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"
