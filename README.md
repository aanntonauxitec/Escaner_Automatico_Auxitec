# Sistema Automático de Escaneo y Procesamiento de Albaranes

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-latest-green.svg)
![zxingcpp](https://img.shields.io/badge/zxingcpp-Barcode_Scanning-orange.svg)

Sistema de visión y procesamiento de documentos diseñado para automatizar la entrada de albaranes logísticos. El programa intercepta PDFs multipágina generados por un escáner de red, detecta códigos de barras para separar los documentos físicos (bultos), extrae la información clave y genera un archivo Excel (`.xls`) listo para su importación en el ERP Prowin.

## Características Principales

- **Separación lógica de bultos:** Escanea el documento buscando un código de barras separador de 13 ceros (`0000000000000`). Corta el PDF automáticamente manteniendo el orden físico.
- **Extracción de datos:** Lee códigos Code 39 Std y Code 128 para extraer `ALBARAN`, `MATRICULA` (`MAT-...`) y `DESTINO` (`DST-...`).
- **Control de duplicados:** Detecta y marca albaranes duplicados en cualquier punto del lote completo.
- **Cero pérdidas:** Cada folio genera una línea en el Excel. Si la impresión es defectuosa o el papel está en blanco, inyecta la incidencia `FALTA-LEER` u `HOJA ILEGIBLE` para revisión manual.
- **Gestión de archivos:** Mueve los PDFs procesados a un histórico y nombra los Excels dinámicamente según el contenido y la hora.

## Estructura de Directorios

```
Raiz_del_Proyecto/
├── run.py                    # Motor principal
├── run.spec                  # Configuración PyInstaller
├── logo.ico                  # Icono del ejecutable
├── 1_entrada/                # (Input) Bandeja de entrada — mapeada a \\auxifs\Auxitec\13 Escaner
├── 2_bultos_cortados/        # (Temp) PDFs troceados por bulto
├── 3_salida_prowin/          # (Output) Excels listos para ERP
└── 4_historico_originales/   # (Backup) PDFs originales procesados
```

## Requisitos de Hardware y Configuración

- **Escáner:** configurado obligatoriamente a **300 DPI** y Blanco y Negro puro. El programa renderiza internamente a 600 DPI para mayor fiabilidad de lectura.
- **Pegatina separadora:** colocar en la primera hoja de cada bulto físico (barcode de 13 ceros).
- **Calidad de impresión:** tóners en buen estado. El programa incluye un fallback de binarización para impresiones de bajo contraste.

## Instalación y Compilación

1. Clonar el repositorio.

2. Instalar las dependencias de Python (requiere Python 3.12):
   ```bash
   pip install PyMuPDF Pillow zxingcpp PyPDF2 xlwt
   ```

3. Compilar el ejecutable `.exe` para los operarios:
   ```bash
   py -3.12 -m PyInstaller run.spec
   ```
   El resultado queda en `dist/run.exe`.

## Flujo de Uso (Operarios de Almacén)

1. Pegar la etiqueta de 13 ceros en el recuadro superior del primer albarán de cada bulto.
2. Colocar el taco completo en la fotocopiadora Konica y escanear.
3. Hacer doble clic en `run.exe`.
4. Revisar la carpeta `3_salida_prowin` para obtener el Excel. Si la columna `INCIDENCIAS` muestra algún error, revisar físicamente ese bulto.

## Historial de Versiones

| Versión | Descripción |
|---------|-------------|
| V1.0 | Versión estable inicial en producción |
| V1.1 | Motor zxingcpp (reemplaza pyzbar) + lectura a 600 DPI + fallback de binarización |
| V1.1.1 | Fix: `Code39Std` en lugar de `Code39` — evita clasificación errónea de barcodes de albarán como Code 32 (farmacéutico italiano), que producía `A201629704` en lugar del número de albarán correcto |
