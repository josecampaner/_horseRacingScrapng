# api/scraping.py
from flask import Blueprint, jsonify, request
import logging
from datetime import datetime
import sys
import os

logger = logging.getLogger(__name__)
scraping_bp = Blueprint('scraping', __name__)

@scraping_bp.route('/scrape', methods=['GET'])
def scrape_route():
    """Endpoint completo para scrapear carreras desde HorseRacingNation y guardar en BD"""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL no proporcionada"}), 400
    
    logger.info(f"Recibida URL para scraping: {url}")
    
    try:
        # Importar funciones del sistema completo de scraping
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scraping'))
        
        from scraping_entries_backup_840lines import (
            parse_race_url_data, _initialize_playwright_and_load_page, 
            _process_race_container, save_race_data_to_db, create_database_tables,
            _close_playwright
        )
        
        # Parsear URL
        parsed_url_info = parse_race_url_data(url)
        if not parsed_url_info or parsed_url_info[0] is None or parsed_url_info[1] is None:
            return jsonify({"error": "URL no válida o formato no reconocido"}), 400
        
        track_name_slug, race_date_str = parsed_url_info
        race_date_obj = datetime.strptime(race_date_str, '%Y-%m-%d').date() if race_date_str else None
        if not race_date_obj: 
            return jsonify({"error": "No se pudo convertir la fecha"}), 400

        logger.info(f"URL parseada: Slug='{track_name_slug}', Fecha='{race_date_str}'")
        
        # Crear tablas si no existen
        if not create_database_tables():
            logger.warning("No se pudieron crear/verificar las tablas de la base de datos")
        
        # Inicializar Playwright
        pw_instance, browser, page = _initialize_playwright_and_load_page(url)
        page_title = page.title() if page else "N/A"

        # Buscar contenedores de carreras
        race_containers = page.query_selector_all('div.my-5') 
        logger.info(f"Encontrados {len(race_containers)} contenedores de carreras")

        if not race_containers:
            _close_playwright(pw_instance, browser, page)
            return jsonify({
                "message": "No se encontraron contenedores de carreras en la página",
                "page_title": page_title,
                "url_processed": url,
                "data": []
            }), 200

        all_races_data = []
        
        # Procesar cada carrera
        for race_container in race_containers:
            processed_data = _process_race_container(race_container, track_name_slug, race_date_obj, url)
            if processed_data:
                all_races_data.append(processed_data)
                
                # Guardar en base de datos
                if save_race_data_to_db(processed_data, url):
                    logger.info(f"Carrera {processed_data.get('race_id')} guardada en BD exitosamente")
                else:
                    logger.warning(f"Error al guardar carrera {processed_data.get('race_id')} en BD")
        
        _close_playwright(pw_instance, browser, page)
        
        return jsonify({
            "data": all_races_data,
            "page_title": page_title,
            "url_processed": url,
            "total_races": len(all_races_data)
        })
        
    except Exception as e:
        logger.error(f"Error general en scraping: {e}")
        return jsonify({"error": f"Error en el servidor: {str(e)}"}), 500

