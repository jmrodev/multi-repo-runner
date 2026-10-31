#!/usr/bin/env python3
"""
Multi-Repo Runner — Herramienta CLI para orquestar múltiples repositorios Git locales simultáneamente.
Muestra estados en tablas Rich con ramas, cambios pendientes, pulls, pushes y ejecución de scripts.
"""
import os
import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def find_git_repos(base_dir):
    """Encuentra repositorios Git en el directorio base o en sus subcarpetas inmediatas."""
    base = Path(base_dir).resolve()
    repos = []
    # Si base_dir contiene una carpeta 'repos', buscar ahí prioritariamente
    if (base / "repos").is_dir():
        for d in (base / "repos").iterdir():
            if d.is_dir() and (d / ".git").is_dir():
                repos.append(d)
    else:
        for d in base.iterdir():
            if d.is_dir() and (d / ".git").is_dir():
                repos.append(d)
    return sorted(repos)

def get_git_status(repo_path):
    """Obtiene rama actual y cantidad de archivos modificados."""
    try:
        branch = subprocess.check_output(["git", "-C", str(repo_path), "branch", "--show-current"], text=True).strip()
        status_out = subprocess.check_output(["git", "-C", str(repo_path), "status", "-s"], text=True).strip()
        mod_count = len(status_out.splitlines()) if status_out else 0
        return branch, mod_count
    except Exception:
        return "Error", 0

def show_status(base_dir="."):
    repos = find_git_repos(base_dir)
    if not repos:
        console.print("[red]❌ No se encontraron repositorios Git en esta ruta.[/red]")
        return

    table = Table(title="📦 Estado Multi-Repositorio", border_style="cyan")
    table.add_column("Repositorio", style="bold green")
    table.add_column("Rama Actual", style="magenta")
    table.add_column("Cambios Locales", justify="right")
    table.add_column("Estado", justify="center")

    for r in repos:
        branch, mods = get_git_status(r)
        if mods > 0:
            status_badge = f"[yellow]{mods} modificado(s)[/yellow]"
            icon = "🟡 Pendiente"
        else:
            status_badge = "[green]Limpio[/green]"
            icon = "🟢 OK"
        table.add_row(r.name, branch, status_badge, icon)

    console.print(table)

def run_command_in_all(cmd_args, base_dir="."):
    repos = find_git_repos(base_dir)
    cmd_str = " ".join(cmd_args)
    console.print(f"\n🚀 [bold cyan]Ejecutando en {len(repos)} repos:[/bold cyan] [yellow]{cmd_str}[/yellow]\n")
    for r in repos:
        console.print(f"👉 [bold green]{r.name}[/bold green]...")
        res = subprocess.run(cmd_str, cwd=str(r), shell=True, text=True, capture_output=True)
        if res.stdout.strip():
            print(res.stdout.strip())
        if res.stderr.strip():
            console.print(f"[red]{res.stderr.strip()}[/red]")
        print()

USAGE = """
Uso: repo-all <comando> [args...]

Comandos:
  status                     Muestra el estado de Git de todos los repositorios en una tabla Rich
  run     "<comando bash>"   Ejecuta cualquier comando bash en cada repositorio (ej: git pull, npm test)
  pull                       Ejecuta 'git pull' en todos los repositorios
  fetch                      Ejecuta 'git fetch' en todos los repositorios
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(0)
    cmd = sys.argv[1].lower()
    if cmd == "status":
        show_status()
    elif cmd == "pull":
        run_command_in_all(["git", "pull"])
    elif cmd == "fetch":
        run_command_in_all(["git", "fetch"])
    elif cmd == "run" and len(sys.argv) >= 3:
        run_command_in_all(sys.argv[2:])
    else:
        print(USAGE)
