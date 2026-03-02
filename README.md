# FeiraPDV (Windows, offline)

Sistema simples de PDV para feirinha/mercadinho com:
- Cadastro de produtos
- Cadastro de barraquinhas/vendedores
- Tela de vendas (carrinho + fechamento)
- Impressão térmica ESC/POS
- Geração de recibo em PDF
- Histórico de vendas e reimpressão

## Stack
- Python 3.11+
- PySide6
- SQLite local
- python-escpos
- reportlab
- PyInstaller

## Estrutura

```text
/app
  main.py
  db.py
  models.py
  config.py
  printing.py
  pdf_generator.py
  /ui
    products_window.py
    barraquinhas_window.py
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
- `data/recibos/`
- `logs/app.log`

Também inclui seed opcional com produtos e barraquinhas iniciais.

## Configuração da impressora térmica e PDF

Arquivo: `data/config.json`

Exemplo:

```json
{
  "nome_da_loja": "Feirinha do Murillo",
  "tipo_impressora": "usb",
  "usb_vendor_id": "0x1234",
  "usb_product_id": "0x5678",
  "cortar_papel": true,
  "gerar_pdf_automaticamente": true
}
```

### Campos
- `nome_da_loja`: texto do cabeçalho do recibo
- `tipo_impressora`: `usb` (implementado como principal) ou `win32` (interface preparada)
- `usb_vendor_id` e `usb_product_id`: IDs da impressora USB
- `cortar_papel`: `true/false`
- `gerar_pdf_automaticamente`: se `true`, cria `data/recibos/recibo_venda_<id>.pdf` ao finalizar venda

> Se não houver impressora conectada, a venda é salva mesmo assim e o sistema mostra aviso. Você pode reimprimir no Histórico e também gerar PDF novamente.

## Build para `.exe` (PyInstaller)

Comando exemplo solicitado:

```bash
pyinstaller --noconsole --onefile app/main.py --name FeiraPDV
```

## Atalhos úteis
- `Enter`: finalizar venda (tela PDV)
- `Esc`: limpar seleção
- `Ctrl+F`: focar busca
