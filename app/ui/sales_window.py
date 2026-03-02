from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.db import Database
from app.models import Sale
from app.pdf_generator import ReceiptPDFGenerator
from app.printing import ReceiptPrinter


class SalesWindow(QWidget):
    def __init__(self, db: Database, printer: ReceiptPrinter, pdf_generator: ReceiptPDFGenerator) -> None:
        super().__init__()
        self.db = db
        self.printer = printer
        self.pdf_generator = pdf_generator
        self.current_sale: Sale | None = None

        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(datetime.now().date())
        self.date_filter.setDisplayFormat("dd/MM/yyyy")

        self.barraquinha_filter = QComboBox()

        btn_filter = QPushButton("Filtrar")
        btn_reprint = QPushButton("Reimprimir Recibo")
        btn_regen_pdf = QPushButton("Gerar PDF novamente")
        btn_delete_sale = QPushButton("Excluir Pedido")

        self.sales_table = QTableWidget(0, 3)
        self.sales_table.setHorizontalHeaderLabels(["Data/Hora", "Barraquinha", "Total"])
        self.sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sales_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.items_table = QTableWidget(0, 4)
        self.items_table.setHorizontalHeaderLabels(["Produto", "Qtd", "Unitário", "Subtotal"])
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)

        top = QHBoxLayout()
        top.addWidget(QLabel("Data:"))
        top.addWidget(self.date_filter)
        top.addWidget(QLabel("Barraquinha:"))
        top.addWidget(self.barraquinha_filter)
        top.addWidget(btn_filter)
        top.addStretch(1)
        top.addWidget(btn_reprint)
        top.addWidget(btn_regen_pdf)
        top.addWidget(btn_delete_sale)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(QLabel("Vendas"))
        layout.addWidget(self.sales_table)
        layout.addWidget(QLabel("Itens da venda"))
        layout.addWidget(self.items_table)

        btn_filter.clicked.connect(self.load_sales)
        self.sales_table.itemSelectionChanged.connect(self.load_sale_items)
        btn_reprint.clicked.connect(self.reprint)
        btn_regen_pdf.clicked.connect(self.regenerate_pdf)
        btn_delete_sale.clicked.connect(self.delete_sale)

        self.load_barraquinhas_filter()
        self.load_sales()

    def load_barraquinhas_filter(self) -> None:
        current = self.barraquinha_filter.currentData()
        self.barraquinha_filter.clear()
        self.barraquinha_filter.addItem("Todas", None)
        for b in self.db.list_barraquinhas(include_inactive=True):
            self.barraquinha_filter.addItem(b.nome, b.id)

        idx = self.barraquinha_filter.findData(current)
        if idx >= 0:
            self.barraquinha_filter.setCurrentIndex(idx)

    def load_sales(self) -> None:
        day = self.date_filter.date().toString("dd/MM/yyyy")
        barraquinha_id = self.barraquinha_filter.currentData()
        sales = self.db.list_sales(day, barraquinha_id)
        self.sales_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            datetime_item = QTableWidgetItem(sale.datahora)
            datetime_item.setData(Qt.UserRole, sale.id)
            self.sales_table.setItem(row, 0, datetime_item)
            self.sales_table.setItem(row, 1, QTableWidgetItem(sale.barraquinha_nome or "N/I"))
            self.sales_table.setItem(row, 2, QTableWidgetItem(f"{sale.total:.2f}"))

        self.sales_table.resizeColumnsToContents()
        self.items_table.setRowCount(0)
        self.current_sale = None

    def load_sale_items(self) -> None:
        row = self.sales_table.currentRow()
        if row < 0:
            return

        sale_id = int(self.sales_table.item(row, 0).data(Qt.UserRole))
        sale = self.db.sale_by_id(sale_id)
        if sale is None:
            return
        self.current_sale = sale

        items = self.db.sale_items(sale_id)
        self.items_table.setRowCount(len(items))
        for idx, item in enumerate(items):
            self.items_table.setItem(idx, 0, QTableWidgetItem(item.nome_produto))
            self.items_table.setItem(idx, 1, QTableWidgetItem(f"{item.quantidade:.2f}"))
            self.items_table.setItem(idx, 2, QTableWidgetItem(f"{item.preco_unitario:.2f}"))
            self.items_table.setItem(idx, 3, QTableWidgetItem(f"{item.subtotal:.2f}"))

        self.items_table.resizeColumnsToContents()

    def reprint(self) -> None:
        if self.current_sale is None:
            QMessageBox.warning(self, "Histórico", "Selecione uma venda.")
            return

        items = self.db.sale_items(self.current_sale.id)
        try:
            self.printer.print_sale(self.current_sale, items)
            QMessageBox.information(self, "Histórico", "Recibo reimpresso com sucesso.")
        except Exception as exc:
            QMessageBox.warning(self, "Histórico", f"Falha na impressão: {exc}")

    def delete_sale(self) -> None:
        if self.current_sale is None:
            QMessageBox.warning(self, "Histórico", "Selecione uma venda.")
            return

        confirm = QMessageBox.question(
            self,
            "Excluir Pedido",
            f"Tem certeza que deseja excluir o pedido #{self.current_sale.id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            self.db.delete_sale(self.current_sale.id)
            self.load_sales()
            QMessageBox.information(self, "Histórico", "Pedido excluído com sucesso.")
        except Exception as exc:
            QMessageBox.warning(self, "Histórico", f"Falha ao excluir pedido: {exc}")

    def regenerate_pdf(self) -> None:
        if self.current_sale is None:
            QMessageBox.warning(self, "Histórico", "Selecione uma venda.")
            return
        items = self.db.sale_items(self.current_sale.id)
        try:
            path = self.pdf_generator.generate_sale_pdf(self.current_sale, items)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            QMessageBox.information(self, "Histórico", f"PDF gerado: {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Histórico", f"Falha ao gerar PDF: {exc}")

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key_Escape:
            self.sales_table.clearSelection()
            self.items_table.clearSelection()
        else:
            super().keyPressEvent(event)
