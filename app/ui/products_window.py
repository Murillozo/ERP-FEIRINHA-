from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
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


class ProductsWindow(QWidget):
    products_changed = Signal()

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_id: int | None = None

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar produto por nome...")

        self.nome_input = QLineEdit()
        self.preco_input = QLineEdit()
        self.ativo_checkbox = QCheckBox("Ativo")
        self.ativo_checkbox.setChecked(True)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Preço", "Ativo"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        btn_new = QPushButton("Novo")
        btn_save = QPushButton("Salvar")
        btn_remove = QPushButton("Desativar")

        form = QFormLayout()
        form.addRow(QLabel("Nome:"), self.nome_input)
        form.addRow(QLabel("Preço (R$):"), self.preco_input)
        form.addRow(QLabel("Status:"), self.ativo_checkbox)

        top = QHBoxLayout()
        top.addWidget(self.search_input)

        actions = QHBoxLayout()
        actions.addWidget(btn_new)
        actions.addWidget(btn_save)
        actions.addWidget(btn_remove)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table)
        layout.addLayout(form)
        layout.addLayout(actions)

        self.search_input.textChanged.connect(self.load_products)
        self.table.itemSelectionChanged.connect(self._on_table_select)
        btn_new.clicked.connect(self.clear_form)
        btn_save.clicked.connect(self.save_product)
        btn_remove.clicked.connect(self.deactivate_product)

        self.load_products()

    def load_products(self) -> None:
        products = self.db.list_products(self.search_input.text(), include_inactive=True)
        self.table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.table.setItem(row, 1, QTableWidgetItem(p.nome))
            self.table.setItem(row, 2, QTableWidgetItem(f"{p.preco:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem("Sim" if p.ativo else "Não"))

        self.table.resizeColumnsToContents()

    def _on_table_select(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        self.selected_id = int(self.table.item(row, 0).text())
        self.nome_input.setText(self.table.item(row, 1).text())
        self.preco_input.setText(self.table.item(row, 2).text())
        self.ativo_checkbox.setChecked(self.table.item(row, 3).text() == "Sim")

    def _validate_form(self) -> tuple[bool, float]:
        nome = self.nome_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Validação", "Nome é obrigatório.")
            return False, 0.0

        try:
            preco = float(self.preco_input.text().replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Validação", "Preço inválido.")
            return False, 0.0

        if preco < 0:
            QMessageBox.warning(self, "Validação", "Preço deve ser maior ou igual a zero.")
            return False, 0.0

        return True, preco

    def save_product(self) -> None:
        valid, preco = self._validate_form()
        if not valid:
            return

        nome = self.nome_input.text().strip()
        ativo = self.ativo_checkbox.isChecked()
        try:
            if self.selected_id is None:
                self.db.create_product(nome, preco, ativo)
            else:
                self.db.update_product(self.selected_id, nome, preco, ativo)

            self.load_products()
            self.products_changed.emit()
            QMessageBox.information(self, "Sucesso", "Produto salvo com sucesso.")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar: {exc}")

    def deactivate_product(self) -> None:
        if self.selected_id is None:
            QMessageBox.warning(self, "Atenção", "Selecione um produto.")
            return
        try:
            self.db.deactivate_product(self.selected_id)
            self.load_products()
            self.products_changed.emit()
            QMessageBox.information(self, "Sucesso", "Produto desativado.")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao desativar: {exc}")

    def clear_form(self) -> None:
        self.selected_id = None
        self.nome_input.clear()
        self.preco_input.clear()
        self.ativo_checkbox.setChecked(True)
        self.table.clearSelection()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key_Escape:
            self.clear_form()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_F:
            self.search_input.setFocus()
        else:
            super().keyPressEvent(event)