@scraping_bp.route('/scrape-horses/<race_id>', methods=['POST'])
def scrape_horses_for_race(race_id):
    """Endpoint para scrapear caballos de una carrera específica"""
    try:
        from utils.database import get_db_connection
        from services.scraping_service import scrape_horse_profile, update_horse_data
        
        logger.info(f"Iniciando scraping de caballos para carrera: {race_id}")
        
        # Obtener participantes de la carrera
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cur = conn.cursor()
        cur.execute("""
            SELECT horse_id, horse_name FROM race_entries 
            WHERE race_id = %s AND horse_id IS NOT NULL AND horse_id != 'N/A'
        """, (race_id,))
        
        horses = cur.fetchall()
        if not horses:
            cur.close()
            conn.close()
            return jsonify({'error': f'No se encontraron caballos para la carrera {race_id}'}), 404
        
        scraped_count = 0
        errors = []
        
        for horse_id, horse_name in horses:
            try:
                logger.info(f"Scrapeando caballo: {horse_name} ({horse_id})")
                horse_data = scrape_horse_profile(horse_id, horse_name)
                
                if horse_data:
                    update_horse_data(cur, horse_id, horse_data)
                    scraped_count += 1
                    logger.info(f"✅ Caballo {horse_name} scrapeado exitosamente")
                else:
                    errors.append(f"No se pudieron obtener datos para {horse_name}")
                    logger.warning(f"❌ No se pudieron obtener datos para {horse_name}")
                    
            except Exception as e:
                error_msg = f"Error scrapeando {horse_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'race_id': race_id,
            'scraped_count': scraped_count,
            'total_horses': len(horses),
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error en scrape_horses_for_race: {e}")
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/scrape-all-horses', methods=['POST'])
def scrape_all_horses():
    """Endpoint para scrapear TODOS los caballos de todas las carreras"""
    try:
        from utils.database import get_db_connection
        from services.scraping_service import scrape_horse_profile, update_horse_data
        
        logger.info("Iniciando scraping masivo de todos los caballos")
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT horse_id, horse_name FROM race_entries 
            WHERE horse_id IS NOT NULL AND horse_id != 'N/A'
        """)
        
        horses = cur.fetchall()
        if not horses:
            cur.close()
            conn.close()
            return jsonify({'error': 'No se encontraron caballos para scrapear'}), 404
        
        scraped_count = 0
        errors = []
        
        for horse_id, horse_name in horses:
            try:
                logger.info(f"Scrapeando caballo: {horse_name} ({horse_id})")
                horse_data = scrape_horse_profile(horse_id, horse_name)
                
                if horse_data:
                    update_horse_data(cur, horse_id, horse_data)
                    scraped_count += 1
                    logger.info(f"✅ Caballo {horse_name} scrapeado exitosamente")
                else:
                    errors.append(f"No se pudieron obtener datos para {horse_name}")
                    logger.warning(f"❌ No se pudieron obtener datos para {horse_name}")
                    
            except Exception as e:
                error_msg = f"Error scrapeando {horse_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'total_horses': scraped_count,
            'total_races': 'N/A',
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error en scrape_all_horses: {e}")
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/scrape-horse-profile', methods=['POST'])
def scrape_horse_profile_endpoint():
    """Endpoint para scrapear el perfil de un caballo individual"""
    try:
        data = request.get_json()
        horse_url = data.get('horse_url')
        
        if not horse_url:
            return jsonify({'error': 'URL del caballo no proporcionada'}), 400
        
        # Extraer horse_id de la URL
        # URL formato: https://www.horseracingnation.com/horse/Mine_Strike
        horse_id = horse_url.split('/')[-1] if '/' in horse_url else horse_url
        horse_name = horse_id.replace('_', ' ')
        
        logger.info(f"Scrapeando perfil individual: {horse_name} ({horse_id})")
        
        from services.scraping_service import scrape_horse_profile, update_horse_data
        from utils.database import get_db_connection
        
        # Scrapear datos del caballo
        horse_data = scrape_horse_profile(horse_id, horse_name)
        
        if not horse_data:
            return jsonify({'error': f'No se pudieron obtener datos para {horse_name}'}), 404
        
        # Guardar en base de datos
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            update_horse_data(cur, horse_id, horse_data)
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"✅ Datos de {horse_name} guardados en BD")
        
        # Preparar respuesta con todos los datos que espera el frontend
        response_data = {
            'horse_id': horse_id,
            'horse_name': horse_name,
            'horse_name_ipa': horse_data.get('horse_name_ipa'),
            'age': horse_data.get('age'),
            'sex': horse_data.get('sex'),
            'color': horse_data.get('color'),
            'owner': horse_data.get('owner'),
            'owner_ipa': horse_data.get('owner_ipa'),
            'trainer': horse_data.get('trainer'),
            'trainer_ipa': horse_data.get('trainer_ipa'),
            'breeder': horse_data.get('breeder'),
            'breeder_ipa': horse_data.get('breeder_ipa'),
            'country_of_birth': horse_data.get('country_of_birth'),
            'status': horse_data.get('status')
        }
        
        return jsonify({
            'success': True,
            'horse_data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error en scrape_horse_profile_endpoint: {e}")
        return jsonify({'error': str(e)}), 500