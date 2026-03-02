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


class BarraquinhasWindow(QWidget):
    barraquinhas_changed = Signal()

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_id: int | None = None

        self.nome_input = QLineEdit()
        self.ativo_checkbox = QCheckBox("Ativa")
        self.ativo_checkbox.setChecked(True)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "Ativa"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        btn_new = QPushButton("Nova")
        btn_save = QPushButton("Salvar")
        btn_toggle = QPushButton("Ativar/Desativar")

        form = QFormLayout()
        form.addRow(QLabel("Nome:"), self.nome_input)
        form.addRow(QLabel("Status:"), self.ativo_checkbox)

        actions = QHBoxLayout()
        actions.addWidget(btn_new)
        actions.addWidget(btn_save)
        actions.addWidget(btn_toggle)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addLayout(form)
        layout.addLayout(actions)

        self.table.itemSelectionChanged.connect(self._on_table_select)
        btn_new.clicked.connect(self.clear_form)
        btn_save.clicked.connect(self.save_barraquinha)
        btn_toggle.clicked.connect(self.toggle_active)

        self.load_barraquinhas()

    def load_barraquinhas(self) -> None:
        data = self.db.list_barraquinhas(include_inactive=True)
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.id)))
            self.table.setItem(row, 1, QTableWidgetItem(item.nome))
            self.table.setItem(row, 2, QTableWidgetItem("Sim" if item.ativo else "Não"))
        self.table.resizeColumnsToContents()

    def _on_table_select(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        self.selected_id = int(self.table.item(row, 0).text())
        self.nome_input.setText(self.table.item(row, 1).text())
        self.ativo_checkbox.setChecked(self.table.item(row, 2).text() == "Sim")

    def save_barraquinha(self) -> None:
        nome = self.nome_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Validação", "Nome da barraquinha é obrigatório.")
            return
        ativo = self.ativo_checkbox.isChecked()

        try:
            if self.selected_id is None:
                self.db.create_barraquinha(nome, ativo)
            else:
                self.db.update_barraquinha(self.selected_id, nome, ativo)
            self.load_barraquinhas()
            self.barraquinhas_changed.emit()
            QMessageBox.information(self, "Sucesso", "Barraquinha salva com sucesso.")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar barraquinha: {exc}")

    def toggle_active(self) -> None:
        if self.selected_id is None:
            QMessageBox.warning(self, "Atenção", "Selecione uma barraquinha.")
            return
        try:
            is_active = self.ativo_checkbox.isChecked()
            self.db.set_barraquinha_active(self.selected_id, not is_active)
            self.load_barraquinhas()
            self.barraquinhas_changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao alterar status: {exc}")

    def clear_form(self) -> None:
        self.selected_id = None
        self.nome_input.clear()
        self.ativo_checkbox.setChecked(True)
        self.table.clearSelection()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key_Escape:
            self.clear_form()
        else:
            super().keyPressEvent(event)
