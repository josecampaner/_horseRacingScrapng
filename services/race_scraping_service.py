import logging
import urllib.parse
from playwright.sync_api import sync_playwright, Error as PlaywrightError
from datetime import datetime

from utils.race_parser import parse_race_url_data, parse_race_title_data, generate_race_id
from utils.text_processing import clean_text, clean_race_type, extract_age_from_conditions, extract_purse_value
from database.models import create_database_tables, save_race_data_to_db

logger = logging.getLogger(__name__)

def initialize_playwright_and_load_page(url_to_scrape):
    """Inicializa Playwright y carga la página"""
    logger.info(f"Inicializando Playwright y navegando a {url_to_scrape}...")
    pw_instance = sync_playwright().start()
    browser = pw_instance.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        page.goto(url_to_scrape, wait_until='networkidle', timeout=90000)
        # Esperar específicamente a que al menos UN 'div.my-5' esté presente.
        # Esto indica que las carreras han comenzado a cargarse.
        page.wait_for_selector('div.my-5', timeout=60000) 
        logger.info(f"Página '{page.title()}' cargada exitosamente y se encontró 'div.my-5'.")
        return pw_instance, browser, page
    except Exception as e:
        logger.error(f"Error durante la inicialización de Playwright o carga de página (esperando 'div.my-5'): {e}")
        # Intentar obtener el título incluso si la espera falla, para logging
        page_title_on_error = "N/A"
        try:
            page_title_on_error = page.title()
        except Exception as title_err:
            logger.error(f"  Error al obtener el título de la página durante el manejo de otra excepción: {title_err}")
        logger.info(f"  Título de la página al momento del error: {page_title_on_error}")
        # Guardar el HTML de la página para depuración si falla la espera del selector
        try:
            page_html_on_error = page.content()
            error_html_filename = f"error_page_content_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}.html"
            with open(error_html_filename, "w", encoding="utf-8") as f:
                f.write(page_html_on_error)
            logger.info(f"  HTML de la página guardado en: {error_html_filename}")
        except Exception as html_save_err:
            logger.error(f"  No se pudo guardar el HTML de la página: {html_save_err}")

        if browser: browser.close()
        if pw_instance: pw_instance.stop()
        raise # Re-lanza la excepción original para que sea manejada por scrape_route

