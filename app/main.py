from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTabWidget

from app.config import load_config
from app.db import Database
from app.pdf_generator import ReceiptPDFGenerator
from app.printing import ReceiptPrinter
from app.ui.barraquinhas_window import BarraquinhasWindow
from app.ui.pos_window import POSWindow
from app.ui.products_window import ProductsWindow
from app.ui.sales_window import SalesWindow


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
RECIBOS_DIR = DATA_DIR / "recibos"
CONFIG_PATH = DATA_DIR / "config.json"
DB_PATH = DATA_DIR / "pdv.sqlite"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Feira PDV")
        self.resize(1200, 760)

        config = load_config(CONFIG_PATH)
        db = Database(DB_PATH)

        try:
            db.initialize()
        except Exception as exc:
            QMessageBox.critical(self, "Erro fatal", f"Falha ao iniciar banco: {exc}")
            raise

        printer = ReceiptPrinter(config)
        pdf_generator = ReceiptPDFGenerator(config, RECIBOS_DIR)

        tabs = QTabWidget()
        self.products = ProductsWindow(db)
        self.barraquinhas = BarraquinhasWindow(db)
        self.pos = POSWindow(db, printer, pdf_generator, config)
        self.sales = SalesWindow(db, printer, pdf_generator)

        tabs.addTab(self.pos, "PDV")
        tabs.addTab(self.products, "Produtos")
        tabs.addTab(self.barraquinhas, "Barraquinhas")
        tabs.addTab(self.sales, "Histórico")
        self.setCentralWidget(tabs)

        self.products.products_changed.connect(self.pos.load_products)
        self.barraquinhas.barraquinhas_changed.connect(self.pos.load_barraquinhas)
        self.barraquinhas.barraquinhas_changed.connect(self.sales.load_barraquinhas_filter)
        self.pos.sale_completed.connect(self.sales.load_sales)


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_DIR / "app.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
