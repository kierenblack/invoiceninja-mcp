# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Python MCP (Model Context Protocol) server** that exposes Invoice Ninja v5 API endpoints as MCP tools. It allows AI systems (Claude, n8n agents, etc.) to manage invoices, clients, projects, tasks, payments, and expenses through the MCP protocol over SSE transport.

- **Framework:** FastMCP 2.14.4 + mcp SDK 1.26.0
- **Python:** 3.12 (local venv), 3.11 (Docker)
- **Modular structure:** Tools organized in `tools/` directory by domain

## Running Locally

```bash
# Activate the virtual environment first
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Environment vars are loaded from .env file, or set manually:
set NINJA_URL=https://your-instance.com/api/v1
set NINJA_TOKEN=your-api-token

# Run the server (SSE on port 8000)
python server.py
```

## Docker Deployment

```bash
docker-compose up              # Starts invoice-mcp (port 8000) + google-search (port 8001)
docker build -t invoice-mcp .  # Build image only
```

Environment variables are loaded from `.env` file (not committed to git).

## Architecture

```
invoiceninja/
├── server.py              # FastMCP init, imports and registers all tools
├── tools/
│   ├── __init__.py
│   ├── config.py          # Shared NINJA_URL, NINJA_TOKEN, HEADERS
│   ├── clients.py         # get_clients, get_client_details, create_client
│   ├── invoices.py        # get_invoices(client_status, include_archived), get_invoice_summary, create_invoice, send_reminder
│   ├── products.py        # get_products
│   ├── system.py          # get_system_summary, ping
│   ├── projects.py        # get_projects(include_archived), get_project_details, create_project, update_project, get_project_summary
│   ├── tasks.py           # get_tasks(include_archived), get_task_details, create_task, start_task, stop_task, log_time, get_billable_hours
│   ├── payments.py        # get_payments, get_payment_details, record_payment, apply_payment_to_invoice
│   ├── expenses.py        # get_expenses, get_expense_details, create_expense, get_expense_categories, get_expense_summary
│   ├── reports.py         # get_outstanding_by_client, get_overdue_aging, get_revenue_by_client(date filter), get_revenue_report(date filter), get_profitability_summary, get_business_dashboard
│   └── documents.py       # get_documents, get_document_details, search_documents
├── Dockerfile
├── docker-compose.yml
├── .env                   # API tokens (gitignored)
└── .gitignore
```

Each tool module exports a `register_tools(mcp)` function that registers its tools with the FastMCP server.

## Adding New Tools

1. Create or edit a file in `tools/` (e.g., `tools/vendors.py`)
2. Import config: `from .config import NINJA_URL, HEADERS`
3. Define `register_tools(mcp)` function with `@mcp.tool()` decorated functions inside
4. Import and register in `server.py`: `from tools import vendors` then `vendors.register_tools(mcp)`

## Invoice Ninja API Conventions

- `status` param filters by entity state: `active`, `archived`, `deleted` (comma-separated)
- `client_status` param filters invoices by payment state: `paid`, `unpaid`, `overdue`
- `include=client,project` embeds related data in responses
- Bulk actions use `POST /{entity}/bulk`
- All API calls use `X-Api-Token` header authentication
- All entity IDs are hashed strings (not integers)

## Default Behavior

- All list tools default to showing only **active** records (not archived/deleted)
- Use `include_archived=True` parameter to include archived/deleted records
- Clients module always shows only active clients (no archive option)

## Task Time Tracking

Tasks store time in `time_log` as JSON: `[[start1, end1], [start2, end2], [start3]]`
- Each entry is `[start_timestamp, end_timestamp]`
- Running timer has only start: `[start_timestamp]`
- Timestamps are Unix epoch seconds

## docker-compose Services

- **invoice-mcp** — This MCP server (port 8000)
- **google-search** — Brave Search MCP server via supergateway SSE wrapper (port 8001)

## No Tests

There are currently no tests, test framework, or CI/CD configuration.