def process_race_container(race_container, track_name_slug, race_date_obj, main_page_url):
    """Procesa un contenedor de carrera individual"""
    # Initialize race_data with all fields expected by index.html and internal logic
    race_data = {
        'race_id': None,
        'race_url': '#', # Corresponds to specific_race_url in frontend
        'track_code': track_name_slug.upper(),
        'race_date': race_date_obj.strftime('%Y-%m-%d') if race_date_obj else 'N/A',
        'race_number': 'N/A',
        'race_name_scraped': 'Título no disponible', # Internal, used for 'title'
        'distance': 'N/A',
        'surface': 'N/A',
        'race_type_full': 'N/A', # Internal, used for race_type_from_detail
        'race_conditions': 'N/A', # Internal, used for conditions
        'purse_text': 'N/A', # Used directly in frontend
        'purse_value': None, # Internal numeric value of purse
        'participants': [],
        'details_summary': 'Detalles no disponibles', # For frontend
        # Explicitly define keys expected by frontend template
        'title': 'Título no disponible',
        'specific_race_url': '#',
        'race_type_from_detail': 'N/A',
        'conditions': 'N/A',
        # other internal fields that might be useful for DB later
        'track_name_scraped': None,
        'time_post_scraped': None,
        'race_type_abbr_scraped': None,
        'sex_restriction_scraped': None,
        'age_restriction_scraped': None,
        'classification_scraped': None,
        'grade_scraped': None,
        'min_claim_price_scraped': None,
        'max_claim_price_scraped': None,
        'min_starter_allowance_price_scraped': None,
        'max_starter_allowance_price_scraped': None,
    }

    try:
        # Buscar el encabezado de la carrera con diferentes selectores
        header_link = race_container.query_selector('h2.row a.race-header')
        
        # Si no encuentra el selector original, probar alternativas
        if not header_link:
            # Buscar cualquier h2 que contenga "Race #"
            h2_elements = race_container.query_selector_all('h2')
            for h2 in h2_elements:
                text_content = h2.inner_text() if h2.inner_text() else ""
                if "Race #" in text_content:
                    # Crear un elemento ficticio para mantener compatibilidad
                    race_title_full = text_content.strip()
                    race_data['race_name_scraped'] = race_title_full
                    race_data['title'] = race_title_full
                    break
            
            # Si no encuentra h2, buscar en el texto del contenedor
            if not race_data.get('title'):
                container_text = race_container.inner_text() if race_container.inner_text() else ""
                lines = container_text.split('\n')
                for line in lines:
                    if "Race #" in line and ("PM" in line or "AM" in line):
                        race_title_full = line.strip()
                        race_data['race_name_scraped'] = race_title_full
                        race_data['title'] = race_title_full
                        break
            
            if not race_data.get('title'):
                logging.warning("No se encontró el título de la carrera. Saltando este contenedor.")
                return None
        else:
            race_title_full = header_link.inner_text().strip() if header_link.inner_text() else 'Título no disponible'
            race_data['race_name_scraped'] = race_title_full
            race_data['title'] = race_title_full # Set frontend title

            race_url_path = header_link.get_attribute('href')
            if race_url_path:
                full_race_url = f"https://www.horseracingnation.com{race_url_path}"
                race_data['race_url'] = full_race_url
                race_data['specific_race_url'] = full_race_url # Set frontend specific_race_url

        parsed_title_info = parse_race_title_data(race_data['title'])
        race_data['race_number'] = parsed_title_info.get('number', 'N/A')
        
        # Generar URL específica con formato #race-X si tenemos el número de carrera
        if race_data['race_number'] != 'N/A' and main_page_url:
            # Construir URL específica: URL_base#race-X
            specific_race_url = f"{main_page_url}#race-{race_data['race_number']}"
            race_data['specific_race_url'] = specific_race_url
        
        logging.info(f"Procesando Carrera: {race_data['title']}")

        details_container = race_container.query_selector('h2.row + div.row')
        summary_parts = []

        if details_container:
            logging.info("  Encontrado details_container con selector 'h2.row + div.row'.")

            distance_div = details_container.query_selector('div.race-distance')
            if distance_div:
                distance_text_full = distance_div.inner_text().strip()
                logging.info(f"    Texto de 'div.race-distance': '{distance_text_full}'")
                parts = [p.strip() for p in distance_text_full.split(',')]
                if len(parts) >= 1: race_data['distance'] = parts[0]
                if len(parts) >= 2: race_data['surface'] = parts[1]
                if len(parts) >= 3: 
                    raw_race_type = ", ".join(parts[2:]) # Join rest for full type
                    race_data['race_type_full'] = clean_race_type(raw_race_type) # Limpiar cantidades monetarias
                
                if race_data['distance'] != 'N/A': summary_parts.append(f"Distancia: {race_data['distance']}")
                if race_data['surface'] != 'N/A': summary_parts.append(f"Superficie: {race_data['surface']}")
                if race_data['race_type_full'] != 'N/A': summary_parts.append(f"Tipo: {race_data['race_type_full']}")
            else:
                logging.warning("    No se encontró 'div.race-distance'.")

            restrictions_div = details_container.query_selector('div.race-restrictions')
            if restrictions_div:
                restrictions_text = restrictions_div.inner_text().strip()
                logging.info(f"    Texto de 'div.race-restrictions': '{restrictions_text}'")
                race_data['race_conditions'] = restrictions_text
                
                # Extraer edad de las condiciones
                age_info = extract_age_from_conditions(restrictions_text)
                race_data['age_restriction_scraped'] = age_info
                
                if race_data['race_conditions'] != 'N/A': summary_parts.append(f"Condiciones: {race_data['race_conditions']}")
                if age_info != 'N/A': summary_parts.append(f"Edad: {age_info}")
            else:
                logging.warning("    No se encontró 'div.race-restrictions'.")

            purse_div = details_container.query_selector('div.race-purse')
            if purse_div:
                purse_text_full = purse_div.inner_text().strip()
                logging.info(f"    Texto de 'div.race-purse': '{purse_text_full}'")
                race_data['purse_text'] = purse_text_full
                race_data['purse_value'] = extract_purse_value(purse_text_full)
                # No agregar bolsa al resumen - se reemplaza por edad
            else:
                logging.warning("    No se encontró 'div.race-purse'.")

            race_data['details_summary'] = '; '.join(summary_parts) if summary_parts else 'Detalles no extraídos.'
            
            # Ensure frontend-specific keys are updated from the more detailed extraction
            race_data['race_type_from_detail'] = race_data['race_type_full']
            race_data['conditions'] = race_data['race_conditions']
            
            # Extraer edad y limpiar condiciones
            race_data['age_restriction_scraped'] = extract_age_from_conditions(race_data['race_conditions'])
            
            logging.info("  Resumen Final de Extracción de Detalles:")
            logging.info(f"    Distancia: {race_data['distance']}")
            logging.info(f"    Superficie: {race_data['surface']}")
            logging.info(f"    Tipo (Detalle): {race_data['race_type_full']}") # race_type_from_detail
            logging.info(f"    Condiciones: {race_data['conditions']}")
            logging.info(f"    Bolsa (Texto): {race_data['purse_text']}")
            logging.info(f"    Bolsa (Num): {race_data['purse_value']}")
            logging.info(f"    Resumen Consolidado (details_summary): {race_data['details_summary']}")
        else:
            logging.warning(f"  No se encontró details_container para '{race_data['title']}'. El resumen de detalles estará vacío o por defecto.")
            race_data['details_summary'] = "Contenedor de detalles no encontrado."

        effective_race_type_for_id = race_data['race_type_full'] if race_data['race_type_full'] != 'N/A' else parsed_title_info.get('type_name', 'UnknownType')
        
        race_data['race_id'] = generate_race_id(
            track_name_slug,
            race_date_obj,
            race_data['race_number'],
            effective_race_type_for_id
        )
        if not race_data['race_id']: # Log if ID generation failed
            logging.warning(f"No se pudo generar race_id para: {race_data['title']}. TrackSlug='{track_name_slug}', DateObj='{race_date_obj}', RaceNum='{race_data['race_number']}', EffectiveType='{effective_race_type_for_id}'")
            race_data['race_id'] = f"ERROR_GENERATING_ID_{race_data['race_number']}" # Fallback ID

        logging.info(f"  Race ID generado: {race_data['race_id']}")
        
        # Extraer participantes de la tabla
        # Buscar la tabla de participantes con diferentes selectores
        race_without_results = race_container.query_selector('div.race-without-results')
        participant_rows = []
        
        logging.info(f"  Buscando tabla de participantes en '{race_data['title']}'...")
        
        if race_without_results:
            logging.info(f"  ✓ Encontrado div.race-without-results para '{race_data['title']}'")
            
            # Buscar tabla con clase específica
            participants_table = race_without_results.query_selector('table.table-entries tbody')
            if participants_table:
                participant_rows = participants_table.query_selector_all('tr')
                logging.info(f"  ✓ Encontradas {len(participant_rows)} filas de participantes en table.table-entries tbody.")
            else:
                logging.info(f"  ✗ No se encontró table.table-entries tbody, intentando con selector genérico...")
                # Intentar con cualquier tabla dentro de race-without-results
                participants_table = race_without_results.query_selector('table tbody')
                if participants_table:
                    participant_rows = participants_table.query_selector_all('tr')
                    logging.info(f"  ✓ Encontradas {len(participant_rows)} filas de participantes usando table tbody genérico.")
                else:
                    logging.warning(f"  ✗ No se encontró ninguna tabla tbody en div.race-without-results.")
        else:
            logging.info(f"  ✗ No se encontró div.race-without-results, buscando tabla directamente...")
            
            # Buscar cualquier tabla en el contenedor
            any_table = race_container.query_selector('table')
            if any_table:
                table_classes = any_table.get_attribute('class') or 'sin-clase'
                logging.info(f"  Encontrada tabla con clases: '{table_classes}'")
                
                # Buscar tbody o usar todas las filas
                tbody = any_table.query_selector('tbody')
                if tbody:
                    participant_rows = tbody.query_selector_all('tr')
                    logging.info(f"  ✓ Encontradas {len(participant_rows)} filas en tbody")
                else:
                    all_rows = any_table.query_selector_all('tr')
                    # Filtrar header row (primera fila)
                    participant_rows = all_rows[1:] if len(all_rows) > 1 else []
                    logging.info(f"  ✓ Encontradas {len(participant_rows)} filas (excluyendo header)")
            else:
                logging.warning(f"  ✗ No se encontró ninguna tabla en el contenedor.")
        
        if participant_rows and len(participant_rows) > 0:
            logging.info(f"  Procesando {len(participant_rows)} filas de participantes...")
            
            for row_idx, row in enumerate(participant_rows):
                try:
                    # Extraer Post Position (PP) - segunda columna
                    pp_cell = row.query_selector('td:nth-child(2)')
                    pp = pp_cell.inner_text().strip() if pp_cell else 'N/A'
                    
                    # Extraer Horse Name, Horse ID y Sire - cuarta columna
                    horse_sire_cell = row.query_selector('td:nth-child(4)')
                    horse_name = 'N/A'
                    horse_id = 'N/A'
                    sire = 'N/A'
                    
                    if horse_sire_cell:
                        horse_link = horse_sire_cell.query_selector('h4 a.horse-link')
                        if horse_link:
                            horse_name = horse_link.inner_text().strip()
                            # Extraer horse_id del href del enlace
                            horse_href = horse_link.get_attribute('href')
                            if horse_href:
                                # El href es algo como "/horse/Camigol" - extraemos la parte final
                                raw_horse_id = horse_href.split('/')[-1] if '/' in horse_href else horse_href
                                # Decodificar caracteres especiales en la URL
                                horse_id = urllib.parse.unquote(raw_horse_id)
                        
                        sire_p = horse_sire_cell.query_selector('p')
                        if sire_p:
                            sire = sire_p.inner_text().strip()
                    
                    # Extraer Trainer y Jockey - quinta columna
                    trainer_jockey_cell = row.query_selector('td:nth-child(5)')
                    trainer = 'N/A'
                    jockey = 'N/A'
                    
                    if trainer_jockey_cell:
                        trainer_jockey_ps = trainer_jockey_cell.query_selector_all('p')
                        if len(trainer_jockey_ps) >= 1:
                            trainer = trainer_jockey_ps[0].inner_text().strip()
                        if len(trainer_jockey_ps) >= 2:
                            jockey = trainer_jockey_ps[1].inner_text().strip()
                    
                    # Solo agregar si tenemos datos válidos
                    if horse_name != 'N/A' or pp != 'N/A':
                        participant = {
                            'pp': pp,
                            'horse_name': horse_name,
                            'horse_id': horse_id,
                            'sire': sire,
                            'trainer': trainer,
                            'jockey': jockey
                        }
                        
                        race_data['participants'].append(participant)
                        logging.info(f"    Participante {row_idx+1}: PP={pp}, Horse={horse_name}, HorseID={horse_id}, Sire={sire}, Trainer={trainer}, Jockey={jockey}")
                    else:
                        logging.info(f"    Fila {row_idx+1} omitida - sin datos válidos de caballo")
                    
                except Exception as e:
                    logging.warning(f"    Error procesando fila {row_idx+1} de participante: {e}")
                    continue
        else:
            logging.warning(f"  No se encontraron filas de participantes para '{race_data['title']}'.")

    except Exception as e:
        logging.error(f"Error procesando un contenedor de carrera para '{race_data.get('title', 'Título Desconocido')}': {e}", exc_info=True)
        # Return the partially populated race_data or None.
        # For robustness, let's return what we have, with error indicators.
        race_data['details_summary'] = f"Error al procesar: {e}"
        race_data['race_id'] = race_data.get('race_id') or f"ERROR_PROCESSING_{race_data.get('race_number', 'UKN_NUM')}"
        # Ensure all frontend keys at least have their default 'N/A' or error string
        for key in ['title', 'specific_race_url', 'distance', 'surface', 'race_type_from_detail', 'conditions', 'purse_text', 'details_summary']:
            if key not in race_data or race_data[key] is None:
                race_data[key] = 'Error de procesamiento'
        return race_data # Return partially filled data with error notes

    return race_data

