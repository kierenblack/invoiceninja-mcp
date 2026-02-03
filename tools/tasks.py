import requests
import json
import time
from .config import NINJA_URL, HEADERS


def register_tools(mcp):
    """Register all task-related tools with the MCP server."""

    @mcp.tool()
    def get_tasks(
        client_id: str = None,
        project_id: str = None,
        status: str = "all",
        limit: int = 20
    ) -> str:
        """
        Fetch tasks with optional filters.
        - client_id: Filter by client
        - project_id: Filter by project
        - status: 'all', 'running', or 'invoiced'
        """
        try:
            url = f"{NINJA_URL}/tasks?status=active&per_page={limit}&include=client,project"

            if client_id:
                url += f"&client_id={client_id}"
            if project_id:
                url += f"&project_id={project_id}"

            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            tasks = response.json().get('data', [])

            if not tasks:
                return "No tasks found."

            output = [f"--- Found {len(tasks)} Tasks ---"]
            for t in tasks:
                task_id = t.get('id')
                description = t.get('description', 'No description')[:50]
                client = t.get('client', {}).get('display_name', 'No Client') if t.get('client') else 'No Client'
                project = t.get('project', {}).get('name', 'No Project') if t.get('project') else 'No Project'

                # Calculate total time from time_log
                time_log = t.get('time_log', '[]')
                try:
                    logs = json.loads(time_log) if isinstance(time_log, str) else time_log
                    total_seconds = 0
                    is_running = False
                    for log in logs:
                        start = log[0] if len(log) > 0 else 0
                        end = log[1] if len(log) > 1 and log[1] else 0
                        if end == 0 and start > 0:
                            is_running = True
                            end = int(time.time())
                        if start and end:
                            total_seconds += (end - start)
                    hours = total_seconds / 3600
                except:
                    hours = 0
                    is_running = False

                status_icon = "RUNNING" if is_running else "stopped"
                output.append(f"- [{status_icon}] {description} (ID: {task_id}) | {client} / {project} | {hours:.2f}h")

            return "\n".join(output)
        except Exception as e:
            return f"Error fetching tasks: {str(e)}"

    @mcp.tool()
    def get_task_details(task_id: str) -> str:
        """Get detailed information about a specific task including time logs."""
        try:
            url = f"{NINJA_URL}/tasks/{task_id}?include=client,project"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            t = response.json().get('data', {})

            if not t:
                return f"Task {task_id} not found."

            description = t.get('description', 'No description')
            client = t.get('client', {}).get('display_name', 'No Client') if t.get('client') else 'No Client'
            project = t.get('project', {}).get('name', 'No Project') if t.get('project') else 'No Project'
            rate = t.get('rate', 0)

            # Parse time logs
            time_log = t.get('time_log', '[]')
            try:
                logs = json.loads(time_log) if isinstance(time_log, str) else time_log
                total_seconds = 0
                is_running = False
                log_details = []

                for i, log in enumerate(logs):
                    start = log[0] if len(log) > 0 else 0
                    end = log[1] if len(log) > 1 and log[1] else 0

                    if end == 0 and start > 0:
                        is_running = True
                        end = int(time.time())

                    if start and end:
                        duration = end - start
                        total_seconds += duration
                        hours = duration / 3600
                        log_details.append(f"  Entry {i+1}: {hours:.2f}h")

                hours = total_seconds / 3600
            except:
                hours = 0
                is_running = False
                log_details = []

            status = "RUNNING" if is_running else "Stopped"
            billable = hours * float(rate) if rate else 0

            output = (
                f"Task: {description}\n"
                f"- ID: {task_id}\n"
                f"- Client: {client}\n"
                f"- Project: {project}\n"
                f"- Status: {status}\n"
                f"- Total Time: {hours:.2f}h\n"
                f"- Rate: ${rate}/hr\n"
                f"- Billable Amount: ${billable:.2f}"
            )

            if log_details:
                output += "\n- Time Entries:\n" + "\n".join(log_details)

            return output
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def create_task(
        description: str,
        client_id: str = None,
        project_id: str = None,
        rate: float = 0
    ) -> str:
        """
        Create a new task.
        - description: What the task is about
        - client_id: Associate with a client (optional)
        - project_id: Associate with a project (optional)
        - rate: Hourly rate override (optional)
        """
        try:
            payload = {
                "description": description,
                "time_log": "[]"
            }

            if client_id:
                payload["client_id"] = client_id
            if project_id:
                payload["project_id"] = project_id
            if rate:
                payload["rate"] = rate

            response = requests.post(f"{NINJA_URL}/tasks", headers=HEADERS, json=payload, timeout=10)

            if response.status_code in [200, 201]:
                task = response.json().get('data', {})
                return f"Success! Created task '{description}' (ID: {task.get('id')})"
            else:
                return f"Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Request failed: {str(e)}"

    @mcp.tool()
    def start_task(task_id: str) -> str:
        """Start the timer on a task. Adds a new time entry with current timestamp."""
        try:
            # First get current task to preserve existing time logs
            response = requests.get(f"{NINJA_URL}/tasks/{task_id}", headers=HEADERS)
            response.raise_for_status()
            task = response.json().get('data', {})

            time_log = task.get('time_log', '[]')
            try:
                logs = json.loads(time_log) if isinstance(time_log, str) else time_log
            except:
                logs = []

            # Check if already running
            if logs and len(logs[-1]) == 1:
                return f"Task {task_id} is already running."

            # Add new time entry with start time
            current_time = int(time.time())
            logs.append([current_time])

            # Update task
            payload = {"time_log": json.dumps(logs)}
            response = requests.put(f"{NINJA_URL}/tasks/{task_id}", headers=HEADERS, json=payload, timeout=10)

            if response.status_code == 200:
                return f"Started timer on task {task_id}."
            else:
                return f"Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def stop_task(task_id: str) -> str:
        """Stop the timer on a running task. Completes the current time entry."""
        try:
            # Get current task
            response = requests.get(f"{NINJA_URL}/tasks/{task_id}", headers=HEADERS)
            response.raise_for_status()
            task = response.json().get('data', {})

            time_log = task.get('time_log', '[]')
            try:
                logs = json.loads(time_log) if isinstance(time_log, str) else time_log
            except:
                logs = []

            # Check if running (last entry has only start time)
            if not logs or len(logs[-1]) != 1:
                return f"Task {task_id} is not currently running."

            # Add end time to last entry
            current_time = int(time.time())
            logs[-1].append(current_time)

            # Calculate duration of this session
            start_time = logs[-1][0]
            duration_seconds = current_time - start_time
            duration_hours = duration_seconds / 3600

            # Update task
            payload = {"time_log": json.dumps(logs)}
            response = requests.put(f"{NINJA_URL}/tasks/{task_id}", headers=HEADERS, json=payload, timeout=10)

            if response.status_code == 200:
                return f"Stopped timer on task {task_id}. Session duration: {duration_hours:.2f}h"
            else:
                return f"Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def log_time(
        task_id: str,
        hours: float,
        description: str = ""
    ) -> str:
        """
        Manually log time to a task.
        - task_id: The task to log time to
        - hours: Number of hours to log
        - description: Optional note about what was done
        """
        try:
            # Get current task
            response = requests.get(f"{NINJA_URL}/tasks/{task_id}", headers=HEADERS)
            response.raise_for_status()
            task = response.json().get('data', {})

            time_log = task.get('time_log', '[]')
            try:
                logs = json.loads(time_log) if isinstance(time_log, str) else time_log
            except:
                logs = []

            # Create a time entry for the specified hours (ending now)
            current_time = int(time.time())
            duration_seconds = int(hours * 3600)
            start_time = current_time - duration_seconds

            logs.append([start_time, current_time])

            # Update task
            payload = {"time_log": json.dumps(logs)}
            if description:
                # Append to existing description
                existing_desc = task.get('description', '')
                payload["description"] = f"{existing_desc}\n[{hours}h] {description}".strip()

            response = requests.put(f"{NINJA_URL}/tasks/{task_id}", headers=HEADERS, json=payload, timeout=10)

            if response.status_code == 200:
                return f"Logged {hours}h to task {task_id}."
            else:
                return f"Failed: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def get_billable_hours(
        client_id: str = None,
        project_id: str = None
    ) -> str:
        """
        Get summary of unbilled hours across tasks.
        Optionally filter by client or project.
        """
        try:
            url = f"{NINJA_URL}/tasks?status=active&per_page=100&include=client,project"

            if client_id:
                url += f"&client_id={client_id}"
            if project_id:
                url += f"&project_id={project_id}"

            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            tasks = response.json().get('data', [])

            if not tasks:
                return "No tasks found."

            # Filter for uninvoiced tasks and calculate hours
            total_hours = 0
            total_billable = 0
            task_summaries = []

            for t in tasks:
                # Skip if already invoiced
                if t.get('invoice_id'):
                    continue

                time_log = t.get('time_log', '[]')
                rate = float(t.get('rate', 0))

                try:
                    logs = json.loads(time_log) if isinstance(time_log, str) else time_log
                    task_seconds = 0
                    for log in logs:
                        start = log[0] if len(log) > 0 else 0
                        end = log[1] if len(log) > 1 and log[1] else int(time.time())
                        if start and end:
                            task_seconds += (end - start)
                    task_hours = task_seconds / 3600
                except:
                    task_hours = 0

                if task_hours > 0:
                    total_hours += task_hours
                    billable = task_hours * rate
                    total_billable += billable

                    desc = t.get('description', 'No description')[:30]
                    task_summaries.append(f"- {desc}: {task_hours:.2f}h (${billable:.2f})")

            output = [
                f"--- Unbilled Hours Summary ---",
                f"Total Hours: {total_hours:.2f}h",
                f"Total Billable: ${total_billable:.2f}",
                f"",
                f"Tasks:"
            ]
            output.extend(task_summaries[:10])  # Show top 10

            if len(task_summaries) > 10:
                output.append(f"... and {len(task_summaries) - 10} more tasks")

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"
