#!/usr/bin/env python3
"""
Generate a polished customer-facing price list from the Arabic price workbook.

Outputs:
- A styled RTL HTML file suitable for WhatsApp sharing as PDF or screenshot.
- Optionally attempts to create a PDF using Microsoft Edge / Chrome headless.

The original Excel file is read-only and never modified.
"""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import List

from generate_price_list_from_price_workbook import (
    DEFAULT_SHEET_NAME,
    PriceItem,
    load_items_from_workbook,
    parse_date,
    syp_money,
)


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"


def money(value: float) -> str:
    return f"{value:,.2f}"


def find_browser_executable() -> str | None:
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    for name in ["msedge", "chrome", "chrome.exe", "msedge.exe"]:
        found = shutil.which(name)
        if found:
            return found
    return None


def unit_and_price(item: PriceItem, exchange_rate: float) -> tuple[str, str, str, str]:
    if item.factor > 1:
        usd_unit = "كرتونة"
        syp_unit = "كروز"
        syp_price = (item.price_usd or 0) / item.factor * exchange_rate
    else:
        usd_unit = "قطعة"
        syp_unit = "قطعة"
        syp_price = (item.price_usd or 0) * exchange_rate
    return usd_unit, money(item.price_usd or 0), syp_unit, syp_money(syp_price)


def build_rows(items: List[PriceItem], exchange_rate: float, mode: str) -> str:
    rows: List[str] = []
    current_group = None
    for item in items:
        if item.group != current_group:
            current_group = item.group
            rows.append(
                f'<tr class="group"><td colspan="3">{html.escape(current_group)}</td></tr>'
            )
        usd_unit, usd_price, syp_unit, syp_price = unit_and_price(item, exchange_rate)
        if mode == "usd":
            unit = usd_unit
            price = usd_price
        else:
            unit = syp_unit
            price = syp_price
        rows.append(
            "<tr>"
            f"<td class=\"item\">{html.escape(item.name)}</td>"
            f"<td class=\"unit\">{html.escape(unit)}</td>"
            f"<td class=\"price\">{html.escape(price)}</td>"
            "</tr>"
        )
    if not rows:
        return '<tr><td colspan="3" class="empty">لا توجد أصناف قابلة للنشر</td></tr>'
    return "\n".join(rows)


def build_review(review_items: List[str]) -> str:
    if not review_items:
        return '<div class="ok">لا توجد أصناف تحتاج تسعير.</div>'
    items = "\n".join(f"<li>{html.escape(item)}</li>" for item in review_items)
    return f"<ul>{items}</ul>"


