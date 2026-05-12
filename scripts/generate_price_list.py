#!/usr/bin/env python3
"""
Local daily price-list generator.

This script reads local product and inventory CSV files, asks for or accepts a
manual exchange rate, and creates a Markdown price list inside output/.

Business pricing rule:
- price_usd is treated as carton price in USD.
- secondary_unit_conversion_factor is the number of crozes in one carton.
- croze price USD = carton price USD / secondary_unit_conversion_factor.
- croze price SYP = croze price USD * exchange rate.

It does not connect to the internet, fetch exchange rates automatically, send
messages, publish to social media, or modify source data.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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
    secondary_unit_conversion_factor: Optional[float]


@dataclass
class InventoryItem:
    product_code: str
    warehouse_name: str
    available_quantity: float
    last_updated: str


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
            secondary_unit_conversion_factor=parse_optional_float(row.get("secondary_unit_conversion_factor", "")),
        )
        if product.product_code:
            products[product.product_code] = product
    return products


def load_inventory(samples_dir: Path) -> List[InventoryItem]:
    inventory: List[InventoryItem] = []
    for row in read_csv(samples_dir / "inventory.csv"):
        inventory.append(
            InventoryItem(
                product_code=row.get("product_code", "").strip(),
                warehouse_name=row.get("warehouse_name", "").strip(),
                available_quantity=parse_float(row.get("available_quantity", "")),
                last_updated=row.get("last_updated", "").strip(),
            )
        )
    return inventory


def money(value: float) -> str:
    return f"{value:,.2f}"


def syp_money(value: float) -> str:
    return f"{round(value):,}"


def infer_group(product: Product) -> str:
    if product.category:
        return product.category
    match = re.match(r"^\s*(\d+)", product.product_name)
    if match:
        return match.group(1)
    first_word = product.product_name.split()[0] if product.product_name.split() else "غير مصنف"
    return first_word


def validate_exchange_rate(exchange_rate: float) -> None:
    if exchange_rate <= 0:
        raise ValueError("Exchange rate must be greater than zero.")
    if exchange_rate > 1_000_000:
        raise ValueError("Exchange rate is unusually high. Please verify it before generating the list.")


def get_exchange_rate(value: Optional[str]) -> float:
    if value is None:
        value = input("Enter today's USD to SYP exchange rate: ").strip()
    exchange_rate = parse_float(value)
    validate_exchange_rate(exchange_rate)
    return exchange_rate


def build_price_rows(
    products: Dict[str, Product],
    inventory: List[InventoryItem],
    exchange_rate: float,
) -> Tuple[str, List[str], List[str]]:
    row_data: List[Tuple[str, str, str]] = []
    excluded_items: List[str] = []
    review_items: List[str] = []

    for item in inventory:
        product = products.get(item.product_code)
        if product is None:
            review_items.append(f"{item.product_code}: موجود في المخزون لكنه غير موجود في ملف المنتجات.")
            continue

        if not product.is_active:
            excluded_items.append(f"{product.product_name}: غير مفعّل للبيع.")
            continue

        if item.available_quantity <= 0:
            excluded_items.append(f"{product.product_name}: غير متوفر في المخزون.")
            continue

        if product.price_usd is None:
            review_items.append(f"{product.product_name}: متوفر لكن لا يوجد له سعر كرتون بالدولار.")
            continue

        if product.secondary_unit_conversion_factor is None or product.secondary_unit_conversion_factor <= 0:
            review_items.append(f"{product.product_name}: متوفر وله سعر لكن لا يوجد عامل تحويل صحيح من الكرتون إلى الكروز.")
            continue

        group = infer_group(product)
        carton_price_usd = product.price_usd
        conversion_factor = product.secondary_unit_conversion_factor
        croze_price_usd = carton_price_usd / conversion_factor
        croze_price_syp = croze_price_usd * exchange_rate
        row = (
            f"| {group} | {product.product_code} | {product.product_name} | "
            f"{item.available_quantity:g} {product.unit} | {money(carton_price_usd)} | "
            f"{money(conversion_factor)} | {money(croze_price_usd)} | {syp_money(croze_price_syp)} |"
        )
        row_data.append((group, product.product_name, row))

    row_data.sort(key=lambda item: (item[0], item[1]))
    rows = [item[2] for item in row_data]
    price_rows = "\n".join(rows) if rows else "| - | - | لا توجد أصناف متوفرة قابلة للنشر | - | - | - | - | - |"
    return price_rows, excluded_items, review_items


def bullet_lines(items: List[str]) -> str:
    if not items:
        return "- لا توجد عناصر."
    return "\n".join(f"- {item}" for item in items)


def build_report_section(excluded_items: List[str], review_items: List[str]) -> str:
    return (
        "\n\n## تقرير المراجعة قبل النشر\n\n"
        f"### الأصناف المستبعدة\n\n{bullet_lines(excluded_items)}\n\n"
        f"### الأصناف التي تحتاج مراجعة\n\n{bullet_lines(review_items)}\n"
    )


def generate_price_list(
    samples_dir: Path,
    templates_dir: Path,
    output_dir: Path,
    report_date: date,
    exchange_rate: float,
) -> Path:
    products = load_products(samples_dir)
    inventory = load_inventory(samples_dir)
    price_rows, excluded_items, review_items = build_price_rows(products, inventory, exchange_rate)

    template_path = templates_dir / "price-list.md"
    template = template_path.read_text(encoding="utf-8")
    content = template
    replacements = {
        "{{date}}": report_date.isoformat(),
        "{{exchange_rate}}": syp_money(exchange_rate),
        "{{price_rows}}": price_rows,
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    content += build_report_section(excluded_items, review_items)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"price-list-{report_date.isoformat()}.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a local daily price list.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Report date in YYYY-MM-DD format.")
    parser.add_argument("--exchange-rate", default=None, help="Manual USD to SYP exchange rate. If omitted, you will be prompted.")
    parser.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR), help="Directory containing CSV sample files.")
    parser.add_argument("--templates-dir", default=str(DEFAULT_TEMPLATES_DIR), help="Directory containing Markdown templates.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for generated price lists.")
    args = parser.parse_args()

    report_date = parse_date(args.date)
    exchange_rate = get_exchange_rate(args.exchange_rate)
    output_path = generate_price_list(
        samples_dir=Path(args.samples_dir),
        templates_dir=Path(args.templates_dir),
        output_dir=Path(args.output_dir),
        report_date=report_date,
        exchange_rate=exchange_rate,
    )
    print(f"Price list generated: {output_path}")


if __name__ == "__main__":
    main()
