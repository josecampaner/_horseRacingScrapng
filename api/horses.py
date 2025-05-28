# api/horses.py
from flask import Blueprint, jsonify, request
import logging
from database.models import get_db_connection
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
                   last_race_date, created_at, updated_at
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
                'created_at': row[18].isoformat() if row[18] else None,
                'updated_at': row[19].isoformat() if row[19] else None
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

@horses_bp.route('/pedigree/check-missing-horses', methods=['POST'])
def check_missing_horses_from_pedigree():
    """
    Revisa la tabla pedigree y añade a la tabla horses todos los caballos
    que no tienen ficha pero aparecen en el pedigree
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cur = conn.cursor()
        
        # 1. Obtener todos los horse_ids únicos del pedigree
        cur.execute("""
            SELECT DISTINCT horse_id 
            FROM pedigree 
            WHERE horse_id IS NOT NULL 
            AND horse_id != ''
        """)
        pedigree_horses = [row[0] for row in cur.fetchall()]
        total_pedigree_horses = len(pedigree_horses)
        
        logger.info(f"Encontrados {total_pedigree_horses} caballos únicos en pedigree")
        
        # 2. Verificar cuáles ya existen en la tabla horses
        if pedigree_horses:
            placeholders = ','.join(['%s'] * len(pedigree_horses))
            cur.execute(f"""
                SELECT horse_id 
                FROM horses 
                WHERE horse_id IN ({placeholders})
            """, pedigree_horses)
            existing_horses = [row[0] for row in cur.fetchall()]
            horses_already_exist = len(existing_horses)
            
            # 3. Encontrar caballos faltantes
            missing_horses = [h for h in pedigree_horses if h not in existing_horses]
            
            logger.info(f"Caballos ya existentes: {horses_already_exist}")
            logger.info(f"Caballos faltantes: {len(missing_horses)}")
            
            # 4. Añadir los caballos faltantes a la tabla horses
            horses_added = 0
            for horse_id in missing_horses:
                try:
                    # Insertar con datos mínimos - el horse_id como nombre temporal
                    cur.execute("""
                        INSERT INTO horses (horse_id, horse_name, status, created_at, updated_at)
                        VALUES (%s, %s, 'incomplete', NOW(), NOW())
                        ON CONFLICT (horse_id) DO NOTHING
                    """, (horse_id, horse_id))
                    
                    if cur.rowcount > 0:
                        horses_added += 1
                        logger.info(f"Añadido caballo: {horse_id}")
                
                except Exception as e:
                    logger.error(f"Error añadiendo caballo {horse_id}: {e}")
                    continue
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'total_pedigree_horses': total_pedigree_horses,
                'horses_already_exist': horses_already_exist,
                'horses_added': horses_added,
                'missing_horses_found': len(missing_horses),
                'message': f'Se añadieron {horses_added} nuevos caballos a la tabla horses'
            })
        
        else:
            cur.close()
            conn.close()
            return jsonify({
                'success': True,
                'total_pedigree_horses': 0,
                'horses_already_exist': 0,
                'horses_added': 0,
                'message': 'No se encontraron caballos en la tabla pedigree'
            })
        
    except Exception as e:
        logger.error(f"Error en check_missing_horses_from_pedigree: {e}")
        return jsonify({'error': str(e)}), 500