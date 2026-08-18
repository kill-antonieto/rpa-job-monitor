"""Registro local de ejecuciones para automatizaciones RPA."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

DATABASE = Path("rpa-monitor.db")
VALID_STATUSES = {"success", "warning", "failed"}


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            owner TEXT NOT NULL,
            schedule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL REFERENCES jobs(id),
            status TEXT NOT NULL CHECK(status IN ('success', 'warning', 'failed')),
            duration_seconds INTEGER NOT NULL CHECK(duration_seconds >= 0),
            notes TEXT NOT NULL DEFAULT '',
            executed_at TEXT NOT NULL
        );
        """
    )
    return connection


def add_job(args: argparse.Namespace) -> None:
    with connect() as db:
        try:
            db.execute(
                "INSERT INTO jobs(name, owner, schedule, created_at) VALUES (?, ?, ?, ?)",
                (args.name, args.owner, args.schedule, datetime.now(UTC).isoformat()),
            )
        except sqlite3.IntegrityError:
            raise SystemExit(f"El bot '{args.name}' ya existe.")
    print(f"Bot registrado: {args.name}")


def record_run(args: argparse.Namespace) -> None:
    with connect() as db:
        job = db.execute("SELECT id FROM jobs WHERE name = ?", (args.name,)).fetchone()
        if not job:
            raise SystemExit(f"No existe un bot llamado '{args.name}'. Usa add-job primero.")
        db.execute(
            "INSERT INTO runs(job_id, status, duration_seconds, notes, executed_at) VALUES (?, ?, ?, ?, ?)",
            (job["id"], args.status, args.duration, args.notes, datetime.now(UTC).isoformat()),
        )
    print(f"Ejecución registrada: {args.name} [{args.status}]")


def dashboard(_: argparse.Namespace) -> None:
    since = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    with connect() as db:
        jobs = db.execute(
            """
            SELECT jobs.name, jobs.owner, jobs.schedule,
                   COUNT(runs.id) AS total,
                   COALESCE(SUM(runs.status = 'success'), 0) AS successes,
                   COALESCE(SUM(runs.status = 'failed'), 0) AS failures,
                   COALESCE(ROUND(AVG(runs.duration_seconds), 1), 0) AS avg_seconds,
                   MAX(runs.executed_at) AS last_run
            FROM jobs
            LEFT JOIN runs ON runs.job_id = jobs.id AND runs.executed_at >= ?
            GROUP BY jobs.id
            ORDER BY jobs.name
            """,
            (since,),
        ).fetchall()
    if not jobs:
        print("No hay bots registrados. Añade uno con add-job.")
        return
    print("\nRPA JOB MONITOR · últimos 30 días\n")
    for job in jobs:
        rate = round((job["successes"] / job["total"]) * 100) if job["total"] else 0
        print(f"{job['name']} · {job['owner']}")
        print(f"  Frecuencia: {job['schedule']}")
        print(f"  Ejecuciones: {job['total']} | Éxito: {rate}% | Fallos: {job['failures']} | Promedio: {job['avg_seconds']} s")
        print(f"  Última ejecución: {job['last_run'] or 'sin datos'}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Registra y consulta ejecuciones RPA.")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add-job", help="Registra un bot.")
    add.add_argument("name")
    add.add_argument("--owner", required=True)
    add.add_argument("--schedule", required=True)
    add.set_defaults(handler=add_job)
    record = commands.add_parser("record", help="Registra una ejecución.")
    record.add_argument("name")
    record.add_argument("status", choices=sorted(VALID_STATUSES))
    record.add_argument("--duration", type=int, required=True, help="Duración en segundos.")
    record.add_argument("--notes", default="")
    record.set_defaults(handler=record_run)
    commands.add_parser("dashboard", help="Muestra indicadores de los últimos 30 días.").set_defaults(handler=dashboard)
    return parser


if __name__ == "__main__":
    arguments = build_parser().parse_args()
    arguments.handler(arguments)
