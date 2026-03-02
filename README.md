# FeiraPDV (Windows, offline)

Sistema simples de PDV para feirinha/mercadinho com:
- Cadastro de produtos

- Histórico de vendas e reimpressão

## Stack


## Estrutura

```text
/app
  main.py
  db.py
  models.py
  config.py
  printing.py

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


```json
{
  "nome_da_loja": "Feirinha do Murillo",
  "tipo_impressora": "usb",
  "usb_vendor_id": "0x1234",
  "usb_product_id": "0x5678",

}
```

### Campos
- `nome_da_loja`: texto do cabeçalho do recibo
- `tipo_impressora`: `usb` (implementado como principal) ou `win32` (interface preparada)
- `usb_vendor_id` e `usb_product_id`: IDs da impressora USB
- `cortar_papel`: `true/false`


## Build para `.exe` (PyInstaller)

Comando exemplo solicitado:

```bash
pyinstaller --noconsole --onefile app/main.py --name FeiraPDV
```


