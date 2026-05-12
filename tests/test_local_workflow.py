#!/usr/bin/env python3
"""
Basic local workflow tests.

These tests use only the Python standard library. They verify that the local
scripts can generate expected output files from the sample CSV data.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def run_command(args: list[str], output_dir: Path) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, *args, "--output-dir", str(output_dir)]
    return subprocess.run(
        command,
        cwd=BASE_DIR,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, (
        "Command failed\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}\n"
    )


def test_generate_daily_report(output_dir: Path) -> None:
    result = run_command(["scripts/generate_daily_report.py", "--date", "2026-05-12"], output_dir)
    assert_success(result)
    report_path = output_dir / "daily-report-2026-05-12.md"
    assert report_path.exists(), "Daily report was not generated."
    content = report_path.read_text(encoding="utf-8")
    assert "تقرير نهاية اليوم" in content
    assert "تحصيل الكاش اليوم" in content


def test_generate_price_list(output_dir: Path) -> None:
    result = run_command(
        ["scripts/generate_price_list.py", "--date", "2026-05-12", "--exchange-rate", "15000"],
        output_dir,
    )
    assert_success(result)
    price_list_path = output_dir / "price-list-2026-05-12.md"
    assert price_list_path.exists(), "Price list was not generated."
    content = price_list_path.read_text(encoding="utf-8")
    assert "نشرة أسعار اليوم" in content
    assert "Sample Product A" in content
    assert "| A002 |" not in content, "Out-of-stock product should not appear in published price rows."


def test_generate_payment_reminders(output_dir: Path) -> None:
    result = run_command(
        ["scripts/generate_payment_reminders.py", "--date", "2026-05-12", "--overdue-days", "4"],
        output_dir,
    )
    assert_success(result)
    summary_path = output_dir / "payment-reminders" / "2026-05-12" / "summary.md"
    assert summary_path.exists(), "Payment reminder summary was not generated."
    content = summary_path.read_text(encoding="utf-8")
    assert "تقرير العملاء المتأخرين والأرصدة" in content
    assert "الرصيد المتأخر" in content


def test_analyze_inventory_movement(output_dir: Path) -> None:
    result = run_command(
        ["scripts/analyze_inventory_movement.py", "--date", "2026-05-12"],
        output_dir,
    )
    assert_success(result)
    report_path = output_dir / "inventory-movement-2026-05-12.md"
    assert report_path.exists(), "Inventory movement report was not generated."
    content = report_path.read_text(encoding="utf-8")
    assert "تحليل حركة الأصناف" in content
    assert "أصناف مطلوبة وكمّيتها قليلة" in content
    assert "أصناف راكدة أو للتصريف" in content


def test_run_local_workflow_with_config_default(output_dir: Path) -> None:
    result = run_command(
        ["scripts/run_local_workflow.py", "--date", "2026-05-12", "--exchange-rate", "15000"],
        output_dir,
    )
    assert_success(result)
    assert (output_dir / "daily-report-2026-05-12.md").exists()
    assert (output_dir / "price-list-2026-05-12.md").exists()
    assert (output_dir / "payment-reminders" / "2026-05-12" / "summary.md").exists()
    assert (output_dir / "inventory-movement-2026-05-12.md").exists()
    audit_log = output_dir / "audit-log.csv"
    assert audit_log.exists(), "Audit log was not generated."
    audit_content = audit_log.read_text(encoding="utf-8")
    assert "inventory_movement_report_generated" in audit_content
    assert "local_workflow_completed" in audit_content


def main() -> None:
    temp_dir = Path(tempfile.mkdtemp(prefix="local-workflow-tests-"))
    try:
        test_generate_daily_report(temp_dir)
        test_generate_price_list(temp_dir)
        test_generate_payment_reminders(temp_dir)
        test_analyze_inventory_movement(temp_dir)
        test_run_local_workflow_with_config_default(temp_dir)
        print("All local workflow tests passed.")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