def close_playwright(pw_instance, browser, page):
    """Cierra Playwright de forma segura"""
    if browser:
        try: 
            browser.close()
            logging.info("Navegador Playwright cerrado.")
        except Exception as e_br:
             logging.error(f"Error al cerrar el navegador Playwright: {e_br}", exc_info=True)
    if pw_instance:
        try: 
            pw_instance.stop()
            logging.info("Instancia de Playwright detenida.")
        except Exception as e_pw:
            logging.error(f"Error al detener la instancia de Playwright: {e_pw}", exc_info=True)

def scrape_races_from_url(url):
    """Función principal para scrapear carreras desde una URL"""
    try:
        # Crear tablas si no existen
        if not create_database_tables():
            return {
                'success': False,
                'error': 'Failed to create database tables'
            }
        
        # Inicializar Playwright y cargar la página
        pw_instance, browser, page = initialize_playwright_and_load_page(url)
        
        if not page:
            return {
                'success': False,
                'error': 'Failed to load page'
            }
        
        # Extraer datos de la URL
        url_data = parse_race_url_data(url)
        track_name_slug = url_data.get('track_name_slug', 'unknown')
        race_date_obj = url_data.get('race_date_obj')
        
        # Buscar contenedores de carreras - probar diferentes selectores
        race_containers = page.query_selector_all('div.race-container')
        
        # Si no encuentra race-container, probar con otros selectores
        if not race_containers:
            logger.info("No se encontraron div.race-container, probando selectores alternativos...")
            
            # Probar con div.my-5 que aparece en los logs
            race_containers = page.query_selector_all('div.my-5')
            logger.info(f"Encontrados {len(race_containers)} elementos con div.my-5")
            
            # Si tampoco encuentra, probar con selectores más generales
            if not race_containers:
                # Buscar cualquier div que contenga "Race #" en el texto
                all_divs = page.query_selector_all('div')
                race_containers = []
                for div in all_divs:
                    text_content = div.inner_text() if div.inner_text() else ""
                    if "Race #" in text_content or "Race " in text_content:
                        race_containers.append(div)
                logger.info(f"Encontrados {len(race_containers)} elementos que contienen 'Race #'")
        
        if not race_containers:
            close_playwright(pw_instance, browser, page)
            return {
                'success': False,
                'error': 'No race containers found on the page'
            }
        
        # Extraer información de la página ANTES de cerrar Playwright
        page_title = page.title() if page else "Unknown Page"
        
        # Procesar cada carrera
        all_races_data = []
        for race_container in race_containers:
            race_data = process_race_container(race_container, track_name_slug, race_date_obj, url)
            if race_data:
                # Guardar en base de datos
                if save_race_data_to_db(race_data, url):
                    logger.info(f"Carrera {race_data.get('race_id')} guardada en BD exitosamente")
                else:
                    logger.error(f"Error al guardar carrera {race_data.get('race_id')} en BD")
                
                all_races_data.append(race_data)
        
        # Cerrar Playwright DESPUÉS de procesar todo
        close_playwright(pw_instance, browser, page)
        
        return {
            'success': True,
            'page_title': page_title,
            'total_races': len(all_races_data),
            'url': url,
            'races': all_races_data
        }
        
    except Exception as e:
        logger.error(f"Error en scrape_races_from_url: {e}")
        return {
            'success': False,
            'error': str(e)
        } 