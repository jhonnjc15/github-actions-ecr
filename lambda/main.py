import time
import pandas as pd
import boto3
import json
import re
from io import StringIO, BytesIO
from urllib.parse import urljoin
from datetime import datetime
from zoneinfo import ZoneInfo
from curl_cffi import requests
from bs4 import BeautifulSoup
from prompt import USER_PROMPT, SYSTEM_PROMPTV3

# ================== CONFIGURACIÓN GENERAL ==================
BUCKET_NAME = "XXXXXXX"
RAW_NEWS = "XXXXXXX"
PROCESS_NEWS = "XXXXXXX"
BASE_URL = "XXXXXXX/"
WEB_ORIGEN = "XXXXXXX"
HAIKU_ID = "XXXXXXX"

s3 = boto3.client("s3")

# ================== FUNCIONES DE LIMPIEZA Y UTILIDADES ==================

def obtener_html(url, max_retries=3, pause_seconds=5):
    """
    Intenta obtener el HTML de una URL con reintentos automáticos
    en caso de fallos de conexión o timeouts.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, impersonate="chrome110", timeout=15)
            
            if response.status_code == 200:
                return response.text
            
            if response.status_code in [500, 502, 503, 504]:
                print(f"Error {response.status_code} en intento {attempt + 1}. Reintentando...")
            else:
                return None

        except Exception as e:
            print(f"Error de conexión en {url} (Intento {attempt + 1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            print(f"Esperando {pause_seconds} segundos antes del reintento...")
            time.sleep(pause_seconds)
    
    print(f"Falló definitivamente la descarga de: {url}")
    return None

def limpiar_texto(texto):
    if not texto: return ""
    texto = re.sub(r'\s+', ' ', str(texto)).strip()
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)

def procesar_fecha(texto_fecha):
    if not texto_fecha: return ""
    texto_limpio = limpiar_texto(texto_fecha)
    
    if ":" in texto_limpio or "ago" in texto_limpio.lower():
        return datetime.now().strftime("%Y-%m-%d")
    
    match_corto = re.match(r'^(\d{1,2})-(\d{1,2})$', texto_limpio)
    if match_corto:
        dia, mes = match_corto.groups()
        anio_actual = datetime.now().year
        return f"{anio_actual}-{mes.zfill(2)}-{dia.zfill(2)}"

    match_largo = re.match(r'^(\d{1,2})-(\d{1,2})-(\d{4})$', texto_limpio)
    if match_largo:
        dia, mes, anio = match_largo.groups()
        return f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"
    
    return texto_limpio

# ================== LÓGICA DE IA ==================
def obtener_resultados_ia(bedrock_client, title: str, fragment: str):
    try:
        user_prompt = USER_PROMPT.format(
            title_field=title,
            fragment_field=fragment
        )

        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 650,
            "system": SYSTEM_PROMPTV3,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
        }

        response = bedrock_client.invoke_model(
            body=json.dumps(native_request),
            modelId=HAIKU_ID,
            accept="application/json",
            contentType="application/json"
        )

        response_body = json.loads(response["body"].read())
        response_text = response_body["content"][0]["text"]
        
        try:
            result_dict = json.loads(response_text)
        except json.JSONDecodeError as e:
            print("Error al convertir response_text a JSON. Texto recibido:")
            print(response_text)
            return ("", "", "", "", "", "", "")

        return (
            result_dict.get("sector_sentiment", ""),
            result_dict.get("producer_impact", ""),
            result_dict.get("reasoning_sector_sentiment", ""),
            result_dict.get("reasoning_producer_impact", ""),
            result_dict.get("deslenguaje", ""), 
            result_dict.get("despaisorigen", ""),
            result_dict.get("descategoria", "") 
        )

    except Exception as e:
        print(f"Error IA en '{title[:20]}...': {e}")
        return ("", "", "", "", "", "", "")

# ================== LÓGICA DE EXTRACCIÓN ==================
def extraer_detalle(url):
    html = obtener_html(url)
    if not html: return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Datos Basicos
    h1 = soup.find('h1')
    titulo = h1.get_text(strip=True) if h1 else "Sin título"
    
    span_fecha = soup.select_one("div.aout-article span")
    raw_fecha = span_fecha.get_text(strip=True) if span_fecha else ""
    fecha_final = procesar_fecha(raw_fecha)
    
    # Descripción
    descripcion = ""
    article = soup.find('article')
    if not article: article = soup 
    
    p_elements = article.find_all('p')
    keywords_filtro = ["cookies", "personal data", "store and/or access", "subscribe", "login"]
    
    for p in p_elements:
        txt = p.get_text(strip=True)
        if len(txt) <= 80: continue
        if any(k in txt.lower() for k in keywords_filtro): continue
        clases = p.get('class', [])
        if clases and any('caption' in c for c in clases): continue 
        descripcion = txt
        break 
    
    if not descripcion:
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            descripcion = meta_desc.get('content')
        if not descripcion:
            og_desc = soup.find('meta', property='og:description')
            if og_desc and og_desc.get('content'):
                descripcion = og_desc.get('content')

    # Imagen
    img = soup.select_one(".wp-post-image")
    url_imagen = img['src'] if img else ""
    
    print(f"Scraped: {titulo[:30]}... [Fecha: {fecha_final}]")
    
    return {
        "nbrtitulo": limpiar_texto(titulo),
        "desresumen": limpiar_texto(descripcion),
        "fecdia": fecha_final,
        "urlimagen": url_imagen,
        "urlnoticia": url,
        "weborigen": WEB_ORIGEN,
        "fuente": "PoultryWorld",
        "codapp": "POULTRYWORLD",
        "descategoria": "", "dessubcategoria": "", "deslenguaje": "", "despaisorigen": ""
    }

def obtener_links_listado(num_pages=1):
    links_totales = []
    for page in range(1, num_pages + 1):
        url = BASE_URL if page == 1 else f"{BASE_URL}page/{page}/"
        print(f"Analizando listado página {page}...")
        html = obtener_html(url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            h3s = soup.find_all('h3')
            for h3 in h3s:
                a_tag = h3.find('a')
                if a_tag and a_tag.get('href'):
                    full_url = urljoin(BASE_URL, a_tag.get('href'))
                    if full_url not in links_totales:
                        links_totales.append(full_url)
            time.sleep(1.5)
    return links_totales

# ================== SUBIDA A S3 ==================
def upload_files_s3(df, timestamp_str):
    nombre_base = f"poultryworld_scrap_news_{timestamp_str}"
    
    # 1. CSV Processed
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    key_csv = f"{PROCESS_NEWS}{nombre_base}.csv"
    s3.put_object(
        Bucket=BUCKET_NAME, Key=key_csv,
        Body=csv_buffer.getvalue().encode('utf-8-sig'), ContentType="text/csv"
    )
    print(f"Subido CSV: {key_csv}")

    # 2. Excel Raw
    try:
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        key_excel = f"{RAW_NEWS}{nombre_base}.xlsx"
        s3.put_object(
            Bucket=BUCKET_NAME, Key=key_excel,
            Body=excel_buffer.read(),
            ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        print(f"Subido Excel: {key_excel}")
    except Exception as e:
        print(f"Error generando Excel: {e}")

# ================== MAIN LAMBDA HANDLER ==================
def lambda_handler(event, context):
    print("Iniciando Ejecucion...")

    try:
        bedrock_runtime = boto3.client("bedrock-runtime")
        print("Bedrock Runtime inicializado")
    except Exception as e:
        print(f"Error inicializando Bedrock: {e}")
        bedrock_runtime = None

    now_lima = datetime.now(ZoneInfo("America/Lima"))
    timestamp_name_file = now_lima.strftime("%Y%m%d_%H%M%S")
    TIMESTAMP_AUDITORIA = now_lima.strftime("%Y-%m-%d %H:%M:%S")

    registros = 0
    
    try:
        # 1. Scraping de Links
        urls_noticias = obtener_links_listado(num_pages=6)
        print(f"Links encontrados: {len(urls_noticias)}")
        
        datos_finales = []
        
        # 2. Extracción de Datos
        for i, link in enumerate(urls_noticias):
            try:
                info = extraer_detalle(link)
                
                if info:
                    if bedrock_runtime:
                        s_sent, p_imp, r_sent, r_imp, d_lang, d_pais, d_cat = obtener_resultados_ia(
                            bedrock_runtime,
                            info["nbrtitulo"], 
                            info["desresumen"]
                        )
                        info["sector_sentiment"] = s_sent
                        info["producer_impact"] = p_imp
                        info["reasoning_sector_sentiment"] = r_sent
                        info["reasoning_producer_impact"] = r_imp
                        info["deslenguaje"] = d_lang      
                        info["despaisorigen"] = d_pais
                        info["descategoria"] = d_cat 
                        info["modelsentiment"] = HAIKU_ID
                    else:
                        info["sector_sentiment"] = ""
                        info["producer_impact"] = ""
                        info["reasoning_sector_sentiment"] = ""
                        info["reasoning_producer_impact"] = ""
                        info["deslenguaje"] = ""          
                        info["despaisorigen"] = ""
                        info["descategoria"] = ""   
                        info["modelsentiment"] = "ERROR_BEDROCK"

                    datos_finales.append(info)
                
                time.sleep(1.5) 
                
            except Exception as e:
                print(f"Error en loop principal noticia {link}: {e}")
        
        # 3. Guardado
        if datos_finales:
            df = pd.DataFrame(datos_finales)
            
            df["fecactualizacionregistro"] = TIMESTAMP_AUDITORIA
            
            columnas_ordenadas = [
                "descategoria", "dessubcategoria", "nbrtitulo", "desresumen", "fecdia",
                "urlimagen", "urlnoticia", "weborigen", "fuente", "deslenguaje",
                "despaisorigen", "sector_sentiment", "producer_impact",
                "reasoning_sector_sentiment", "reasoning_producer_impact",
                "codapp", "fecactualizacionregistro", "modelsentiment"
            ]
            
            for col in columnas_ordenadas:
                if col not in df.columns:
                    df[col] = ""
            
            df = df[columnas_ordenadas]
            registros = len(df)
            
            upload_files_s3(df, timestamp_name_file)
            
            print("Proceso finalizado con éxito.")
        else:
            print("No se generaron datos.")

    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "message": str(e)}

    return {
        "statusCode": 200,
        "message": "Ejecución correcta",
        "total_procesado": registros,
        "timestamp": timestamp_name_file
    }