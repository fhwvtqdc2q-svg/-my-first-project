#!/usr/bin/env python3
"""
Run the local safe workflow.

This script generates:
- Daily accounting report
- Daily price list
- Overdue customer payment reminder drafts
- Local audit log entry

It does not connect to the internet, send messages, publish content, print files,
or modify source CSV data.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict


BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
DEFAULT_SAMPLES_DIR = BASE_DIR / "samples"
DEFAULT_TEMPLATES_DIR = BASE_DIR / "templates"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"

# Allow importing sibling scripts when executed directly.
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_daily_report import build_report, parse_date as parse_report_date  # noqa: E402
from generate_price_list import generate_price_list, validate_exchange_rate  # noqa: E402
from generate_payment_reminders import generate_reminders  # noqa: E402


def append_audit_log(output_dir: Path, event: Dict[str, str]) -> Path:
    """Append one local audit event without storing secrets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = output_dir / "audit-log.csv"
    fieldnames = [
        "timestamp",
        "event_type",
        "status",
        "details",
        "source",
    ]
    exists = audit_path.exists()
    with audit_path.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({key: event.get(key, "") for key in fieldnames})
    return audit_path


def run_workflow(
    report_date: date,
    exchange_rate: float,
    overdue_days: int,
    samples_dir: Path,
    templates_dir: Path,
    output_dir: Path,
) -> Dict[str, Path]:
    validate_exchange_rate(exchange_rate)

    results: Dict[str, Path] = {}

    daily_report_path = build_report(
        samples_dir=samples_dir,
        templates_dir=templates_dir,
        output_dir=output_dir,
        report_date=report_date,
    )
    results["daily_report"] = daily_report_path
    append_audit_log(
        output_dir,
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event_type": "daily_report_generated",
            "status": "success",
            "details": str(daily_report_path.relative_to(BASE_DIR)),
            "source": "run_local_workflow.py",
        },
    )

    price_list_path = generate_price_list(
        samples_dir=samples_dir,
        templates_dir=templates_dir,
        output_dir=output_dir,
        report_date=report_date,
        exchange_rate=exchange_rate,
    )
    results["price_list"] = price_list_path
    append_audit_log(
        output_dir,
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event_type": "price_list_generated",
            "status": "success",
            "details": f"{price_list_path.relative_to(BASE_DIR)}; exchange_rate={exchange_rate}",
            "source": "run_local_workflow.py",
        },
    )

    reminders_summary_path = generate_reminders(
        samples_dir=samples_dir,
        templates_dir=templates_dir,
        output_dir=output_dir,
        report_date=report_date,
        overdue_days=overdue_days,
    )
    results["payment_reminders"] = reminders_summary_path
    append_audit_log(
        output_dir,
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event_type": "payment_reminders_generated",
            "status": "success",
            "details": f"{reminders_summary_path.relative_to(BASE_DIR)}; overdue_days={overdue_days}",
            "source": "run_local_workflow.py",
        },
    )

    audit_path = append_audit_log(
        output_dir,
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event_type": "local_workflow_completed",
            "status": "success",
            "details": "Generated daily report, price list, and payment reminder drafts locally.",
            "source": "run_local_workflow.py",
        },
    )
    results["audit_log"] = audit_path
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the complete local safe workflow.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Workflow date in YYYY-MM-DD format.")
    parser.add_argument("--exchange-rate", required=True, type=float, help="Manual USD to SYP exchange rate.")
    parser.add_argument("--overdue-days", default=4, type=int, help="Minimum overdue days before reminders are generated.")
    parser.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR), help="Directory containing CSV sample files.")
    parser.add_argument("--templates-dir", default=str(DEFAULT_TEMPLATES_DIR), help="Directory containing Markdown templates.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for generated local outputs.")
    args = parser.parse_args()

    report_date = parse_report_date(args.date)
    results = run_workflow(
        report_date=report_date,
        exchange_rate=args.exchange_rate,
        overdue_days=args.overdue_days,
        samples_dir=Path(args.samples_dir),
        templates_dir=Path(args.templates_dir),
        output_dir=Path(args.output_dir),
    )

    print("Local workflow completed successfully.")
    for name, path in results.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
