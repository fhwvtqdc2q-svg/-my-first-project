#!/usr/bin/env python3
"""
Local inventory movement analyzer.

This script identifies:
- High-demand low-stock items that may need reorder.
- Slow-moving or dead-stock items that may need clearance offers.

It generates a local Markdown report only. It does not send messages, publish
content, connect to the internet, or modify inventory data.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
DEFAULT_SAMPLES_DIR = BASE_DIR / "samples"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"
DEFAULT_SETTINGS_PATH = BASE_DIR / "config" / "settings.json"

sys.path.insert(0, str(SCRIPTS_DIR))

from local_settings import load_settings, require_local_safe_settings  # noqa: E402


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
class ProductMovement:
    product_code: str
    last_sale_date: Optional[date]
    sales_last_7_days: float
    sales_last_30_days: float


def parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def parse_optional_date(value: str) -> Optional[date]:
    value = (value or "").strip()
    if not value:
        return None
    return parse_date(value)


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


def load_inventory(samples_dir: Path) -> Dict[str, InventoryItem]:
    inventory: Dict[str, InventoryItem] = {}
    for row in read_csv(samples_dir / "inventory.csv"):
        item = InventoryItem(
            product_code=row.get("product_code", "").strip(),
            warehouse_name=row.get("warehouse_name", "").strip(),
            available_quantity=parse_float(row.get("available_quantity", "")),
            last_updated=row.get("last_updated", "").strip(),
        )
        if item.product_code:
            inventory[item.product_code] = item
    return inventory


def load_movement(samples_dir: Path) -> Dict[str, ProductMovement]:
    movement: Dict[str, ProductMovement] = {}
    for row in read_csv(samples_dir / "product_movement.csv"):
        item = ProductMovement(
            product_code=row.get("product_code", "").strip(),
            last_sale_date=parse_optional_date(row.get("last_sale_date", "")),
            sales_last_7_days=parse_float(row.get("sales_last_7_days", "")),
            sales_last_30_days=parse_float(row.get("sales_last_30_days", "")),
        )
        if item.product_code:
            movement[item.product_code] = item
    return movement


def days_since(last_sale_date: Optional[date], report_date: date) -> Optional[int]:
    if last_sale_date is None:
        return None
    return max((report_date - last_sale_date).days, 0)


def line_for_item(product: Product, inventory: InventoryItem, movement: ProductMovement, report_date: date) -> str:
    days = days_since(movement.last_sale_date, report_date)
    days_text = "لا يوجد تاريخ بيع" if days is None else f"آخر بيع منذ {days} يوم"
    return (
        f"- {product.product_name} ({product.product_code}) — الكمية: {inventory.available_quantity:g} {product.unit}، "
        f"مبيعات آخر 30 يومًا: {movement.sales_last_30_days:g}، {days_text}."
    )


def generate_report(samples_dir: Path, output_dir: Path, settings_path: Path, report_date: date) -> Path:
    settings = load_settings(settings_path)
    require_local_safe_settings(settings)
    thresholds = settings.get("inventory_movement", {})

    low_stock_quantity = float(thresholds.get("low_stock_quantity", 5))
    high_sales_30_days = float(thresholds.get("high_sales_30_days", 10))
    slow_moving_days = int(thresholds.get("slow_moving_days", 30))
    dead_stock_days = int(thresholds.get("dead_stock_days", 60))
    dead_stock_min_quantity = float(thresholds.get("dead_stock_min_quantity", 10))

    products = load_products(samples_dir)
    inventory = load_inventory(samples_dir)
    movement = load_movement(samples_dir)

    reorder_items: List[str] = []
    slow_items: List[str] = []
    dead_items: List[str] = []
    review_items: List[str] = []

    for product_code, product in products.items():
        if not product.is_active:
            continue

        item = inventory.get(product_code)
        move = movement.get(product_code)
        if item is None:
            review_items.append(f"- {product.product_name} ({product.product_code}) — لا يوجد سجل مخزون.")
            continue
        if move is None:
            review_items.append(f"- {product.product_name} ({product.product_code}) — لا يوجد سجل حركة مبيعات.")
            continue

        quantity = item.available_quantity
        days = days_since(move.last_sale_date, report_date)

        if quantity > 0 and quantity <= low_stock_quantity and move.sales_last_30_days >= high_sales_30_days:
            reorder_items.append(line_for_item(product, item, move, report_date) + " الاقتراح: إعادة طلب كمية جديدة.")
            continue

        if quantity > 0 and days is not None and days >= dead_stock_days and quantity >= dead_stock_min_quantity:
            dead_items.append(line_for_item(product, item, move, report_date) + " الاقتراح: تصريف بعرض خاص أو ترشيحه لزبائن مناسبين.")
            continue

        if quantity > 0 and days is not None and days >= slow_moving_days:
            slow_items.append(line_for_item(product, item, move, report_date) + " الاقتراح: مراقبته أو إدخاله ضمن عرض خفيف.")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"inventory-movement-{report_date.isoformat()}.md"

    def section(title: str, items: List[str], empty: str) -> str:
        return f"## {title}\n\n" + ("\n".join(items) if items else f"- {empty}") + "\n"

    report = "\n".join(
        [
            "# تحليل حركة الأصناف",
            "",
            f"التاريخ: {report_date.isoformat()}",
            "",
            "## قواعد التحليل المستخدمة",
            "",
            f"- كمية قليلة: أقل من أو تساوي {low_stock_quantity:g}.",
            f"- مبيعات عالية خلال 30 يومًا: أكبر من أو تساوي {high_sales_30_days:g}.",
            f"- بطيء الحركة: لا بيع منذ {slow_moving_days} يومًا أو أكثر.",
            f"- راكد/للتصريف: لا بيع منذ {dead_stock_days} يومًا أو أكثر وكمية لا تقل عن {dead_stock_min_quantity:g}.",
            "",
            section("أصناف مطلوبة وكمّيتها قليلة — إعادة طلب", reorder_items, "لا توجد أصناف تحتاج إعادة طلب حسب القواعد الحالية."),
            section("أصناف بطيئة الحركة — مراقبة أو عرض خفيف", slow_items, "لا توجد أصناف بطيئة الحركة حسب القواعد الحالية."),
            section("أصناف راكدة أو للتصريف", dead_items, "لا توجد أصناف راكدة حسب القواعد الحالية."),
            section("أصناف تحتاج مراجعة بيانات", review_items, "لا توجد أصناف تحتاج مراجعة بيانات."),
            "## ملاحظات للرسائل الخارجية",
            "",
            "- لا تستخدم عبارة صنف ميت أو بضاعة راكدة مع الزبائن.",
            "- استخدم عبارات مثل: عرض خاص، كمية محدودة، أصناف مختارة.",
            "- لا يتم إرسال أي رسالة تلقائيًا. هذه النتائج للمراجعة الداخلية فقط.",
            "",
        ]
    )
    output_path.write_text(report, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze local inventory movement and clearance candidates.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Analysis date in YYYY-MM-DD format.")
    parser.add_argument("--settings", default=str(DEFAULT_SETTINGS_PATH), help="Path to local settings JSON file.")
    parser.add_argument("--samples-dir", default=str(DEFAULT_SAMPLES_DIR), help="Directory containing CSV sample files.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for generated local outputs.")
    args = parser.parse_args()

    output_path = generate_report(
        samples_dir=Path(args.samples_dir),
        output_dir=Path(args.output_dir),
        settings_path=Path(args.settings),
        report_date=parse_date(args.date),
    )
    print(f"Inventory movement report generated: {output_path}")


if __name__ == "__main__":
    main()
