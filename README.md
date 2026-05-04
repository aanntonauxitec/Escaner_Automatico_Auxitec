# 📦 Sistema Automático de Escaneo y Procesamiento de Albaranes

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-1.19+-green.svg)
![pyzbar](https://img.shields.io/badge/pyzbar-Barcode_Scanning-orange.svg)

Sistema de visión y procesamiento de documentos diseñado para automatizar la entrada de albaranes logísticos. El programa intercepta PDFs multipágina generados por un escáner de red, detecta códigos de barras para separar los documentos físicos (bultos), extrae la información clave y genera un archivo Excel (`.xls`) listo para su importación en el ERP Prowin.

## 🚀 Características Principales

- **Separación Lógica de Bultos (Fase 1):** Escanea el documento buscando un código de barras separador de 13 ceros (`0000000000000`). Corta el PDF automáticamente manteniendo el orden físico inquebrantable.
- **Extracción de Datos (Fase 2):** Lee códigos Code 128/Code 39 para extraer `ALBARAN`, `MATRICULA` (MAT-...) y `DESTINO` (DST-...).
- **Control de Memoria Global:** Detecta y marca albaranes duplicados en cualquier punto del lote completo.
- **Red de Seguridad (Cero Pérdidas):** Asegura que cada folio físico genere una línea en el Excel. Si la tinta es defectuosa o el papel está en blanco, inyecta la incidencia `FALTA-LEER` u `HOJA ILEGIBLE` para su revisión manual.
- **Gestión de Archivos:** Mueve los PDFs procesados a un histórico y nombra los Excels dinámicamente según el contenido y la hora.

## 🏗️ Estructura de Directorios

El programa generará automáticamente la siguiente estructura de carpetas en su entorno de ejecución si no existen:
```text
📁 Raiz_del_Proyecto/
├── 📄 run.py                 # Orquestador y motor principal
├── 📄 logo.ico               # Icono para el ejecutable (opcional)
├── 📄 README.md              # Documentación del proyecto
├── 📂 13 Escaner/            # (Input) Bandeja de entrada del escáner de red
├── 📂 2_bultos_cortados/     # (Temp) Almacenamiento temporal de PDFs troceados
├── 📂 3_salida_prowin/       # (Output) Excels generados listos para ERP
└── 📂 4_historico_originales/# (Backup) PDFs originales procesados con éxito

⚙️ Requisitos de Hardware y Configuración
Para garantizar una tasa de éxito del 100% en la lectura sin requerir cámaras industriales:

Configuración del Escáner: Debe estar configurado obligatoriamente a 300 DPI y en Blanco y Negro puro (no escala de grises).

Pegatina Separadora: Debe colocarse en la primera hoja de cada bulto físico (formato de 13 ceros).

Calidad de Impresión: Requiere tóners en buen estado.

💻 Instalación y Compilación
Clonar el repositorio.

Instalar las dependencias de Python:

Bash
pip install PyMuPDF Pillow pyzbar PyPDF2 xlwt

3. (Opcional) Compilar el script en un único archivo ejecutable `.exe` para los operarios usando PyInstaller:
   ```bash
   python -m PyInstaller --onefile --collect-all pyzbar --icon=logo.ico run.py
🛠️ Flujo de Uso (Operarios de Almacén)
Pegar la etiqueta de 13 ceros en el recuadro superior del primer albarán de cada bulto.

Colocar el taco completo en la fotocopiadora Konica y escanear.

Hacer doble clic en el archivo run.exe.

Revisar la carpeta 3_salida_prowin para obtener el Excel. Si la columna "INCIDENCIAS" muestra algún error, revisar físicamente ese bulto.