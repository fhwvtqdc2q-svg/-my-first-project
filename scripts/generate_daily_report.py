#!/usr/bin/env python3
"""
Local daily accounting report generator.

This script reads local CSV files from the samples/ directory and creates a
Markdown report inside output/. It does not connect to the internet, send
messages, access accounts, or modify source data.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SAMPLES_DIR = BASE_DIR / "samples"
DEFAULT_TEMPLATES_DIR = BASE_DIR / "templates"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"


@dataclass
class Product:
    product_code: str
    product_name: str
    category: str
    unit: str
    price_usd: Optional[float]
    is_active: bool


@dataclass
class InventoryItem:
    product_code: str
    warehouse_name: str
    available_quantity: float
    last_updated: str


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


@dataclass
class Payment:
    payment_id: str
    customer_id: str
    invoice_id: str
    payment_date: date
    amount: float
    payment_method: str


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


def parse_optional_float(value: str) -> Optional[float]:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_bool(value: str) -> bool:
    return (value or "").strip().lower() in {"true", "1", "yes", "y"}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_products(samples_dir: Path) -> Dict[str, Product]:
    products: Dict[str, Product] = {}
    for row in read_csv(samples_dir / "products.csv"):
        product = Product(
            product_code=row.get("product_code", "").strip(),
            product_name=row.get("product_name", "").strip(),
            category=row.get("category", "").strip(),
            unit=row.get("unit", "").strip(),
            price_usd=parse_optional_float(row.get("price_usd", "")),
            is_active=parse_bool(row.get("is_active", "")),
        )
        if product.product_code:
            products[product.product_code] = product
    return products


def load_inventory(samples_dir: Path) -> List[InventoryItem]:
    items: List[InventoryItem] = []
    for row in read_csv(samples_dir / "inventory.csv"):
        items.append(
            InventoryItem(
                product_code=row.get("product_code", "").strip(),
                warehouse_name=row.get("warehouse_name", "").strip(),
                available_quantity=parse_float(row.get("available_quantity", "")),
                last_updated=row.get("last_updated", "").strip(),
            )
        )
    return items


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


def load_payments(samples_dir: Path) -> List[Payment]:
    payments: List[Payment] = []
    for row in read_csv(samples_dir / "payments.csv"):
        payments.append(
            Payment(
                payment_id=row.get("payment_id", "").strip(),
                customer_id=row.get("customer_id", "").strip(),
                invoice_id=row.get("invoice_id", "").strip(),
                payment_date=parse_date(row.get("payment_date", "")),
                amount=parse_float(row.get("amount", "")),
                payment_method=row.get("payment_method", "").strip().lower(),
            )
        )
    return payments


def money(value: float) -> str:
    return f"{value:,.2f}"


def bullet_lines(lines: Iterable[str]) -> str:
    lines = list(lines)
    if not lines:
        return "- لا توجد عناصر تحتاج متابعة."
    return "\n".join(f"- {line}" for line in lines)


def calculate_cash_today(payments: List[Payment], report_date: date) -> float:
    return sum(
        payment.amount
        for payment in payments
        if payment.payment_date == report_date and payment.payment_method == "cash"
    )


def calculate_cash_average(payments: List[Payment], report_date: date, days: int = 7) -> float:
    previous_amounts: List[float] = []
    for offset in range(1, days + 1):
        current_day = report_date.fromordinal(report_date.toordinal() - offset)
        total = sum(
            payment.amount
            for payment in payments
            if payment.payment_date == current_day and payment.payment_method == "cash"
        )
        previous_amounts.append(total)
    return sum(previous_amounts) / days if previous_amounts else 0.0


def build_report(samples_dir: Path, templates_dir: Path, output_dir: Path, report_date: date) -> Path:
    products = load_products(samples_dir)
    inventory = load_inventory(samples_dir)
    customers = load_customers(samples_dir)
    invoices = load_invoices(samples_dir)
    payments = load_payments(samples_dir)

    cash_today = calculate_cash_today(payments, report_date)
    cash_average = calculate_cash_average(payments, report_date)

    if cash_average == 0:
        cash_status = "لا يوجد متوسط سابق كافٍ للمقارنة"
    elif cash_today < cash_average * 0.75:
        cash_status = "منخفض ويحتاج مراجعة"
    else:
        cash_status = "طبيعي"

    available_product_codes = {
        item.product_code
        for item in inventory
        if item.available_quantity > 0
        and item.product_code in products
        and products[item.product_code].is_active
    }
    out_of_stock_items = [
        item for item in inventory if item.available_quantity <= 0 and item.product_code in products
    ]
    missing_price_products = [
        product for product in products.values() if product.is_active and product.price_usd is None
    ]

    overdue_invoices: List[Invoice] = []
    for invoice in invoices:
        if invoice.is_open and (report_date - invoice.due_date).days >= 4:
            overdue_invoices.append(invoice)

    customer_due_totals: Dict[str, float] = {}
    for invoice in invoices:
        if invoice.is_open:
            customer_due_totals[invoice.customer_id] = customer_due_totals.get(invoice.customer_id, 0.0) + invoice.amount_due

    highest_due_customer = "لا يوجد"
    if customer_due_totals:
        customer_id, due_amount = max(customer_due_totals.items(), key=lambda item: item[1])
        customer_name = customers.get(customer_id, Customer(customer_id, customer_id, "", 0)).customer_name
        highest_due_customer = f"{customer_name} ({money(due_amount)})"

    alerts: List[str] = []
    if cash_status == "منخفض ويحتاج مراجعة":
        alerts.append(
            f"تحصيل الكاش اليوم ({money(cash_today)}) أقل من متوسط آخر 7 أيام ({money(cash_average)})."
        )
    for invoice in overdue_invoices:
        customer_name = customers.get(invoice.customer_id, Customer(invoice.customer_id, invoice.customer_id, "", 0)).customer_name
        days_overdue = (report_date - invoice.due_date).days
        alerts.append(
            f"العميل {customer_name} لديه فاتورة {invoice.invoice_id} متأخرة {days_overdue} أيام، المبلغ المتبقي {money(invoice.amount_due)}."
        )
    for item in out_of_stock_items:
        product_name = products[item.product_code].product_name
        alerts.append(f"الصنف {product_name} غير متوفر في المخزون ويجب ألا يظهر في نشرة الأسعار.")
    for product in missing_price_products:
        alerts.append(f"الصنف {product.product_name} مفعّل لكن لا يوجد له سعر، ويحتاج مراجعة قبل النشر.")

    recommendations: List[str] = []
    if overdue_invoices:
        recommendations.append("تجهيز رسائل تذكير للزبائن المتأخرين، دون إرسالها إلا بعد الموافقة.")
    if out_of_stock_items:
        recommendations.append("تحديث نشرة الأسعار واستبعاد الأصناف غير المتوفرة.")
    if missing_price_products:
        recommendations.append("مراجعة أسعار الأصناف المفعلة التي لا تحتوي على سعر.")
    recommendations.append("حفظ نسخة من تقرير اليوم داخل الأرشيف المحلي.")

    template_path = templates_dir / "daily-report.md"
    template = template_path.read_text(encoding="utf-8")
    report = template
    replacements = {
        "{{date}}": report_date.isoformat(),
        "{{cash_today}}": money(cash_today),
        "{{cash_7_day_average}}": money(cash_average),
        "{{cash_status}}": cash_status,
        "{{available_products_count}}": str(len(available_product_codes)),
        "{{out_of_stock_count}}": str(len(out_of_stock_items)),
        "{{missing_price_count}}": str(len(missing_price_products)),
        "{{overdue_customers_count}}": str(len({invoice.customer_id for invoice in overdue_invoices})),
        "{{highest_due_customer}}": highest_due_customer,
        "{{alerts}}": bullet_lines(alerts),
        "{{recommendations}}": bullet_lines(recommendations),
    }
    for placeholder, value in replacements.items():
        report = report.replace(placeholder, value)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"daily-report-{report_date.isoformat()}.md"
    output_path.write_text(report, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a local daily accounting report.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Report date in YYYY-MM-DD format.")
    parser.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR), help="Directory containing CSV sample files.")
    parser.add_argument("--templates-dir", default=str(DEFAULT_TEMPLATES_DIR), help="Directory containing Markdown templates.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for generated reports.")
    args = parser.parse_args()

    report_date = parse_date(args.date)
    output_path = build_report(
        samples_dir=Path(args.samples_dir),
        templates_dir=Path(args.templates_dir),
        output_dir=Path(args.output_dir),
        report_date=report_date,
    )
    print(f"Daily report generated: {output_path}")


if __name__ == "__main__":
    main()
