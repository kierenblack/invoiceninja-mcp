# Invoice Ninja MCP Server

A Model Context Protocol (MCP) server that exposes Invoice Ninja v5 API endpoints as tools for AI agents. Built for freelancers who want to manage their invoicing, time tracking, and business finances through conversational AI.

## Features

**36 MCP tools** organized across 10 domains:

| Domain | Tools | Description |
|--------|-------|-------------|
| **Clients** | 3 | Create, list, and get client details |
| **Invoices** | 4 | Create invoices, check status, send reminders |
| **Products** | 1 | List available products/services |
| **Projects** | 5 | Manage projects with budgets and track progress |
| **Tasks** | 7 | Time tracking with start/stop timers, manual logging |
| **Payments** | 4 | Record payments, apply to invoices |
| **Expenses** | 5 | Track expenses by category and vendor |
| **Documents** | 3 | View attached documents (read-only) |
| **Reports** | 7 | Revenue reports, aging, profitability, dashboard |
| **System** | 2 | Health check and connectivity |

## Quick Start

### Prerequisites

- Python 3.11+
- Invoice Ninja v5 instance (self-hosted or hosted)
- API token from Invoice Ninja (Settings → Account Management → API Tokens)

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/invoiceninja-mcp.git
cd invoiceninja-mcp

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install mcp[server] fastmcp requests

# Configure environment
cp .env.example .env
# Edit .env with your Invoice Ninja credentials

# Run the server
python server.py
```

### Docker

```bash
# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run with Docker Compose
docker-compose up -d
```

The server runs on `http://localhost:8000` using SSE transport.

## Configuration

Create a `.env` file with your Invoice Ninja credentials:

```env
NINJA_URL=https://your-instance.com/api/v1
NINJA_TOKEN=your-api-token-here
```

## Architecture

```
invoiceninja-mcp/
├── server.py              # FastMCP server initialization
├── tools/
│   ├── config.py          # Shared API configuration
│   ├── clients.py         # Client management
│   ├── invoices.py        # Invoice operations
│   ├── products.py        # Product catalog
│   ├── projects.py        # Project management
│   ├── tasks.py           # Time tracking
│   ├── payments.py        # Payment recording
│   ├── expenses.py        # Expense tracking
│   ├── documents.py       # Document viewing
│   ├── reports.py         # Business reports
│   └── system.py          # Health checks
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Tool Highlights

### Time Tracking
```
start_task(task_id)     → Start timer
stop_task(task_id)      → Stop timer, shows duration
log_time(task_id, 2.5)  → Manually log 2.5 hours
get_billable_hours()    → Summary of unbilled time
```

### Project Management
```
create_project(client_id, "Website Redesign", budgeted_hours=40)
get_project_summary(project_id)  → Hours vs budget, task breakdown
```

### Business Dashboard
```
get_business_dashboard()  → Quick snapshot:
  - Revenue, outstanding, overdue amounts
  - Active clients, projects, tasks
  - Running timers alert
  - Overdue invoices alert
```

### Revenue Reports
```
get_revenue_report(start_date="2024-01-01", group_by="month")
get_revenue_by_client(start_date="2024-01-01", limit=10)
get_overdue_aging()  → 30/60/90+ day buckets
```

## Integration Examples

### n8n AI Agent

Connect to the MCP server in n8n using the MCP Client node with SSE transport:
- URL: `http://localhost:8000/sse`

### Claude Desktop

Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "invoice-ninja": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "NINJA_URL": "https://your-instance.com/api/v1",
        "NINJA_TOKEN": "your-token"
      }
    }
  }
}
```

## Tech Stack

- **[FastMCP](https://github.com/jlowin/fastmcp)** - Pythonic MCP server framework
- **[MCP SDK](https://github.com/modelcontextprotocol/python-sdk)** - Model Context Protocol implementation
- **[Invoice Ninja v5 API](https://api-docs.invoicing.co/)** - Invoicing backend

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Invoice Ninja](https://invoiceninja.com/) for the excellent open-source invoicing platform
- [Anthropic](https://anthropic.com/) for the Model Context Protocol specification
