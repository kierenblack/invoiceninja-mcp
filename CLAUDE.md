# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Python MCP (Model Context Protocol) server** that exposes Invoice Ninja v5 API endpoints as MCP tools. It allows AI systems (Claude, n8n agents, etc.) to manage invoices, clients, and products through the MCP protocol over SSE transport.

- **Framework:** FastMCP 2.14.4 + mcp SDK 1.26.0
- **Python:** 3.12 (local venv), 3.11 (Docker)
- **Single-file server:** All logic lives in `server.py` (~307 lines)

## Running Locally

```bash
# Activate the virtual environment first
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Set required env vars
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

## Architecture

The server is a single `server.py` file with this structure:

1. **FastMCP initialization** — Creates server "InvoiceNinja-Production" on `0.0.0.0:8000` with SSE transport
2. **Config** — `NINJA_URL` and `NINJA_TOKEN` from environment variables, shared `HEADERS` dict
3. **11 `@mcp.tool()` functions** — Each wraps an Invoice Ninja v5 REST API call:
   - Invoices: `get_invoices`, `get_invoice_summary`, `create_invoice`, `send_reminder`
   - Clients: `get_clients`, `get_client_details`, `create_client`
   - Products: `get_products`
   - System: `get_system_summary`, `ping`, `help`

All tools return plain strings. Errors are caught and returned as formatted error messages (not raised).

## Invoice Ninja API Conventions

- `status=active` query param excludes deleted/archived records
- `client_status` param filters by payment state (paid/unpaid/overdue)
- `include=client` embeds client data in invoice responses
- Bulk actions (e.g., send_reminder) use `POST /invoices/bulk`
- All API calls use `X-Api-Token` header authentication

## docker-compose Services

- **invoice-mcp** — This MCP server (port 8000)
- **google-search** — Brave Search MCP server via supergateway SSE wrapper (port 8001)

## No Tests

There are currently no tests, test framework, or CI/CD configuration.
