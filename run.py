import os
import shutil
import time
import sys

# ==========================================
# CINTURÓN DE SEGURIDAD PARA ARRANQUE
# ==========================================
try:
    import fitz  # PyMuPDF
    from PIL import Image
    import zxingcpp
    from PyPDF2 import PdfReader, PdfWriter
    import re
    from datetime import datetime
    import xlwt
except Exception as e:
    print("\n=======================================================")
    print(" [!] ERROR CRÍTICO AL ARRANCAR EL MOTOR DEL PROGRAMA")
    print("=======================================================")
    print("Parece que el empaquetador .exe se dejó alguna pieza fuera.")
    print(f"Detalle técnico para el informático: {e}")
    input("\nPresiona la tecla ENTER para cerrar esta ventana...")
    sys.exit(1)

# ==========================================
# CONFIGURACIÓN DE RUTAS 
# ==========================================
CARPETA_ENTRADA = r'\\auxifs\Auxitec\13 Escaner'
CARPETA_CORTADOS = '2_bultos_cortados'
CARPETA_PROWIN = '3_salida_prowin'
CARPETA_HISTORICO = '4_historico_originales'
FORMATOS_BARCODE = zxingcpp.BarcodeFormat.Code128 | zxingcpp.BarcodeFormat.Code39

for carpeta in [CARPETA_CORTADOS, CARPETA_PROWIN, CARPETA_HISTORICO]:
    os.makedirs(carpeta, exist_ok=True)

# ==========================================
# FASE 1: BÚSQUEDA Y CORTE
# ==========================================
def hay_pegatina_separadora(pagina_pdf):
    pix = pagina_pdf.get_pixmap(dpi=600, colorspace=fitz.csGRAY)
    img = Image.frombytes("L", [pix.width, pix.height], pix.samples)
    for codigo in zxingcpp.read_barcodes(img, formats=FORMATOS_BARCODE):
        texto = codigo.text.strip()
        if "0000000" in texto:
            return True
    return False

def extraer_datos_pagina(pagina_pdf):
    albaran, matricula, destino = None, None, None
    pix = pagina_pdf.get_pixmap(dpi=600, colorspace=fitz.csGRAY)
    img = Image.frombytes("L", [pix.width, pix.height], pix.samples)

    codigos_encontrados = zxingcpp.read_barcodes(img, formats=FORMATOS_BARCODE)
    if not codigos_encontrados:
        img_bin = img.point(lambda p: 255 if p > 128 else 0)
        codigos_encontrados = zxingcpp.read_barcodes(img_bin, formats=FORMATOS_BARCODE)

    for codigo in codigos_encontrados:
        texto_barras = codigo.text.strip().strip('*')
        
        if "0000000" in texto_barras:
            continue
        
        print(f"       -> Dato encontrado: {texto_barras}")
        
        if texto_barras.startswith("MAT-"):
            matricula = texto_barras.replace("MAT-", "")
        elif texto_barras.startswith("DST-"):
            destino = texto_barras.replace("DST-", "")
        elif len(texto_barras) < 10 and texto_barras.isdigit():
            albaran = texto_barras
            
    return albaran, matricula, destino

def obtener_numero_bulto(nombre_archivo):
    match = re.search(r'BULTO_(\d+)', nombre_archivo)
    return int(match.group(1)) if match else 0