def build_html(
    items: List[PriceItem],
    review_items: List[str],
    report_date: date,
    exchange_rate: float,
    source_file: Path,
) -> str:
    usd_rows = build_rows(items, exchange_rate, "usd")
    syp_rows = build_rows(items, exchange_rate, "syp")
    review_html = build_review(review_items)
    generated_at = datetime.now().isoformat(timespec="seconds")

    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>نشرة أسعار اليوم</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #f3f4f6;
    color: #111827;
    font-family: "Segoe UI", Tahoma, Arial, sans-serif;
    direction: rtl;
  }}
  .page {{
    width: 210mm;
    min-height: 297mm;
    margin: 0 auto;
    background: #ffffff;
    padding: 18mm 14mm;
  }}
  .header {{
    border: 2px solid #111827;
    border-radius: 18px;
    padding: 18px 22px;
    margin-bottom: 18px;
    background: linear-gradient(135deg, #ffffff, #f9fafb);
  }}
  .brand {{
    font-size: 30px;
    font-weight: 800;
    margin: 0 0 6px 0;
    letter-spacing: -0.5px;
  }}
  .meta {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    font-size: 15px;
    color: #374151;
  }}
  .pill {{
    border: 1px solid #d1d5db;
    background: #fff;
    border-radius: 999px;
    padding: 6px 12px;
  }}
  .section {{
    margin-top: 18px;
    page-break-inside: avoid;
  }}
  .section-title {{
    font-size: 22px;
    font-weight: 800;
    margin: 0 0 10px 0;
    padding: 10px 14px;
    border-radius: 12px;
    background: #111827;
    color: #fff;
  }}
  table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    overflow: hidden;
    border: 1px solid #d1d5db;
    border-radius: 14px;
    font-size: 14px;
  }}
  th {{
    background: #f3f4f6;
    color: #111827;
    padding: 10px;
    text-align: right;
    border-bottom: 1px solid #d1d5db;
  }}
  td {{
    padding: 9px 10px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
  }}
  tr:last-child td {{ border-bottom: 0; }}
  .group td {{
    background: #e5e7eb;
    color: #111827;
    font-weight: 800;
    padding: 8px 10px;
  }}
  .item {{ width: 62%; font-weight: 600; }}
  .unit {{ width: 16%; white-space: nowrap; color: #374151; }}
  .price {{ width: 22%; text-align: left; direction: ltr; font-weight: 800; white-space: nowrap; }}
  .review {{
    margin-top: 18px;
    border: 1px dashed #9ca3af;
    border-radius: 14px;
    padding: 12px 16px;
    background: #fffbeb;
    font-size: 13px;
  }}
  .review h2 {{ margin: 0 0 8px 0; font-size: 17px; }}
  .review ul {{ margin: 0; padding-right: 20px; }}
  .ok {{ color: #166534; font-weight: 700; }}
  .footer {{
    margin-top: 18px;
    color: #6b7280;
    font-size: 12px;
    text-align: center;
  }}
  .internal {{ display: none; }}
  @media print {{
    body {{ background: #fff; }}
    .page {{ width: auto; min-height: auto; padding: 0; }}
  }}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <h1 class="brand">نشرة أسعار اليوم</h1>
    <div class="meta">
      <span class="pill">التاريخ: {html.escape(report_date.isoformat())}</span>
      <span class="pill">سعر الصرف: {html.escape(syp_money(exchange_rate))}</span>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title">نشرة الدولار</h2>
    <table>
      <thead><tr><th>الصنف</th><th>الوحدة</th><th>السعر بالدولار</th></tr></thead>
      <tbody>{usd_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2 class="section-title">نشرة السوري</h2>
    <table>
      <thead><tr><th>الصنف</th><th>الوحدة</th><th>السعر بالليرة السورية</th></tr></thead>
      <tbody>{syp_rows}</tbody>
    </table>
  </div>

  <div class="review">
    <h2>مراجعة داخلية قبل النشر</h2>
    {review_html}
  </div>

  <div class="footer">
    الأسعار قابلة للتغيير حسب التوفر وسعر الصرف. يرجى التأكد قبل اعتماد الطلب.
  </div>

  <div class="internal">
    Source: {html.escape(str(source_file))} | Generated: {html.escape(generated_at)}
  </div>
</div>
</body>
</html>
"""


def write_pdf_with_browser(html_path: Path, pdf_path: Path) -> bool:
    browser = find_browser_executable()
    if not browser:
        return False
    file_url = html_path.resolve().as_uri()
    command = [
        browser,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={pdf_path}",
        file_url,
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return pdf_path.exists()


def generate_visual_price_list(
    file_path: Path,
    output_dir: Path,
    sheet_name: str,
    report_date: date,
    exchange_rate: float,
    make_pdf: bool,
) -> tuple[Path, Path | None]:
    items, review_items = load_items_from_workbook(file_path, sheet_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / f"price-list-visual-{report_date.isoformat()}.html"
    pdf_path = output_dir / f"price-list-visual-{report_date.isoformat()}.pdf"

    html_content = build_html(items, review_items, report_date, exchange_rate, file_path)
    html_path.write_text(html_content, encoding="utf-8")

    created_pdf: Path | None = None
    if make_pdf:
        if write_pdf_with_browser(html_path, pdf_path):
            created_pdf = pdf_path
    return html_path, created_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a polished HTML/PDF price list from the price workbook.")
    parser.add_argument("--file", required=True, help="Path to the .xlsx/.xlsm price workbook.")
    parser.add_argument("--sheet", default=DEFAULT_SHEET_NAME, help="Worksheet name to read.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Report date in YYYY-MM-DD format.")
    parser.add_argument("--exchange-rate", required=True, type=float, help="USD to SYP exchange rate.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for generated output.")
    parser.add_argument("--pdf", action="store_true", help="Also try to create a PDF using Edge/Chrome headless.")
    args = parser.parse_args()

    html_path, pdf_path = generate_visual_price_list(
        file_path=Path(args.file),
        output_dir=Path(args.output_dir),
        sheet_name=args.sheet,
        report_date=parse_date(args.date),
        exchange_rate=args.exchange_rate,
        make_pdf=args.pdf,
    )
    print(f"Visual HTML price list generated: {html_path}")
    if args.pdf:
        if pdf_path:
            print(f"PDF price list generated: {pdf_path}")
        else:
            print("PDF was not generated automatically. Open the HTML file and use Print > Save as PDF.")
    print("Original Excel file was not modified.")


if __name__ == "__main__":
    main()
