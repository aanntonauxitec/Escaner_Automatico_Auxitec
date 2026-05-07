# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sistema automático de escaneo y procesamiento de albaranes logísticos para Auxitec. Toma PDFs escaneados desde una carpeta de red, los divide por bultos usando códigos de barras separadores, extrae datos (albarán, matrícula, destino) y genera un Excel para importar en el ERP Prowin.

## Commands

**Run in development:**
```bash
py -3.12 run.py
```

**Build standalone executable for operators:**
```bash
py -3.12 -m PyInstaller run.spec
# Output: dist/run.exe
```

**Install dependencies:**
```bash
pip install PyMuPDF Pillow zxingcpp PyPDF2 xlwt
```

There is no test suite. Manual testing is done by placing PDFs in `1_entrada/` and running `py -3.12 run.py`.

## Architecture

All logic lives in a single file: `run.py`. The processing pipeline is orchestrated by `procesar_bandeja_entrada()`:

**Phase 1 – Split:** Reads PDFs from the network share (`\\auxifs\Auxitec\13 Escaner`). Renders each page at 600 DPI grayscale via `hay_pegatina_separadora()`, scans for barcodes via `zxingcpp`. A barcode containing at least 7 zeros (`"0000000" in data`) marks the start of a new shipment (bulto). Splits the source PDF into per-bulto PDFs saved to `2_bultos_cortados/`.

**Phase 2 – Extract:** Reads each split PDF via `extraer_datos_pagina()`, decodes barcodes on every page. Looks for three barcode types: plain number (≤9 digits) → `ALBARAN`, `MAT-` prefix → `MATRICULA`, `DST-` prefix → `DESTINO`. A global set deduplicates albaranes across the entire batch. Pages with unreadable or missing barcodes get incident flags: `FALTA-LEER`, `HOJA ILEGIBLE / EN BLANCO`, `DUPLICADO`, `REVISAR ALBARAN`.

**Phase 3 – Output:** Writes a `.xls` file to `3_salida_prowin/` using `xlwt`. Filename pattern: `{destino} {primer_albaran} TOT{n_paginas} {timestamp}.xls`. Columns: ALBARAN, MATRICULA, DESTINO, BULTO, INCIDENCIAS. Appends an end-of-batch marker row. Moves the original source PDF to `4_historico_originales/`.

## Key Constraints

- **Rendering at 600 DPI** grayscale with binarization fallback — hardcoded in both `hay_pegatina_separadora` and `extraer_datos_pagina`.
- **`FORMATOS_BARCODE` uses `Code39Std` (not `Code39`)** — critical. Generic `Code39` causes zxingcpp to misidentify some valid Code 39 barcodes as Code 32 (Italian Pharmacode), returning e.g. `A201629704` instead of `609808`. `Code39Std` forces strict Code 39 interpretation. No Auxitec barcode is Code 32.
- **Separator barcode**: EAN-13 or similar format containing at least 7 zeros. Detected in `hay_pegatina_separadora` without format filter (reads all formats).
- **Excel output is `.xls`** (legacy xlwt format), not `.xlsx`, because Prowin ERP requires it.
- **`zxingcpp` binary** is bundled via `run.spec` (explicit `binaries` entry pointing to the `.pyd` file). Do not use `--collect-all pyzbar`; the library is now `zxingcpp`, not `pyzbar`.
- **All folder paths are relative** to the script location so the `.exe` works when placed on the operator's desktop.
- **Python 3.12** is the version with all dependencies installed (`py -3.12`). Python 3.14 is also present but lacks the libraries.
- All user-facing messages are in Spanish.

## Diagnostic Tools (temporary, not for production)

- `diagnostico_pdf.py` — prints barcode detection results page by page with format, value, and program diagnosis.
- `diagnostico_visual.py` — same but saves annotated PNG images with bounding boxes per page to `diagnostico_imagenes/`.

Run with: `py -3.12 diagnostico_pdf.py "path\to\file.pdf"`
