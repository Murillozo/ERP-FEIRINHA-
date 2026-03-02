from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import Product, Sale, SaleItem


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS produtos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    preco REAL NOT NULL,
                    ativo INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS vendas(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    datahora TEXT NOT NULL,
                    total REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS itens_venda(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venda_id INTEGER NOT NULL,
                    produto_id INTEGER NOT NULL,
                    nome_produto TEXT NOT NULL,
                    quantidade REAL NOT NULL,
                    preco_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY(venda_id) REFERENCES vendas(id)
                );
                """
            )
            self._seed_products(conn)

    def _seed_products(self, conn: sqlite3.Connection) -> None:
        count = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        if count > 0:
            return

        seed = [
            ("Tomate", 6.99),
            ("Cebola", 4.50),
            ("Batata", 5.20),
            ("Banana", 4.99),
            ("Maçã", 8.90),
            ("Arroz 5kg", 28.00),
            ("Feijão 1kg", 7.50),
            ("Açúcar 1kg", 4.20),
            ("Café 500g", 15.90),
            ("Leite 1L", 4.80),
        ]
        conn.executemany(
            "INSERT INTO produtos(nome, preco, ativo) VALUES (?, ?, 1)",
            seed,
        )

    def list_products(self, search: str = "", include_inactive: bool = False) -> list[Product]:
        where = "WHERE 1=1"
        params: list[object] = []
        if search:
            where += " AND nome LIKE ?"
            params.append(f"%{search}%")
        if not include_inactive:
            where += " AND ativo = 1"

        query = f"SELECT id, nome, preco, ativo FROM produtos {where} ORDER BY nome"
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Product(id=r["id"], nome=r["nome"], preco=r["preco"], ativo=bool(r["ativo"])) for r in rows]

    def create_product(self, nome: str, preco: float, ativo: bool = True) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO produtos(nome, preco, ativo) VALUES (?, ?, ?)",
                (nome.strip(), preco, int(ativo)),
            )

    def update_product(self, product_id: int, nome: str, preco: float, ativo: bool) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE produtos SET nome=?, preco=?, ativo=? WHERE id=?",
                (nome.strip(), preco, int(ativo), product_id),
            )

    def deactivate_product(self, product_id: int) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE produtos SET ativo=0 WHERE id=?", (product_id,))

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            conn.execute("BEGIN")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_sale(self, datahora: str, items: list[dict[str, float | int | str]]) -> int:
        total = float(sum(float(item["subtotal"]) for item in items))

        with self.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO vendas(datahora, total) VALUES (?, ?)",
                (datahora, total),
            )
            venda_id = int(cur.lastrowid)
            for item in items:
                conn.execute(
                    """
                    INSERT INTO itens_venda(
                        venda_id, produto_id, nome_produto, quantidade, preco_unitario, subtotal
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        venda_id,
                        int(item["produto_id"]),
                        str(item["nome_produto"]),
                        float(item["quantidade"]),
                        float(item["preco_unitario"]),
                        float(item["subtotal"]),
                    ),
                )
        return venda_id

    def list_sales(self, date_prefix: str | None = None) -> list[Sale]:
        where = ""
        params: list[str] = []
        if date_prefix:
            where = "WHERE datahora LIKE ?"
            params.append(f"{date_prefix}%")

        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT id, datahora, total FROM vendas {where} ORDER BY id DESC",
                params,
            ).fetchall()
        return [Sale(id=r["id"], datahora=r["datahora"], total=r["total"]) for r in rows]

    def sale_items(self, venda_id: int) -> list[SaleItem]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, venda_id, produto_id, nome_produto, quantidade, preco_unitario, subtotal
                FROM itens_venda
                WHERE venda_id = ?
                ORDER BY id
                """,
                (venda_id,),
            ).fetchall()
        return [
            SaleItem(
                id=r["id"],
                venda_id=r["venda_id"],
                produto_id=r["produto_id"],
                nome_produto=r["nome_produto"],
                quantidade=r["quantidade"],
                preco_unitario=r["preco_unitario"],
                subtotal=r["subtotal"],
            )
            for r in rows
        ]

    def sale_by_id(self, venda_id: int) -> Sale | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, datahora, total FROM vendas WHERE id=?",
                (venda_id,),
            ).fetchone()
        if row is None:
            return None
        return Sale(id=row["id"], datahora=row["datahora"], total=row["total"])
