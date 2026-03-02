from __future__ import annotations

import logging
from typing import Iterable

from .config import AppConfig
from .models import Sale, SaleItem

try:
    from escpos.printer import Usb
except Exception:  # pragma: no cover - fallback em ambiente sem lib
    Usb = None

try:
    from escpos.printer.win32raw import Win32Raw
except Exception:  # pragma: no cover
    Win32Raw = None


logger = logging.getLogger(__name__)


def _parse_hex(value: str) -> int:
    value = value.strip().lower()
    if value.startswith("0x"):
        return int(value, 16)
    return int(value)


def _cut_name(name: str, size: int = 20) -> str:
    return name if len(name) <= size else f"{name[:size-1]}…"


class ReceiptPrinter:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def print_sale(self, sale: Sale, items: Iterable[SaleItem]) -> None:
        printer_type = self.config.get("tipo_impressora", "usb")
        printer = None
        if printer_type == "usb":
            if Usb is None:
                raise RuntimeError("python-escpos não está disponível para USB.")
            vendor_id = _parse_hex(self.config.get("usb_vendor_id", "0x0000"))
            product_id = _parse_hex(self.config.get("usb_product_id", "0x0000"))
            printer = Usb(vendor_id, product_id, timeout=0, in_ep=0x82, out_ep=0x01)
        elif printer_type == "win32":
            if Win32Raw is None:
                raise RuntimeError("Modo win32 não disponível nesta instalação.")
            printer_name = self.config.get("printer_name", "")
            if not printer_name:
                raise RuntimeError("Defina printer_name no config para usar modo win32.")
            printer = Win32Raw(printer_name)
        else:
            raise RuntimeError("tipo_impressora inválido. Use 'usb' ou 'win32'.")

        logger.info("Imprimindo recibo da venda %s", sale.id)
        printer.set(align="center", bold=True, width=2, height=2)
        printer.text(f"{self.config['nome_da_loja']}\n")
        printer.set(align="left", bold=False, width=1, height=1)
        printer.text("-" * 32 + "\n")

        for item in items:
            name = _cut_name(item.nome_produto, 20)
            printer.text(f"{name}\n")
            if item.barraquinha_nome:
                printer.text(f"  [{_cut_name(item.barraquinha_nome, 20)}]\n")
            printer.text(
                f" {item.quantidade:.2f} x {item.preco_unitario:>.2f}"
                f" = {item.subtotal:>.2f}\n"
            )

        printer.text("-" * 32 + "\n")
        printer.set(bold=True, align="right", width=2, height=2)
        printer.text(f"TOTAL: R$ {sale.total:.2f}\n")
        printer.set(bold=False, align="left", width=1, height=1)
        printer.text(f"Data/Hora: {sale.datahora}\n")
        printer.text(f"Barraquinha: {sale.barraquinha_nome or 'N/I'}\n")
        printer.set(align="center")
        printer.text("Obrigado!\n\n")

        if self.config.get("cortar_papel", True):
            printer.cut()
        else:
            printer.text("\n\n\n")

        printer.close()
