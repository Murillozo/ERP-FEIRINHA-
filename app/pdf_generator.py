from __future__ import annotations

from pathlib import Path
from typing import Iterable

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .config import AppConfig
from .models import Sale, SaleItem


def _cut_name(name: str, size: int = 35) -> str:
    return name if len(name) <= size else f"{name[:size-1]}…"


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
        line_count = 8 + (2 * len(item_list))
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

        for item in item_list:
            line(_cut_name(item.nome_produto), bold=True)
            line(
                f"{item.quantidade:.2f} x R$ {item.preco_unitario:.2f}"
                f" = R$ {item.subtotal:.2f}",
                size=10,
            )

        line("-" * 45)
        line(f"TOTAL: R$ {sale.total:.2f}", bold=True, size=12)
        line(f"Data/Hora: {sale.datahora}")
        line(f"Barraquinha: {sale.barraquinha_nome or 'Não informada'}")
        line("Obrigado pela preferência", bold=True)

        c.showPage()
        c.save()
        return filepath
