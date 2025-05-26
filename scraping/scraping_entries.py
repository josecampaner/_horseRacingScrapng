from flask import Flask, render_template, jsonify, request, send_from_directory
from playwright.sync_api import Error as PlaywrightError
import logging
from datetime import datetime

# Importar módulos locales
from modules.config import TRACK_CODES
from modules.database import create_database_tables, save_race_data_to_db
from modules.parsers import parse_race_url_data
from modules.scraper import initialize_playwright_and_load_page, close_playwright, process_race_container

# Ajustar la ruta de template_folder ya que el script está ahora en un subdirectorio
app = Flask(__name__, template_folder='../bases/entries')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/race_data_component.html')
def serve_race_component():
    return send_from_directory(app.template_folder, 'race_data_component.html')

@app.route('/scrape', methods=['GET'])
def scrape_route():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL no proporcionada"}), 400
    
    logging.info(f"Recibida URL para scraping: {url}")
    pw_instance = None 
    browser = None 
    page_obj_for_title = None

    try:
        parsed_url_info = parse_race_url_data(url)
        if not parsed_url_info or parsed_url_info[0] is None or parsed_url_info[1] is None:
            return jsonify({"error": "URL no válida o formato no reconocido..."}), 400
        
        track_name_slug, race_date_str = parsed_url_info
        race_date_obj = datetime.strptime(race_date_str, '%Y-%m-%d').date() if race_date_str else None
        if not race_date_obj: 
            return jsonify({"error": "No se pudo convertir la fecha..."}), 400

        logging.info(f"DEBUG POST-PARSE_URL: Slug='{track_name_slug}', DateStr='{race_date_str}'")
        
        # Crear tablas si no existen
        if not create_database_tables():
            logger.warning("No se pudieron crear/verificar las tablas de la base de datos")
        
        pw_instance, browser, page = initialize_playwright_and_load_page(url)
        page_obj_for_title = page 

        all_races_data = []
        race_containers = page.query_selector_all('div.my-5') 
        logging.info(f"Encontrados {len(race_containers)} contenedores de carreras (div.my-5).")

        current_page_title = page_obj_for_title.title() if page_obj_for_title else "N/A"

        if not race_containers:
            message = "No se encontraron contenedores de carreras (div.my-5) en la página."
            logging.warning(message)
            close_playwright(pw_instance, browser, page) 
            return jsonify({
                "message": message, 
                "page_title": current_page_title, 
                "url_processed": url,
                "data": []
            }), 200

        for race_container in race_containers:
            processed_data = process_race_container(race_container, track_name_slug, race_date_obj, url)
            if processed_data:
                all_races_data.append(processed_data)
                
                # Guardar en base de datos
                if save_race_data_to_db(processed_data, url):
                    logger.info(f"Carrera {processed_data.get('race_id')} guardada en BD exitosamente")
                else:
                    logger.warning(f"Error al guardar carrera {processed_data.get('race_id')} en BD")
        
        close_playwright(pw_instance, browser, page) 
        
        return jsonify({"data": all_races_data, "page_title": current_page_title})

    except Exception as e:
        logging.error(f"Error general en la ruta de scraping: {e}", exc_info=True)
        title_in_exception = "N/A"
        if page_obj_for_title:
            try:
                title_in_exception = page_obj_for_title.title()
            except Exception as title_ex:
                logging.info(f"No se pudo obtener el título durante el manejo de la excepción principal: {title_ex}")
        
        if not isinstance(e, PlaywrightError) or "event loop is closed" not in str(e).lower():
            if browser: 
                try: browser.close()
                except PlaywrightError: pass 
                except Exception as ex_br_close: logging.error(f"Otro error al cerrar browser: {ex_br_close}")
            if pw_instance: 
                try: pw_instance.stop()
                except PlaywrightError: pass 
                except Exception as ex_pw_stop: logging.error(f"Otro error al detener pw_instance: {ex_pw_stop}")
        
        return jsonify({"error": f"Error en el servidor durante el scraping: {str(e)}", "page_title": title_in_exception}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True, use_reloader=False) 