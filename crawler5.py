import os
import requests
import time
import sys
import math
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}

def obtener_sopa(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        print(f"\n[!] Error de conexión: {e}")
        return None

def mostrar_paginado(lista_roms, items_por_pag=50):
    total_roms = len(lista_roms)
    total_paginas = math.ceil(total_roms / items_por_pag)
    pagina_actual = 1

    while True:
        inicio = (pagina_actual - 1) * items_por_pag
        fin = inicio + items_por_pag
        bloque = lista_roms[inicio:fin]

        print(f"\n--- PÁGINA {pagina_actual} de {total_paginas} ({total_roms} ROMs totales) ---")
        for i, rom in enumerate(bloque, inicio + 1):
            print(f"{i:4}. {rom['nombre']}")
        
        print("\n[ NAVEGACIÓN ]")
        print(" 's' = Siguiente | 'a' = Anterior | 'p[num]' = Ir a página (ej: p5)")
        print(" 'f' = Ir al buscador/descarga | 'menu' = Volver al inicio")
        
        accion = input("\n[?] Elige una opción: ").strip().lower()

        if accion == 's' and pagina_actual < total_paginas:
            pagina_actual += 1
        elif accion == 'a' and pagina_actual > 1:
            pagina_actual -= 1
        elif accion.startswith('p'):
            try:
                nueva_pag = int(accion[1:])
                if 1 <= nueva_pag <= total_paginas: pagina_actual = nueva_pag
            except: print("Página no válida")
        elif accion == 'f':
            return 'FILTRAR'
        elif accion == 'menu':
            return 'BACK'
        elif accion == 'salir':
            sys.exit()

def filtrar_y_descargar(roms_totales, nombre_sistema):
    print("\n" + "="*50)
    print("   MODO DESCARGA / FILTRADO")
    print("="*50)
    print(" > '1,3,5' o '10-20' o 'nombre_juego' o 'todas'")
    print(" > 'volver' para regresar a la paginación")
    
    entrada = input("\n[?] ¿Qué quieres bajar?: ").strip().lower()
    
    if entrada == 'volver': return False
    
    seleccionadas = []
    if entrada == 'todas':
        seleccionadas = roms_totales
    elif ',' in entrada:
        indices = [int(i.strip()) - 1 for i in entrada.split(',') if i.strip().isdigit()]
        seleccionadas = [roms_totales[i] for i in indices if 0 <= i < len(roms_totales)]
    elif '-' in entrada:
        try:
            inicio, fin = map(int, entrada.split('-'))
            seleccionadas = roms_totales[max(0, inicio-1) : fin]
        except: pass
    elif entrada.isdigit():
        idx = int(entrada) - 1
        if 0 <= idx < len(roms_totales): seleccionadas = [roms_totales[idx]]
    else:
        seleccionadas = [r for r in roms_totales if entrada in r['nombre'].lower()]

    if seleccionadas:
        descargar_archivos(seleccionadas, nombre_sistema)
    return True

def descargar_archivos(roms, nombre_sistema):
    carpeta = os.path.join("descargas", nombre_sistema)
    if not os.path.exists(carpeta): os.makedirs(carpeta)
    
    print(f"\n[!] Confirmar {len(roms)} archivos. (s/n)")
    if input("> ").lower() != 's': return

    for i, rom in enumerate(roms, 1):
        ruta = os.path.join(carpeta, rom['nombre'])
        if os.path.exists(ruta): continue
        print(f"[{i}/{len(roms)}] Bajando: {rom['nombre']}")
        with requests.get(rom['url'], headers=HEADERS, stream=True) as r:
            with open(ruta, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024): f.write(chunk)
        time.sleep(0.1)

def ejecucion_principal():
    URL_RAIZ = "https://myrient.erista.me/files/No-Intro/"
    items_pag = 30 # CONFIGURACIÓN: Cuántos juegos ver a la vez

    while True:
        soup = obtener_sopa(URL_RAIZ)
        if not soup: break
        
        sistemas = []
        for a in soup.find_all('a', href=True):
            if a['href'].endswith('/') and not a['href'].startswith(('?', '..')):
                sistemas.append({'nombre': unquote(a['href'].strip('/')), 'url': urljoin(URL_RAIZ, a['href'])})
        
        for i, s in enumerate(sistemas, 1): print(f"{i:3}. {s['nombre']}")
        
        opcion = input("\nElige sistema (número) o 'salir': ").strip().lower()
        if opcion == 'salir': break
        
        try:
            sis = sistemas[int(opcion)-1]
            print(f"\n[+] Cargando ROMs de {sis['nombre']}...")
            soup_roms = obtener_sopa(sis['url'])
            roms_list = [{'nombre': unquote(a['href']), 'url': urljoin(sis['url'], a['href'])} 
                        for a in soup_roms.find_all('a', href=True) if a['href'].lower().endswith('.zip')]

            while True:
                res = mostrar_paginado(roms_list, items_pag)
                if res == 'BACK': break
                if res == 'FILTRAR':
                    if filtrar_y_descargar(roms_list, sis['nombre']):
                        break # Opcional: volver al menú tras descargar
        except:
            print("Selección inválida.")

if __name__ == "__main__":
    ejecucion_principal()
