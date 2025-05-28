# api/scraping.py
from flask import Blueprint, jsonify, request
import logging
from datetime import datetime
import sys
import os

logger = logging.getLogger(__name__)
scraping_bp = Blueprint('scraping', __name__)

@scraping_bp.route('/scrape', methods=['GET', 'POST'])
def scrape_route():
    """Endpoint completo para scrapear carreras desde HorseRacingNation y guardar en BD"""
    if request.method == 'POST':
        data = request.get_json()
        url = data.get('url') if data else None
    else:
        url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL no proporcionada"}), 400
    
    logger.info(f"Recibida URL para scraping: {url}")
    
    try:
        # Importar funciones del sistema completo de scraping
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from utils.race_parser import parse_race_url_data
        from database.models import create_database_tables, save_race_data_to_db
        from services.race_scraping_service import scrape_races_from_url
        
        # Usar la función completa que incluye completado automático de perfiles
        result = scrape_races_from_url(url)
        
        if result.get('success'):
            return jsonify({
                "success": True,
                "races": result.get('races', []),
                "page_title": result.get('page_title', 'N/A'),
                "url": url,
                "total_races": result.get('total_races', 0),
                "message": f"Scraping completado: {result.get('total_races', 0)} carreras procesadas. Los perfiles de caballos se completaron automáticamente."
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Error desconocido')
            }), 500
        
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
        
        # Obtener participantes de la carrera usando horse_id
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cur = conn.cursor()
        cur.execute("""
            SELECT re.horse_id, re.horse_name 
            FROM race_entries re
            LEFT JOIN horses h ON re.horse_id = h.horse_id
            WHERE re.race_id = %s 
            AND re.horse_id IS NOT NULL 
            AND re.horse_id != 'N/A'
            AND (
                h.updated_at IS NULL 
                OR h.updated_at < NOW() - INTERVAL '20 days'
            )
        """, (race_id,))
        
        horses = cur.fetchall()
        
        # También contar cuántos caballos ya están actualizados
        cur.execute("""
            SELECT COUNT(*) FROM race_entries re
            LEFT JOIN horses h ON re.horse_id = h.horse_id
            WHERE re.race_id = %s 
            AND re.horse_id IS NOT NULL 
            AND re.horse_id != 'N/A'
            AND h.updated_at IS NOT NULL 
            AND h.updated_at >= NOW() - INTERVAL '20 days'
        """, (race_id,))
        
        skipped_result = cur.fetchone()
        skipped_count = skipped_result[0] if skipped_result else 0
        
        if not horses:
            cur.close()
            conn.close()
            if skipped_count > 0:
                return jsonify({
                    'success': True,
                    'race_id': race_id,
                    'message': f'Todos los {skipped_count} caballos ya fueron actualizados en los últimos 20 días',
                    'scraped_count': 0,
                    'skipped_count': skipped_count
                })
            else:
                return jsonify({'error': f'No se encontraron caballos para la carrera {race_id}'}), 404
        
        scraped_count = 0
        errors = []
        
        for horse_id, horse_name in horses:
            try:
                logger.info(f"Scrapeando caballo: {horse_name} ({horse_id})")
                
                horse_data = scrape_horse_profile(horse_id, horse_name)
                
                if horse_data:
                    # Usar el horse_id para guardar en BD
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
            'total_horses': len(horses),
            'scraped_count': scraped_count,
            'skipped_count': skipped_count,
            'errors': errors,
            'message': f'Scraping completado: {scraped_count}/{len(horses)} caballos procesados, {skipped_count} omitidos (actualizados recientemente)'
        })
        
    except Exception as e:
        logger.error(f"Error en scrape_horses_for_race: {str(e)}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

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
            SELECT DISTINCT re.horse_id, re.horse_name 
            FROM race_entries re
            LEFT JOIN horses h ON re.horse_id = h.horse_id
            WHERE re.horse_id IS NOT NULL 
            AND re.horse_id != 'N/A'
            AND (
                h.updated_at IS NULL 
                OR h.updated_at < NOW() - INTERVAL '20 days'
            )
        """)
        
        horses = cur.fetchall()
        
        # Contar caballos omitidos
        cur.execute("""
            SELECT COUNT(DISTINCT re.horse_id) 
            FROM race_entries re
            LEFT JOIN horses h ON re.horse_id = h.horse_id
            WHERE re.horse_id IS NOT NULL 
            AND re.horse_id != 'N/A'
            AND h.updated_at IS NOT NULL 
            AND h.updated_at >= NOW() - INTERVAL '20 days'
        """)
        
        skipped_result = cur.fetchone()
        skipped_count = skipped_result[0] if skipped_result else 0
        
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
            'total_horses': len(horses),
            'scraped_count': scraped_count,
            'skipped_count': skipped_count,
            'errors': errors,
            'message': f'Scraping masivo completado: {scraped_count}/{len(horses)} caballos procesados, {skipped_count} omitidos (actualizados recientemente)'
        })
        
    except Exception as e:
        logger.error(f"Error en scrape_all_horses: {str(e)}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

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
            'status': horse_data.get('status'),
            'pedigree': horse_data.get('pedigree')
        }
        
        return jsonify({
            'success': True,
            'horse_data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error en scrape_horse_profile_endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@scraping_bp.route('/check-and-update-horses', methods=['POST'])
def check_and_update_horses():
    """Endpoint para revisar y actualizar caballos que no se han actualizado en los últimos 20 días"""
    try:
        from utils.database import get_db_connection
        from services.scraping_service import scrape_horse_profile, update_horse_data
        
        logger.info("Revisando caballos que necesitan actualización")
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cur = conn.cursor()
        
        # Buscar caballos que no se han actualizado en los últimos 20 días
        cur.execute("""
            SELECT horse_id, horse_name 
            FROM horses 
            WHERE updated_at IS NULL 
            OR updated_at < NOW() - INTERVAL '20 days'
            ORDER BY horse_name
        """)
        
        horses_to_update = cur.fetchall()
        
        # Contar caballos ya actualizados
        cur.execute("""
            SELECT COUNT(*) 
            FROM horses 
            WHERE updated_at IS NOT NULL 
            AND updated_at >= NOW() - INTERVAL '20 days'
        """)
        
        updated_result = cur.fetchone()
        already_updated_count = updated_result[0] if updated_result else 0
        
        if not horses_to_update:
            cur.close()
            conn.close()
            return jsonify({
                'success': True,
                'message': f'Todos los caballos están actualizados. Total: {already_updated_count} caballos actualizados en los últimos 20 días',
                'horses_to_update': 0,
                'already_updated': already_updated_count,
                'scraped_count': 0,
                'errors': []
            })
        
        scraped_count = 0
        errors = []
        
        logger.info(f"Encontrados {len(horses_to_update)} caballos que necesitan actualización")
        
        for horse_id, horse_name in horses_to_update:
            try:
                logger.info(f"Actualizando caballo: {horse_name} ({horse_id})")
                
                horse_data = scrape_horse_profile(horse_id, horse_name)
                
                if horse_data:
                    update_horse_data(cur, horse_id, horse_data)
                    scraped_count += 1
                    logger.info(f"✅ Caballo {horse_name} actualizado exitosamente")
                else:
                    errors.append(f"No se pudieron obtener datos para {horse_name}")
                    logger.warning(f"❌ No se pudieron obtener datos para {horse_name}")
                    
            except Exception as e:
                error_msg = f"Error actualizando {horse_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'horses_to_update': len(horses_to_update),
            'already_updated': already_updated_count,
            'scraped_count': scraped_count,
            'errors': errors,
            'message': f'Actualización completada: {scraped_count}/{len(horses_to_update)} caballos actualizados. {already_updated_count} ya estaban actualizados.'
        })
        
    except Exception as e:
        logger.error(f"Error en check_and_update_horses: {str(e)}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@scraping_bp.route('/scrape-null-horses', methods=['POST'])
def scrape_null_horses():
    """Endpoint específico para scrapear solo caballos con updated_at NULL"""
    try:
        from utils.database import get_db_connection
        from services.scraping_service import scrape_horse_profile, update_horse_data
        
        logger.info("Iniciando scraping de caballos NULL")
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cur = conn.cursor()
        
        # Buscar solo caballos con updated_at NULL
        cur.execute("""
            SELECT horse_id, horse_name 
            FROM horses 
            WHERE updated_at IS NULL
            ORDER BY horse_name
        """)
        
        null_horses = cur.fetchall()
        
        if not null_horses:
            cur.close()
            conn.close()
            return jsonify({
                'success': True,
                'message': 'No hay caballos con updated_at NULL',
                'null_horses_found': 0,
                'scraped_count': 0,
                'errors': []
            })
        
        scraped_count = 0
        errors = []
        
        logger.info(f"Encontrados {len(null_horses)} caballos con updated_at NULL")
        
        for horse_id, horse_name in null_horses:
            try:
                logger.info(f"Scrapeando caballo NULL: {horse_name} ({horse_id})")
                
                horse_data = scrape_horse_profile(horse_id, horse_name)
                
                if horse_data:
                    update_horse_data(cur, horse_id, horse_data)
                    scraped_count += 1
                    logger.info(f"✅ Caballo NULL {horse_name} scrapeado exitosamente")
                else:
                    errors.append(f"No se pudieron obtener datos para {horse_name}")
                    logger.warning(f"❌ No se pudieron obtener datos para {horse_name}")
                    
            except Exception as e:
                error_msg = f"Error scrapeando {horse_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                
                # Si hay error de transacción, hacer rollback y crear nueva conexión
                if 'current transaction is aborted' in str(e):
                    logger.warning("Transacción abortada, creando nueva conexión")
                    try:
                        conn.rollback()
                        cur.close()
                        conn.close()
                        
                        # Nueva conexión
                        conn = get_db_connection()
                        if conn:
                            cur = conn.cursor()
                        else:
                            break
                    except Exception as rollback_error:
                        logger.error(f"Error en rollback: {rollback_error}")
                        break
        
        if conn:
            try:
                conn.commit()
                cur.close()
                conn.close()
            except Exception as commit_error:
                logger.error(f"Error en commit final: {commit_error}")
        
        return jsonify({
            'success': True,
            'null_horses_found': len(null_horses),
            'scraped_count': scraped_count,
            'errors': errors,
            'message': f'Scraping NULL completado: {scraped_count}/{len(null_horses)} caballos NULL procesados'
        })
        
    except Exception as e:
        logger.error(f"Error en scrape_null_horses: {str(e)}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500