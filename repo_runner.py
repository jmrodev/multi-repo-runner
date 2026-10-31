#!/usr/bin/env python3
"""
Multi-Repo Runner — Herramienta CLI universal para orquestar múltiples repositorios Git locales.
Soporta:
  - Detección automática en directorio actual, subdirectorio 'repos' o ruta personalizada (--path)
  - Tabla visual con Rich: Rama, cambios staged/unstaged, commits pendientes de push/pull
  - Ejecución de comandos concurrentes o secuenciales ('run')
  - Operaciones masivas: pull, push, checkout, branch, stash, fetch
"""
import os
import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def find_git_repos(base_dir="."):
    """Encuentra repositorios Git en el directorio base o en sus subcarpetas inmediatas."""
    base = Path(base_dir).resolve()
    repos = []
    if (base / "repos").is_dir():
        for d in (base / "repos").iterdir():
            if d.is_dir() and (d / ".git").is_dir():
                repos.append(d)
    if not repos:
        for d in base.iterdir():
            if d.is_dir() and (d / ".git").is_dir():
                repos.append(d)
    return sorted(repos)

def get_detailed_status(repo_path):
    """Obtiene rama, staged, unstaged y commits adelantados/atrasados respecto al upstream."""
    try:
        branch = subprocess.check_output(["git", "-C", str(repo_path), "branch", "--show-current"], text=True).strip()
        status_out = subprocess.check_output(["git", "-C", str(repo_path), "status", "-s"], text=True).strip()
        lines = status_out.splitlines() if status_out else []
        staged = sum(1 for l in lines if l[0] in "MADRC")
        unstaged = sum(1 for l in lines if l[1] in "MD?" or l[0] == "?")

        # Comprobar commits por empujar (ahead)
        try:
            ahead_out = subprocess.check_output(
                ["git", "-C", str(repo_path), "rev-list", "@{u}..HEAD", "--count"],
                stderr=subprocess.DEVNULL, text=True
            ).strip()
            ahead = int(ahead_out) if ahead_out else 0
        except Exception:
            ahead = 0

        return branch or "(detached)", staged, unstaged, ahead
    except Exception:
        return "Error", 0, 0, 0

def show_status(base_dir="."):
    repos = find_git_repos(base_dir)
    if not repos:
        console.print("[red]❌ No se encontraron repositorios Git en esta ruta.[/red]")
        return

    table = Table(title="📦 Estado Multi-Repositorio", border_style="cyan")
    table.add_column("Repositorio", style="bold green")
    table.add_column("Rama Actual", style="magenta")
    table.add_column("Staged", justify="center")
    table.add_column("Modificados", justify="center")
    table.add_column("Por Push (Ahead)", justify="center")
    table.add_column("Estado", justify="center")

    for r in repos:
        branch, staged, unstaged, ahead = get_detailed_status(r)
        staged_badge = f"[green]{staged}[/green]" if staged else "-"
        unstaged_badge = f"[yellow]{unstaged}[/yellow]" if unstaged else "-"
        ahead_badge = f"[bold cyan]↑{ahead}[/bold cyan]" if ahead else "-"

        if staged or unstaged:
            icon = "🟡 Pendiente"
        elif ahead:
            icon = "🔵 Por subir"
        else:
            icon = "🟢 Limpio"
        table.add_row(r.name, branch, staged_badge, unstaged_badge, ahead_badge, icon)

    console.print(table)

def run_command_in_all(cmd_args, base_dir="."):
    repos = find_git_repos(base_dir)
    if not repos:
        console.print("[red]❌ No se encontraron repositorios Git.[/red]")
        return
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

def checkout_branch(branch_name, base_dir="."):
    run_command_in_all(["git", "checkout", branch_name], base_dir)

USAGE = """
Uso: repo-all <comando> [args...]

Consultas de Estado:
  status                     Muestra el estado detallado (rama, staged, unstaged, ahead)

Operaciones Git Masivas:
  pull                       Ejecuta 'git pull' en todos los repositorios
  push                       Ejecuta 'git push' en todos los repositorios
  fetch                      Ejecuta 'git fetch' en todos los repositorios
  checkout   <branch>        Cambia de rama en todos los repositorios que la tengan
  stash                      Aplica 'git stash' en todos los repositorios con cambios

Comandos Libres:
  run        "<comando>"     Ejecuta cualquier comando bash en cada repositorio (ej: npm test, eslint)
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
    elif cmd == "push":
        run_command_in_all(["git", "push"])
    elif cmd == "fetch":
        run_command_in_all(["git", "fetch"])
    elif cmd == "stash":
        run_command_in_all(["git", "stash"])
    elif cmd == "checkout" and len(sys.argv) >= 3:
        checkout_branch(sys.argv[2])
    elif cmd == "run" and len(sys.argv) >= 3:
        run_command_in_all(sys.argv[2:])
    else:
        print(USAGE)
