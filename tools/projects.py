import requests
from .config import NINJA_URL, HEADERS


def register_tools(mcp):
    """Register all project-related tools with the MCP server."""

    @mcp.tool()
    def get_projects(
        client_id: str = None,
        include_archived: bool = False,
        limit: int = 20
    ) -> str:
        """
        Fetch projects, optionally filtered by client.
        - client_id: Filter by client
        - include_archived: If True, includes archived/deleted projects (default: False, only active)
        - limit: Number of projects to return
        Returns project name, client, budgeted hours, and current hours logged.
        """
        try:
            entity_status = "active" if not include_archived else "active,archived,deleted"
            url = f"{NINJA_URL}/projects?status={entity_status}&per_page={limit}&include=client"
            if client_id:
                url += f"&client_id={client_id}"

            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            projects = response.json().get('data', [])

            if not projects:
                return "No projects found."

            output = [f"--- Found {len(projects)} Projects ---"]
            for p in projects:
                name = p.get('name', 'Unnamed')
                proj_id = p.get('id')
                client = p.get('client', {}).get('display_name', 'No Client')
                budgeted = p.get('budgeted_hours', 0)
                logged = p.get('current_hours', 0)
                due_date = p.get('due_date', 'No due date')

                budget_str = f"{logged}/{budgeted}h" if budgeted else f"{logged}h logged"
                output.append(f"- {name} (ID: {proj_id}) | Client: {client} | Hours: {budget_str} | Due: {due_date}")

            return "\n".join(output)
        except Exception as e:
            return f"Error fetching projects: {str(e)}"

    @mcp.tool()
    def get_project_details(project_id: str) -> str:
        """Get detailed information about a specific project including tasks and budget status."""
        try:
            url = f"{NINJA_URL}/projects/{project_id}?include=client"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            p = response.json().get('data', {})

            if not p:
                return f"Project {project_id} not found."

            name = p.get('name', 'Unnamed')
            client = p.get('client', {}).get('display_name', 'No Client')
            budgeted = float(p.get('budgeted_hours', 0))
            logged = float(p.get('current_hours', 0))
            due_date = p.get('due_date', 'No due date')
            task_rate = p.get('task_rate', 0)
            notes = p.get('public_notes', '') or p.get('private_notes', '') or 'None'

            # Calculate budget usage
            if budgeted > 0:
                percent_used = (logged / budgeted) * 100
                budget_status = f"{logged:.1f}/{budgeted:.1f}h ({percent_used:.0f}% used)"
            else:
                budget_status = f"{logged:.1f}h logged (no budget set)"

            return (
                f"Project: {name}\n"
                f"- ID: {project_id}\n"
                f"- Client: {client}\n"
                f"- Hours: {budget_status}\n"
                f"- Task Rate: ${task_rate}/hr\n"
                f"- Due Date: {due_date}\n"
                f"- Notes: {notes[:100]}"
            )
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def create_project(
        client_id: str,
        name: str,
        budgeted_hours: float = 0,
        task_rate: float = 0,
        due_date: str = "",
        notes: str = ""
    ) -> str:
        """
        Create a new project for a client.
        - client_id: The client's hashed ID
        - name: Project name
        - budgeted_hours: Estimated hours for the project
        - task_rate: Hourly rate for tasks (overrides default)
        - due_date: YYYY-MM-DD format
        - notes: Project description/notes
        """
        try:
            payload = {
                "client_id": client_id,
                "name": name,
                "budgeted_hours": budgeted_hours,
                "task_rate": task_rate,
                "public_notes": notes
            }
            if due_date:
                payload["due_date"] = due_date

            response = requests.post(f"{NINJA_URL}/projects", headers=HEADERS, json=payload, timeout=10)

            if response.status_code in [200, 201]:
                proj = response.json().get('data', {})
                return f"Success! Created project '{name}' (ID: {proj.get('id')}) for client {client_id}."
            else:
                return f"Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Request failed: {str(e)}"

    @mcp.tool()
    def update_project(
        project_id: str,
        name: str = None,
        budgeted_hours: float = None,
        task_rate: float = None,
        due_date: str = None,
        notes: str = None
    ) -> str:
        """Update an existing project's details."""
        try:
            # Build payload with only provided fields
            payload = {}
            if name is not None:
                payload["name"] = name
            if budgeted_hours is not None:
                payload["budgeted_hours"] = budgeted_hours
            if task_rate is not None:
                payload["task_rate"] = task_rate
            if due_date is not None:
                payload["due_date"] = due_date
            if notes is not None:
                payload["public_notes"] = notes

            if not payload:
                return "No fields provided to update."

            response = requests.put(f"{NINJA_URL}/projects/{project_id}", headers=HEADERS, json=payload, timeout=10)

            if response.status_code == 200:
                return f"Successfully updated project {project_id}."
            else:
                return f"Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Request failed: {str(e)}"

    @mcp.tool()
    def get_project_summary(project_id: str) -> str:
        """
        Get a comprehensive summary of a project including:
        - Hours logged vs budgeted
        - Task breakdown with time per task
        - Billable amount calculation
        """
        try:
            import json

            # Get project details
            proj_resp = requests.get(f"{NINJA_URL}/projects/{project_id}?include=client", headers=HEADERS)
            proj_resp.raise_for_status()
            p = proj_resp.json().get('data', {})

            if not p:
                return f"Project {project_id} not found."

            name = p.get('name', 'Unnamed')
            client = p.get('client', {}).get('display_name', 'No Client')
            budgeted = float(p.get('budgeted_hours', 0))
            task_rate = float(p.get('task_rate', 0))

            # Get tasks for this project
            tasks_resp = requests.get(f"{NINJA_URL}/tasks?project_id={project_id}&status=active&per_page=100", headers=HEADERS)
            tasks_resp.raise_for_status()
            tasks = tasks_resp.json().get('data', [])

            # Calculate hours per task
            total_hours = 0
            task_breakdown = []
            running_tasks = 0

            for t in tasks:
                desc = t.get('description', 'No description')[:40]
                task_id = t.get('id')
                time_log = t.get('time_log', '[]')
                rate = float(t.get('rate', 0)) or task_rate

                try:
                    logs = json.loads(time_log) if isinstance(time_log, str) else time_log
                    task_seconds = 0
                    is_running = False

                    for log in logs:
                        start = log[0] if len(log) > 0 else 0
                        end = log[1] if len(log) > 1 and log[1] else 0
                        if end == 0 and start > 0:
                            is_running = True
                            import time
                            end = int(time.time())
                        if start and end:
                            task_seconds += (end - start)

                    task_hours = task_seconds / 3600
                    total_hours += task_hours

                    if is_running:
                        running_tasks += 1

                    status = " [RUNNING]" if is_running else ""
                    task_breakdown.append(f"  - {desc}{status}: {task_hours:.2f}h (${task_hours * rate:.2f})")
                except:
                    task_breakdown.append(f"  - {desc}: 0h")

            # Calculate totals
            total_billable = total_hours * task_rate
            if budgeted > 0:
                percent_used = (total_hours / budgeted) * 100
                remaining = budgeted - total_hours
                budget_status = f"{total_hours:.2f}/{budgeted:.0f}h ({percent_used:.0f}% used, {remaining:.2f}h remaining)"
            else:
                budget_status = f"{total_hours:.2f}h logged (no budget set)"

            output = [
                f"=== PROJECT SUMMARY: {name} ===",
                f"",
                f"Client: {client}",
                f"Task Rate: ${task_rate}/hr",
                f"",
                f"HOURS",
                f"  {budget_status}",
                f"",
                f"BILLABLE",
                f"  Total: ${total_billable:.2f}",
                f"",
                f"TASKS ({len(tasks)} total, {running_tasks} running)"
            ]

            if task_breakdown:
                output.extend(task_breakdown[:15])
                if len(task_breakdown) > 15:
                    output.append(f"  ... and {len(task_breakdown) - 15} more tasks")
            else:
                output.append("  No tasks yet")

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"
