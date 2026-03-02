from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Iterable

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .config import AppConfig
from .models import Sale, SaleItem


def _cut_name(name: str, size: int = 35) -> str:
    return name if len(name) <= size else f"{name[:size-1]}…"


def _group_items_by_barraquinha(items: list[SaleItem]) -> list[tuple[str, list[SaleItem]]]:
    grouped: OrderedDict[str, list[SaleItem]] = OrderedDict()
    for item in items:
        group_name = item.barraquinha_nome or "Sem barraquinha"
        grouped.setdefault(group_name, []).append(item)
    return list(grouped.items())


class ReceiptPDFGenerator:
    def __init__(self, config: AppConfig, output_dir: Path) -> None:
        self.config = config
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_sale_pdf(self, sale: Sale, items: Iterable[SaleItem]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.output_dir / f"recibo_venda_{sale.id}.pdf"

        receipt_width_mm = int(self.config.get("largura_recibo_mm", 80))
        if receipt_width_mm not in (58, 80):
            receipt_width_mm = 80

        item_list = list(items)
        grouped_items = _group_items_by_barraquinha(item_list)
        group_headers = len(grouped_items)
        group_subtotals = len(grouped_items)
        line_count = 8 + (2 * len(item_list)) + group_headers + group_subtotals
        page_height = max(100, 20 + line_count * 6) * mm
        receipt_width = receipt_width_mm * mm

        c = canvas.Canvas(str(filepath), pagesize=(receipt_width, page_height))

        left = 2 * mm
        y = page_height - 8 * mm

        def line(text: str, bold: bool = False, size: int = 10) -> None:
            nonlocal y
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            c.drawString(left, y, text)
            y -= 6 * mm

        line("RECIBO", bold=True, size=13)
        line("-" * 45)

        for index, (group_name, group_items) in enumerate(grouped_items, start=1):
            line(f"Grupo {index:02d} - {_cut_name(group_name)}", bold=True, size=10)
            group_total = 0.0
            for item in group_items:
                line(_cut_name(item.nome_produto), bold=True)
                line(
                    f"{item.quantidade:.2f} x R$ {item.preco_unitario:.2f}"
                    f" = R$ {item.subtotal:.2f}",
                    size=10,
                )
                group_total += float(item.subtotal)
            line(f"Subtotal grupo: R$ {group_total:.2f}", size=9)

        line("-" * 45)
        line(f"TOTAL: R$ {sale.total:.2f}", bold=True, size=12)
        line(f"Data/Hora: {sale.datahora}")
        line(f"Barraquinha: {sale.barraquinha_nome or 'Não informada'}")
        line("Obrigado pela preferência", bold=True)

        c.showPage()
        c.save()
        return filepath
