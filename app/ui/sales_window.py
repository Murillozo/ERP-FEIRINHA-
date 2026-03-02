from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
from app.printing import ReceiptPrinter


class SalesWindow(QWidget):
    def __init__(self, db: Database, printer: ReceiptPrinter) -> None:
        super().__init__()
        self.db = db
        self.printer = printer
        self.current_sale: Sale | None = None

        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(datetime.now().date())
        self.date_filter.setDisplayFormat("dd/MM/yyyy")

        btn_filter = QPushButton("Filtrar")
        btn_reprint = QPushButton("Reimprimir Recibo")

        self.sales_table = QTableWidget(0, 3)
        self.sales_table.setHorizontalHeaderLabels(["ID", "Data/Hora", "Total"])
        self.sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sales_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.items_table = QTableWidget(0, 4)
        self.items_table.setHorizontalHeaderLabels(["Produto", "Qtd", "Unitário", "Subtotal"])
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)

        top = QHBoxLayout()
        top.addWidget(QLabel("Data:"))
        top.addWidget(self.date_filter)
        top.addWidget(btn_filter)
        top.addStretch(1)
        top.addWidget(btn_reprint)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(QLabel("Vendas"))
        layout.addWidget(self.sales_table)
        layout.addWidget(QLabel("Itens da venda"))
        layout.addWidget(self.items_table)

        btn_filter.clicked.connect(self.load_sales)
        self.sales_table.itemSelectionChanged.connect(self.load_sale_items)
        btn_reprint.clicked.connect(self.reprint)

        self.load_sales()

    def load_sales(self) -> None:
        day = self.date_filter.date().toString("dd/MM/yyyy")
        sales = self.db.list_sales(day)
        self.sales_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            self.sales_table.setItem(row, 0, QTableWidgetItem(str(sale.id)))
            self.sales_table.setItem(row, 1, QTableWidgetItem(sale.datahora))
            self.sales_table.setItem(row, 2, QTableWidgetItem(f"{sale.total:.2f}"))

        self.sales_table.resizeColumnsToContents()
        self.items_table.setRowCount(0)
        self.current_sale = None

    def load_sale_items(self) -> None:
        row = self.sales_table.currentRow()
        if row < 0:
            return

        sale_id = int(self.sales_table.item(row, 0).text())
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

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key_Escape:
            self.sales_table.clearSelection()
            self.items_table.clearSelection()
        else:
            super().keyPressEvent(event)
