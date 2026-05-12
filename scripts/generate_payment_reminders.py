#!/usr/bin/env python3
"""
Local overdue customer reminder generator.

This script reads local customer and invoice CSV files, identifies customers
with overdue balances, and creates local Markdown reminder drafts in output/.

It does not send WhatsApp messages, SMS, emails, or connect to the internet.
All generated reminders are drafts for manual review only.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SAMPLES_DIR = BASE_DIR / "samples"
DEFAULT_TEMPLATES_DIR = BASE_DIR / "templates"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"


@dataclass
class Customer:
    customer_id: str
    customer_name: str
    priority_level: str
    credit_limit: float


@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    invoice_date: date
    due_date: date
    total_amount: float
    amount_paid: float
    payment_method: str
    status: str

    @property
    def amount_due(self) -> float:
        return max(self.total_amount - self.amount_paid, 0.0)

    @property
    def is_open(self) -> bool:
        return self.amount_due > 0 and self.status.lower() != "paid"


def parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def parse_float(value: str, default: float = 0.0) -> float:
    value = (value or "").strip()
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_customers(samples_dir: Path) -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    for row in read_csv(samples_dir / "customers.csv"):
        customer = Customer(
            customer_id=row.get("customer_id", "").strip(),
            customer_name=row.get("customer_name", "").strip(),
            priority_level=row.get("priority_level", "").strip(),
            credit_limit=parse_float(row.get("credit_limit", "")),
        )
        if customer.customer_id:
            customers[customer.customer_id] = customer
    return customers


def load_invoices(samples_dir: Path) -> List[Invoice]:
    invoices: List[Invoice] = []
    for row in read_csv(samples_dir / "invoices.csv"):
        invoices.append(
            Invoice(
                invoice_id=row.get("invoice_id", "").strip(),
                customer_id=row.get("customer_id", "").strip(),
                invoice_date=parse_date(row.get("invoice_date", "")),
                due_date=parse_date(row.get("due_date", "")),
                total_amount=parse_float(row.get("total_amount", "")),
                amount_paid=parse_float(row.get("amount_paid", "")),
                payment_method=row.get("payment_method", "").strip().lower(),
                status=row.get("status", "").strip().lower(),
            )
        )
    return invoices


def money(value: float) -> str:
    return f"{value:,.2f}"


def safe_file_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value.strip())
    return cleaned.strip("-") or "customer"


def render_template(template: str, replacements: Dict[str, str]) -> str:
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def group_open_invoices_by_customer(invoices: List[Invoice]) -> Dict[str, List[Invoice]]:
    grouped: Dict[str, List[Invoice]] = {}
    for invoice in invoices:
        if invoice.is_open:
            grouped.setdefault(invoice.customer_id, []).append(invoice)
    return grouped


def invoice_lines(invoices: List[Invoice], report_date: date) -> str:
    lines: List[str] = []
    for invoice in sorted(invoices, key=lambda item: item.due_date):
        days_overdue = max((report_date - invoice.due_date).days, 0)
        status = "متأخرة" if days_overdue > 0 else "غير مستحقة بعد"
        lines.append(
            f"- فاتورة {invoice.invoice_id}: الرصيد المتبقي {money(invoice.amount_due)}، "
            f"تاريخ الاستحقاق {invoice.due_date.isoformat()}، الحالة: {status} ({days_overdue} يوم)."
        )
    return "\n".join(lines)


def generate_reminders(
    samples_dir: Path,
    templates_dir: Path,
    output_dir: Path,
    report_date: date,
    overdue_days: int,
) -> Path:
    customers = load_customers(samples_dir)
    invoices = load_invoices(samples_dir)
    open_by_customer = group_open_invoices_by_customer(invoices)

    template = (templates_dir / "payment-reminder.md").read_text(encoding="utf-8")
    reminders_dir = output_dir / "payment-reminders" / report_date.isoformat()
    reminders_dir.mkdir(parents=True, exist_ok=True)

    summary_lines: List[str] = [
        "# تقرير العملاء المتأخرين والأرصدة",
        "",
        f"التاريخ: {report_date.isoformat()}",
        f"قاعدة التأخير: {overdue_days} أيام أو أكثر بعد تاريخ الاستحقاق.",
        "",
    ]

    generated_count = 0
    for customer_id, customer_invoices in sorted(open_by_customer.items()):
        overdue_invoices = [
            invoice
            for invoice in customer_invoices
            if (report_date - invoice.due_date).days >= overdue_days
        ]
        if not overdue_invoices:
            continue

        customer = customers.get(customer_id, Customer(customer_id, customer_id, "", 0.0))
        total_balance = sum(invoice.amount_due for invoice in customer_invoices)
        overdue_balance = sum(invoice.amount_due for invoice in overdue_invoices)
        oldest_overdue_days = max((report_date - invoice.due_date).days for invoice in overdue_invoices)

        draft_message = render_template(
            template,
            {
                "customer_name": customer.customer_name,
                "days_overdue": str(oldest_overdue_days),
                "amount_due": money(overdue_balance),
            },
        )

        content = (
            f"# مسودة تذكير دفع\n\n"
            f"## بيانات العميل\n\n"
            f"- العميل: {customer.customer_name}\n"
            f"- رقم العميل: {customer.customer_id}\n"
            f"- أولوية العميل: {customer.priority_level or 'غير محددة'}\n"
            f"- إجمالي الرصيد المفتوح على العميل: {money(total_balance)}\n"
            f"- الرصيد المتأخر المطلوب متابعته: {money(overdue_balance)}\n"
            f"- أقدم تأخير: {oldest_overdue_days} يوم\n\n"
            f"## الفواتير المفتوحة\n\n"
            f"{invoice_lines(customer_invoices, report_date)}\n\n"
            f"## مسودة الرسالة\n\n"
            f"{draft_message}\n\n"
            f"## ملاحظة أمان\n\n"
            f"هذه مسودة فقط. لا يتم إرسالها تلقائيًا. يجب مراجعتها والموافقة عليها يدويًا قبل الإرسال.\n"
        )

        output_file = reminders_dir / f"{safe_file_name(customer.customer_id)}-{safe_file_name(customer.customer_name)}.md"
        output_file.write_text(content, encoding="utf-8")
        generated_count += 1

        summary_lines.extend(
            [
                f"## {customer.customer_name}",
                "",
                f"- إجمالي الرصيد المفتوح: {money(total_balance)}",
                f"- الرصيد المتأخر: {money(overdue_balance)}",
                f"- أقدم تأخير: {oldest_overdue_days} يوم",
                f"- ملف المسودة: `{output_file.name}`",
                "",
            ]
        )

    if generated_count == 0:
        summary_lines.append("لا يوجد عملاء متأخرون حسب القاعدة المحددة.")

    summary_path = reminders_dir / "summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate local overdue customer reminder drafts.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Report date in YYYY-MM-DD format.")
    parser.add_argument("--overdue-days", type=int, default=4, help="Minimum overdue days before a reminder is generated.")
    parser.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR), help="Directory containing CSV sample files.")
    parser.add_argument("--templates-dir", default=str(DEFAULT_TEMPLATES_DIR), help="Directory containing Markdown templates.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for generated reminder drafts.")
    args = parser.parse_args()

    report_date = parse_date(args.date)
    summary_path = generate_reminders(
        samples_dir=Path(args.samples_dir),
        templates_dir=Path(args.templates_dir),
        output_dir=Path(args.output_dir),
        report_date=report_date,
        overdue_days=args.overdue_days,
    )
    print(f"Payment reminder drafts generated: {summary_path}")


if __name__ == "__main__":
    main()
