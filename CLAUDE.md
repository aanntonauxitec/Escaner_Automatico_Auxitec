# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sistema automático de escaneo y procesamiento de albaranes logísticos para Auxitec. Toma PDFs escaneados desde una carpeta de red, los divide por bultos usando códigos de barras separadores, extrae datos (albarán, matrícula, destino) y genera un Excel para importar en el ERP Prowin.

## Commands

**Run in development:**
```bash
python run.py
```

**Build standalone executable for operators:**
```bash
python -m PyInstaller --onefile --collect-all pyzbar --icon=logo.ico run.py
# Output: dist/run.exe
```

**Install dependencies:**
```bash
pip install PyMuPDF Pillow pyzbar PyPDF2 xlwt
```

There is no test suite. Manual testing is done by placing PDFs in `1_entrada/` and running `python run.py`.

## Architecture

All logic lives in a single file: `run.py`. The processing pipeline runs in three phases:

**Phase 1 – Split (`cortar_bultos`):** Reads PDFs from `1_entrada/` (mapped to network share `\\auxifs\Auxitec\13 Escaner`). Renders each page at 300 DPI, scans for barcodes via `pyzbar`. A barcode string of 13 zeros (`0000000000000`) on the first page marks the start of a new shipment (bulto). Splits the source PDF into per-bulto PDFs saved to `2_bultos_cortados/`.

**Phase 2 – Extract (`procesar_bultos`):** Reads each split PDF, decodes barcodes on every page. Looks for three barcode types by prefix: plain number → `ALBARAN`, `MAT-` → `MATRICULA`, `DST-` → `DESTINO`. A global set `todos_los_albaranes` deduplicates invoices across the entire batch session. Pages with unreadable or missing barcodes get incident flags: `FALTA-LEER`, `HOJA ILEGIBLE / EN BLANCO`, `DUPLICADO`, `REVISAR ALBARAN`.

**Phase 3 – Output (`generar_excel`):** Writes a `.xls` file to `3_salida_prowin/` using `xlwt`. Filename pattern: `{destino} {primer_albaran} TOT{n_paginas} {timestamp}.xls`. Columns: ALBARAN, MATRICULA, DESTINO, BULTO, INCIDENCIAS. Appends an end-of-batch marker row. Moves the original source PDF to `4_historico_originales/`.

## Key Constraints

- **Input PDFs must be scanned at 300 DPI**, black & white — hardcoded rendering assumption.
- **Separator barcode must be Code 128 or Code 39** containing at least 7 zeros; detected by `"0000000" in data`.
- **Excel output is `.xls`** (legacy xlwt format), not `.xlsx`, because Prowin ERP requires it.
- **`pyzbar` requires `zbar` native library** — the PyInstaller build uses `--collect-all pyzbar` to bundle it.
- **All folder paths are relative** to the script location so the `.exe` works when placed on the operator's desktop.
- All user-facing messages are in Spanish.
