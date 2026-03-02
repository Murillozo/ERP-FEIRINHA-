from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict


class AppConfig(TypedDict):
    nome_da_loja: str
    tipo_impressora: str
    usb_vendor_id: str
    usb_product_id: str
    cortar_papel: bool


DEFAULT_CONFIG: AppConfig = {
    "nome_da_loja": "Feirinha do Murillo",
    "tipo_impressora": "usb",
    "usb_vendor_id": "0x0000",
    "usb_product_id": "0x0000",
    "cortar_papel": True,
}


def _merge_with_default(data: dict[str, Any]) -> AppConfig:
    merged = DEFAULT_CONFIG.copy()
    merged.update(data)
    return merged


def load_config(config_path: Path) -> AppConfig:
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        save_config(config_path, DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("config inválida")
        cfg = _merge_with_default(payload)
    except Exception:
        cfg = DEFAULT_CONFIG.copy()
        save_config(config_path, cfg)

    return cfg


def save_config(config_path: Path, config: AppConfig) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
