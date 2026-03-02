from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
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


class POSWindow(QWidget):
    sale_completed = Signal()

    def __init__(self, db: Database, printer: ReceiptPrinter) -> None:
        super().__init__()
        self.db = db
        self.printer = printer
        self.cart: dict[int, dict[str, float | int | str]] = {}

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar produto...")

        self.products_table = QTableWidget(0, 3)
        self.products_table.setHorizontalHeaderLabels(["ID", "Nome", "Preço"])
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)

        btn_add = QPushButton("Adicionar")

        self.cart_table = QTableWidget(0, 5)
        self.cart_table.setHorizontalHeaderLabels(["ID", "Nome", "Qtd", "Unitário", "Subtotal"])
        self.cart_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)

        btn_plus = QPushButton("+")
        btn_minus = QPushButton("-")
        btn_remove = QPushButton("Remover")
        self.btn_finish = QPushButton("Finalizar Venda (Enter)")

        self.total_label = QLabel("Total: R$ 0.00")
        self.total_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        layout = QVBoxLayout(self)
        search_row = QHBoxLayout()
        search_row.addWidget(self.search_input)
        search_row.addWidget(btn_add)
        layout.addLayout(search_row)
        layout.addWidget(self.products_table)
        layout.addWidget(QLabel("Carrinho:"))
        layout.addWidget(self.cart_table)

        cart_actions = QHBoxLayout()
        cart_actions.addWidget(btn_plus)
        cart_actions.addWidget(btn_minus)
        cart_actions.addWidget(btn_remove)
        cart_actions.addStretch(1)
        cart_actions.addWidget(self.total_label)
        layout.addLayout(cart_actions)
        layout.addWidget(self.btn_finish)

        self.search_input.textChanged.connect(self.load_products)
        btn_add.clicked.connect(self.add_selected_product)
        self.products_table.itemDoubleClicked.connect(lambda *_: self.add_selected_product())
        btn_plus.clicked.connect(lambda: self.change_qty(1))
        btn_minus.clicked.connect(lambda: self.change_qty(-1))
        btn_remove.clicked.connect(self.remove_item)
        self.btn_finish.clicked.connect(self.finalize_sale)

        self.load_products()

    def load_products(self) -> None:
        products = self.db.list_products(self.search_input.text(), include_inactive=False)
        self.products_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.products_table.setItem(row, 1, QTableWidgetItem(p.nome))
            self.products_table.setItem(row, 2, QTableWidgetItem(f"{p.preco:.2f}"))

        self.products_table.resizeColumnsToContents()

    def add_selected_product(self) -> None:
        row = self.products_table.currentRow()
        if row < 0:
            return
        product_id = int(self.products_table.item(row, 0).text())
        name = self.products_table.item(row, 1).text()
        price = float(self.products_table.item(row, 2).text())

        if product_id not in self.cart:
            self.cart[product_id] = {
                "produto_id": product_id,
                "nome_produto": name,
                "quantidade": 1.0,
                "preco_unitario": price,
                "subtotal": price,
            }
        else:
            self.cart[product_id]["quantidade"] = float(self.cart[product_id]["quantidade"]) + 1
            self.cart[product_id]["subtotal"] = float(self.cart[product_id]["quantidade"]) * price

        self.refresh_cart_table()

    def refresh_cart_table(self) -> None:
        items = list(self.cart.values())
        self.cart_table.setRowCount(len(items))
        total = 0.0

        for row, item in enumerate(items):
            total += float(item["subtotal"])
            self.cart_table.setItem(row, 0, QTableWidgetItem(str(item["produto_id"])))
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(item["nome_produto"])))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"{float(item['quantidade']):.2f}"))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"{float(item['preco_unitario']):.2f}"))
            self.cart_table.setItem(row, 4, QTableWidgetItem(f"{float(item['subtotal']):.2f}"))

        self.cart_table.resizeColumnsToContents()
        self.total_label.setText(f"Total: R$ {total:.2f}")

    def _current_cart_product_id(self) -> int | None:
        row = self.cart_table.currentRow()
        if row < 0:
            return None
        return int(self.cart_table.item(row, 0).text())

    def change_qty(self, delta: float) -> None:
        product_id = self._current_cart_product_id()
        if product_id is None:
            return

        current = float(self.cart[product_id]["quantidade"])
        new_qty = current + delta
        if new_qty <= 0:
            self.cart.pop(product_id)
        else:
            price = float(self.cart[product_id]["preco_unitario"])
            self.cart[product_id]["quantidade"] = new_qty
            self.cart[product_id]["subtotal"] = new_qty * price

        self.refresh_cart_table()

    def remove_item(self) -> None:
        product_id = self._current_cart_product_id()
        if product_id is None:
            return
        self.cart.pop(product_id, None)
        self.refresh_cart_table()

    def finalize_sale(self) -> None:
        if not self.cart:
            QMessageBox.warning(self, "PDV", "Carrinho vazio.")
            return

        datahora = datetime.now().strftime("%d/%m/%Y %H:%M")
        items = list(self.cart.values())

        try:
            sale_id = self.db.create_sale(datahora, items)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar venda: {exc}")
            return

        sale = Sale(id=sale_id, datahora=datahora, total=sum(float(i["subtotal"]) for i in items))
        sale_items = self.db.sale_items(sale_id)

        try:
            self.printer.print_sale(sale, sale_items)
            QMessageBox.information(self, "Venda", f"Venda #{sale_id} finalizada e impressa.")
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Venda salva / impressão falhou",
                f"Venda #{sale_id} salva com sucesso, mas a impressão falhou.\n\nErro: {exc}",
            )

        self.cart.clear()
        self.refresh_cart_table()
        self.sale_completed.emit()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.finalize_sale()
        elif event.key() == Qt.Key_Escape:
            self.products_table.clearSelection()
            self.cart_table.clearSelection()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_F:
            self.search_input.setFocus()
        else:
            super().keyPressEvent(event)
