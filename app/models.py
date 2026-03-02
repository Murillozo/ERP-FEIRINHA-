from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Product:
    id: int
    nome: str
    preco: float
    ativo: bool = True


@dataclass
class Sale:
    id: int
    datahora: str
    total: float


@dataclass
class SaleItem:
    id: int
    venda_id: int
    produto_id: int
    nome_produto: str
    quantidade: float
    preco_unitario: float
    subtotal: float
