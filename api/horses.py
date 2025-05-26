# api/horses.py
from flask import Blueprint, jsonify, request
import logging
from utils.database import get_db_connection
from services.scraping_service import scrape_horse_profile, update_horse_data

logger = logging.getLogger(__name__)
horses_bp = Blueprint('horses', __name__)

@horses_bp.route('/horses')
def get_horses():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cur = conn.cursor()
        cur.execute("""
            SELECT horse_id, horse_name, horse_name_ipa, owner, owner_ipa, 
                   trainer, trainer_ipa, breeder, breeder_ipa, country, 
                   country_of_birth, age, status, sex, color, url, profile_url,
                   last_race_date, last_scraped_at, created_at, updated_at
            FROM horses ORDER BY horse_name
        """)
        
        horses = []
        for row in cur.fetchall():
            horse = {
                'horse_id': row[0], 'horse_name': row[1], 'horse_name_ipa': row[2],
                'owner': row[3], 'owner_ipa': row[4], 'trainer': row[5], 'trainer_ipa': row[6],
                'breeder': row[7], 'breeder_ipa': row[8], 'country': row[9], 'country_of_birth': row[10],
                'age': row[11], 'status': row[12], 'sex': row[13], 'color': row[14],
                'url': row[15], 'profile_url': row[16],
                'last_race_date': row[17].isoformat() if row[17] else None,
                'last_scraped_at': row[18].isoformat() if row[18] else None,
                'created_at': row[19].isoformat() if row[19] else None,
                'updated_at': row[20].isoformat() if row[20] else None
            }
            horses.append(horse)
        
        cur.close()
        conn.close()
        return jsonify({'horses': horses, 'total': len(horses)})
        
    except Exception as e:
        logger.error(f"Error obteniendo caballos: {e}")
        return jsonify({'error': str(e)}), 500

@horses_bp.route('/scrape-horse/<horse_id>', methods=['POST'])
def scrape_single_horse(horse_id):
    try:
        data = request.get_json()
        horse_name = data.get('horse_name', horse_id)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cur = conn.cursor()
        horse_data = scrape_horse_profile(horse_id, horse_name)
        
        if horse_data:
            update_horse_data(cur, horse_id, horse_data)
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'horse_id': horse_id,
                'horse_name': horse_name,
                'data_updated': horse_data
            })
        else:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': f'No se pudieron obtener datos para {horse_name}'}), 404
        
    except Exception as e:
        logger.error(f"Error en scrape_single_horse: {e}")
        return jsonify({'error': str(e)}), 500