# ==========================================
# MOTOR PRINCIPAL (ORQUESTADOR)
# ==========================================
def procesar_bandeja_entrada():
    print("\n[1] Conectando con el escáner de la red...")
    print(f"    Ruta configurada: {CARPETA_ENTRADA}")
    
    try:
        archivos_entrada = [f for f in os.listdir(CARPETA_ENTRADA) if f.lower().endswith('.pdf')]
    except FileNotFoundError:
        print("\n[!] ERROR DE CONEXIÓN:")
        print(f"    No puedo acceder a la ruta: {CARPETA_ENTRADA}")
        print("    Comprueba que el ordenador está conectado a la red y tienes permisos.")
        return
    
    if not archivos_entrada:
        print("\n---------------------------------------------------------")
        print(" [i] BANDEJA VACÍA: No hay ningún PDF nuevo para procesar.")
        print("     Todo está al día. Vuelve a ejecutarme cuando escanees más palés.")
        print("---------------------------------------------------------")
        return

    print(f"\n[2] ¡Bingo! Se han encontrado {len(archivos_entrada)} archivo(s) pendientes de procesar.")
    print("    [!] MODO FUERZA BRUTA (600 DPI + ZXING) ACTIVADO.")

    for archivo in archivos_entrada:
        timestamp = datetime.now().strftime("%H%M%S")
        fecha_dia = datetime.now().strftime("%Y%m%d")
        ruta_pdf_original = os.path.join(CARPETA_ENTRADA, archivo)
        
        print(f"\n==================================================")
        print(f"  ABRIENDO ARCHIVO: {archivo}")
        print(f"==================================================")
        
        carpeta_lote_cortados = os.path.join(CARPETA_CORTADOS, f"Lote_{fecha_dia}_{timestamp}")
        os.makedirs(carpeta_lote_cortados, exist_ok=True)
        
        print("  [*] Fase 1: Buscando pegatinas de salto de bulto (13 ceros) y troceando...")
        doc_fitz = fitz.open(ruta_pdf_original)
        
        total_paginas = len(doc_fitz)
        
        pdf_reader = PdfReader(ruta_pdf_original)
        pdf_writer = PdfWriter()
        
        contador_bultos = 1
        bulto_actual = f"BULTO_{contador_bultos}"
        bultos_generados = 0
        
        for num_pagina in range(total_paginas):
            es_salto = hay_pegatina_separadora(doc_fitz[num_pagina])
            
            if es_salto and len(pdf_writer.pages) > 0:
                with open(os.path.join(carpeta_lote_cortados, f"{bulto_actual}.pdf"), "wb") as f_out:
                    pdf_writer.write(f_out)
                    bultos_generados += 1
                
                pdf_writer = PdfWriter()
                contador_bultos += 1
                bulto_actual = f"BULTO_{contador_bultos}"
            
            pdf_writer.add_page(pdf_reader.pages[num_pagina])
        
        if len(pdf_writer.pages) > 0:
            with open(os.path.join(carpeta_lote_cortados, f"{bulto_actual}.pdf"), "wb") as f_out:
                pdf_writer.write(f_out)
                bultos_generados += 1
                
        doc_fitz.close()
        
        if bultos_generados > 0:
            print(f"  [*] Fase 2: {bultos_generados} bulto(s) generados. Extrayendo datos...")
            datos_finales = []
            
            # NUEVO: Memoria GLOBAL para todo el palé
            albaranes_globales = set()
            
            archivos_bultos = [f for f in os.listdir(carpeta_lote_cortados) if f.lower().endswith('.pdf')]
            archivos_bultos.sort(key=obtener_numero_bulto)
            
            for bulto_pdf in archivos_bultos:
                numero_bulto = str(obtener_numero_bulto(bulto_pdf))
                doc_bulto = fitz.open(os.path.join(carpeta_lote_cortados, bulto_pdf))
                
                for num_pagina in range(len(doc_bulto)):
                    albaran, matricula, destino = extraer_datos_pagina(doc_bulto[num_pagina])
                    incidencia = ""
                    
                    if albaran:
                        if albaran in albaranes_globales:
                            incidencia = "DUPLICADO"
                            print(f"       [!] DUPLICADO DETECTADO: El albarán {albaran} ya se leyó antes.")
                        else:
                            albaranes_globales.add(albaran)
                            
                        datos_finales.append({
                            'ALBARAN': albaran,
                            'MATRICULA': matricula if matricula else '',
                            'DESTINO': destino if destino else '',
                            'BULTO': numero_bulto,
                            'INCIDENCIA': incidencia
                        })
                            
                    elif matricula or destino:
                        datos_finales.append({
                            'ALBARAN': 'FALTA-LEER',
                            'MATRICULA': matricula if matricula else '',
                            'DESTINO': destino if destino else '',
                            'BULTO': numero_bulto,
                            'INCIDENCIA': 'REVISAR ALBARAN'
                        })
                        print("       [!] OJO: Albarán ilegible. Marcado para revisión manual.")
                        
                    else:
                        datos_finales.append({
                            'ALBARAN': 'FALTA-LEER',
                            'MATRICULA': 'FALTA-LEER',
                            'DESTINO': 'FALTA-LEER',
                            'BULTO': numero_bulto,
                            'INCIDENCIA': 'HOJA ILEGIBLE / EN BLANCO'
                        })
                        print(f"       [!] ALARMA: Hoja completamente ilegible en el Bulto {numero_bulto}.")

                doc_bulto.close()

            if datos_finales:
                print("  [*] Creando el archivo Excel para Prowin...")
                
                primer_destino = "SIN-DESTINO"
                for dato in datos_finales:
                    if dato['DESTINO'] and dato['DESTINO'] != 'FALTA-LEER':
                        primer_destino = dato['DESTINO']
                        break

                primer_albaran = "SIN-ALBARAN"
                for dato in datos_finales:
                    if dato['ALBARAN'] and dato['ALBARAN'] != 'FALTA-LEER':
                        primer_albaran = dato['ALBARAN']
                        break
                
                nombre_base = f"{primer_destino} {primer_albaran} TOT{total_paginas} {timestamp}"
                archivo_excel = os.path.join(CARPETA_PROWIN, f"{nombre_base}.xls")
                
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Hoja1')
                
                # NUEVO: Añadida la columna INCIDENCIAS
                columnas = ['ALBARAN', 'MATRICULA', 'DESTINO', 'BULTO', 'INCIDENCIAS']
                for col_num, nombre_col in enumerate(columnas):
                    ws.write(0, col_num, nombre_col)
                    
                for row_num, fila in enumerate(datos_finales):
                    ws.write(row_num + 1, 0, fila['ALBARAN'])
                    ws.write(row_num + 1, 1, fila['MATRICULA'])
                    ws.write(row_num + 1, 2, fila['DESTINO'])
                    ws.write(row_num + 1, 3, int(fila['BULTO']))
                    ws.write(row_num + 1, 4, fila['INCIDENCIA'])
                
                ultima_fila = len(datos_finales) + 1
                ws.write(ultima_fila, 0, '--- FIN DE LOTE ---')
                    
                wb.save(archivo_excel)
                
                ruta_historico = os.path.join(CARPETA_HISTORICO, f"{nombre_base}_{archivo}")
                shutil.move(ruta_pdf_original, ruta_historico)
                
                print(f"  [OK] ¡ÉXITO! Excel guardado como: {nombre_base}.xls")
                print("       El PDF original se ha movido al histórico para mantener el escáner limpio.")
            else:
                print(f"  [!] AVISO: El archivo se revisó, pero no se leyó ningún código útil.")
        else:
            print(f"  [!] ERROR: Hubo un problema al intentar procesar el PDF.")
            
        time.sleep(1)

# ==========================================
# INICIO DEL PROGRAMA
# ==========================================
if __name__ == "__main__":
    try:
        print("==================================================")
        print("     SISTEMA DE LECTURA DE ALBARANES AUXITEC      ")
        print("==================================================")
        print("¡Hola! Vamos a procesar los documentos escaneados.\n")
        
        procesar_bandeja_entrada()
        
        print("\n==================================================")
        print("           EL PROCESO HA TERMINADO                ")
        print("==================================================")
        input("\nPulsa la tecla ENTER para cerrar esta ventana...")
        
    except Exception as error_general:
        print("\n[!] VAYA, ALGO HA FALLADO DE FORMA INESPERADA.")
        print(f"Detalle: {error_general}")
        input("\nPulsa ENTER para salir...")