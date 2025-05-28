# api/races.py
from flask import Blueprint, jsonify
import logging
from utils.database import get_db_connection

logger = logging.getLogger(__name__)
races_bp = Blueprint('races', __name__)

@races_bp.route('/races')
def get_races():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cur = conn.cursor()
        cur.execute("""
            SELECT race_id, race_name, race_number, race_type, 
                   distance, surface, conditions_clean, age_restriction, 
                   specific_race_url, race_date, track_name, track_code, created_at
            FROM races 
            WHERE race_date = (SELECT MAX(race_date) FROM races)
            ORDER BY race_number
        """)
        
        races = []
        for row in cur.fetchall():
            race = {
                'race_id': row[0], 
                'race_title': row[1], 
                'race_name': row[1],  # Alias para compatibilidad
                'race_number': row[2],
                'race_type': row[3], 
                'distance': row[4], 
                'surface': row[5],
                'conditions': row[6], 
                'conditions_clean': row[6],  # Alias para compatibilidad
                'age_restriction': row[7], 
                'specific_race_url': row[8],
                'race_date': row[9].isoformat() if row[9] else None,
                'track_name': row[10],
                'track_code': row[11],
                'created_at': row[12].isoformat() if row[12] else None
            }
            races.append(race)
        
        cur.close()
        conn.close()
        return jsonify({'races': races, 'total': len(races)})
        
    except Exception as e:
        logger.error(f"Error obteniendo carreras: {e}")
        return jsonify({'error': str(e)}), 500

@races_bp.route('/races/<race_id>/entries')
def get_race_entries(race_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cur = conn.cursor()
        cur.execute("""
            SELECT horse_name, horse_id, sire, trainer, jockey, 
                   status, status_history, status_changed_at, post_position
            FROM race_entries WHERE race_id = %s ORDER BY post_position NULLS LAST, horse_name
        """, (race_id,))
        
        entries = []
        for row in cur.fetchall():
            entry = {
                'horse_name': row[0], 
                'horse_id': row[1],
                'sire': row[2], 
                'trainer': row[3], 
                'jockey': row[4],
                'status': row[5],
                'status_history': row[6],
                'status_changed_at': row[7].isoformat() if row[7] else None,
                'post_position': row[8]
            }
            entries.append(entry)
        
        cur.close()
        conn.close()
        return jsonify({'entries': entries, 'total': len(entries)})
        
    except Exception as e:
        logger.error(f"Error obteniendo participantes: {e}")
        return jsonify({'error': str(e)}), 500