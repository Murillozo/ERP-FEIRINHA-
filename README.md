# FeiraPDV (Windows, offline)

Sistema simples de PDV para feirinha/mercadinho com:
- Cadastro de produtos
- Tela de vendas (carrinho + fechamento)
- Impressão térmica ESC/POS
- Histórico de vendas e reimpressão

## Stack
- Python 3.11+
- PySide6
- SQLite local
- python-escpos
- PyInstaller

## Estrutura

```text
/app
  main.py
  db.py
  models.py
  config.py
  printing.py
  /ui
    products_window.py
    pos_window.py
    sales_window.py
/assets
requirements.txt
README.md
```

## Instalação

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Como rodar

```bash
python -m app.main
```

Na primeira execução o sistema cria automaticamente:
- `data/pdv.sqlite`
- `data/config.json`
- `logs/app.log`

Também inclui seed opcional com 10 produtos iniciais.

## Configuração da impressora térmica

Arquivo: `data/config.json`

Exemplo (USB principal):

```json
{
  "nome_da_loja": "Feirinha do Murillo",
  "tipo_impressora": "usb",
  "usb_vendor_id": "0x1234",
  "usb_product_id": "0x5678",
  "cortar_papel": true
}
```

### Campos
- `nome_da_loja`: texto do cabeçalho do recibo
- `tipo_impressora`: `usb` (implementado como principal) ou `win32` (interface preparada)
- `usb_vendor_id` e `usb_product_id`: IDs da impressora USB
- `cortar_papel`: `true/false`

> Se não houver impressora conectada, a venda é salva mesmo assim e o sistema mostra aviso. Você pode reimprimir no Histórico.

## Build para `.exe` (PyInstaller)

Comando exemplo solicitado:

```bash
pyinstaller --noconsole --onefile app/main.py --name FeiraPDV
```

Opcional (ícone):

```bash
pyinstaller --noconsole --onefile app/main.py --name FeiraPDV --icon assets/icon.ico
```

## Atalhos úteis
- `Enter`: finalizar venda (tela PDV)
- `Esc`: limpar seleção
- `Ctrl+F`: focar busca

