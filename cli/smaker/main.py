"""
Software Maker CLI - Command line interface for the Software Maker Platform.
"""
import typer
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from typing import Optional
import time
import json

app = typer.Typer(
    name="smaker",
    help="Software Maker - AI-powered software generation platform CLI"
)

console = Console()

# Default API base URL
API_BASE = "http://localhost:8000"


def get_api_base() -> str:
    """Get API base URL from config or environment."""
    import os
    return os.getenv("SMAKER_API_URL", API_BASE)


@app.command()
def init(
    prompt: str = typer.Argument(..., help="Description of the software to build"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Project name"),
    user_id: str = typer.Option("cli-user", "--user", "-u", help="User ID"),
):
    """
    Create a new software project from a prompt.
    """
    api_base = get_api_base()

    with console.status("[bold green]Creating project..."):
        try:
            response = requests.post(
                f"{api_base}/projects",
                json={
                    "prompt": prompt,
                    "name": name,
                    "user_id": user_id,
                }
            )
            response.raise_for_status()
            project = response.json()

            console.print("\n[bold green]✓[/bold green] Project created successfully!")
            console.print(f"[bold]Project ID:[/bold] {project['id']}")
            console.print(f"[bold]Name:[/bold] {project['name']}")
            console.print(f"[bold]Status:[/bold] {project['status']}")
            console.print(f"\nUse [bold]smaker status {project['id']}[/bold] to check progress")

        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            raise typer.Exit(1)


@app.command()
def status(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """
    Get the status of a project.
    """
    api_base = get_api_base()

    try:
        response = requests.get(f"{api_base}/projects/{project_id}")
        response.raise_for_status()
        project = response.json()

        # Get stats
        stats_response = requests.get(f"{api_base}/projects/{project_id}/stats")
        stats = stats_response.json() if stats_response.ok else {}

        console.print("\n[bold]Project Status[/bold]")
        console.print(f"ID: {project['id']}")
        console.print(f"Name: {project['name']}")
        console.print(f"Status: [bold]{project['status']}[/bold]")
        console.print(f"Created: {project['created_at']}")

        if stats:
            console.print(f"\n[bold]Progress[/bold]")
            console.print(f"Total Tasks: {stats.get('total_tasks', 0)}")
            console.print(f"Completed: {stats.get('completed_tasks', 0)}")
            console.print(f"Running: {stats.get('running_tasks', 0)}")
            console.print(f"Failed: {stats.get('failed_tasks', 0)}")
            console.print(f"Progress: {stats.get('progress_percentage', 0):.1f}%")

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def list(
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="Filter by user ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of projects to show"),
):
    """
    List all projects.
    """
    api_base = get_api_base()

    try:
        params = {"limit": limit}
        if user_id:
            params["user_id"] = user_id

        response = requests.get(f"{api_base}/projects", params=params)
        response.raise_for_status()
        projects = response.json()

        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return

        # Create table
        table = Table(title="Projects")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Created", style="blue")
        table.add_column("Tasks", justify="right")

        for project in projects:
            table.add_row(
                project["id"][:8] + "...",
                project["name"],
                project["status"],
                project["created_at"][:19],
                f"{project['completed_tasks']}/{project['total_tasks']}"
            )

        console.print(table)

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def logs(
    project_id: str = typer.Argument(..., help="Project ID"),
    limit: int = typer.Option(50, "--limit", "-l", help="Number of log entries"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs in real-time"),
):
    """
    View project logs/events.
    """
    api_base = get_api_base()

    try:
        response = requests.get(
            f"{api_base}/projects/{project_id}/events",
            params={"limit": limit}
        )
        response.raise_for_status()
        events = response.json()

        console.print(f"\n[bold]Project Logs[/bold] ({project_id[:8]}...)\n")

        for event in reversed(events):  # Show oldest first
            timestamp = event["timestamp"][:19]
            level = event["level"].upper()
            message = event["message"]

            level_color = {
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "DEBUG": "blue",
            }.get(level, "white")

            console.print(f"[dim]{timestamp}[/dim] [{level_color}]{level:8}[/{level_color}] {message}")

        if follow:
            console.print("\n[dim]Following logs... (Ctrl+C to stop)[/dim]\n")
            # In production, implement WebSocket connection for real-time logs

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def pause(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """
    Pause a running project.
    """
    api_base = get_api_base()

    try:
        response = requests.post(f"{api_base}/projects/{project_id}/pause")
        response.raise_for_status()
        result = response.json()

        console.print(f"[bold green]✓[/bold green] {result['message']}")

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def resume(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """
    Resume a paused project.
    """
    api_base = get_api_base()

    try:
        response = requests.post(f"{api_base}/projects/{project_id}/resume")
        response.raise_for_status()
        result = response.json()

        console.print(f"[bold green]✓[/bold green] {result['message']}")

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def delete(
    project_id: str = typer.Argument(..., help="Project ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    Delete a project.
    """
    api_base = get_api_base()

    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete project {project_id}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    try:
        response = requests.delete(f"{api_base}/projects/{project_id}")
        response.raise_for_status()

        console.print("[bold green]✓[/bold green] Project deleted successfully")

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def timeline(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """
    View project timeline and milestones.
    """
    api_base = get_api_base()

    try:
        response = requests.get(f"{api_base}/projects/{project_id}/timeline")
        response.raise_for_status()
        timeline = response.json()

        project = timeline.get("project", {})
        milestones = timeline.get("milestones", [])

        console.print(f"\n[bold]Project Timeline[/bold] - {project.get('name')}\n")

        for milestone in milestones:
            console.print(f"[green]●[/green] {milestone['name']}")
            console.print(f"   [dim]{milestone['timestamp']}[/dim]\n")

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def config():
    """
    View system configuration.
    """
    api_base = get_api_base()

    try:
        response = requests.get(f"{api_base}/config")
        response.raise_for_status()
        config = response.json()

        console.print("\n[bold]System Configuration[/bold]\n")
        console.print(f"LLM Mode: {config['llm_mode']}")
        console.print("\n[bold]Providers:[/bold]")

        for name, provider in config['providers'].items():
            status = "[green]enabled[/green]" if provider['enabled'] else "[red]disabled[/red]"
            console.print(f"  {name}: {status} (model: {provider['model']})")

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
