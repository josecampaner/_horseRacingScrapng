#!/usr/bin/env python3
"""
Aplicación Flask modular para scraping de carreras de caballos
Versión refactorizada usando módulos separados
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurar Flask con rutas de archivos estáticos y templates
app = Flask(__name__, 
           template_folder='bases/entries',
           static_folder='bases/entries')

# Importar servicios
from services.race_scraping_service import scrape_races_from_url
from database.models import get_db_connection

@app.route('/')
def index():
    """Página principal con formulario de búsqueda"""
    return render_template('index.html')

@app.route('/race_data_component.html')
def serve_race_component():
    """Servir el componente de datos de carrera"""
    return send_from_directory(app.template_folder, 'race_data_component.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Servir archivos CSS"""
    css_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bases', 'entries', 'css'))
    return send_from_directory(css_dir, filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Servir archivos JavaScript"""
    js_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bases', 'entries', 'js'))
    return send_from_directory(js_dir, filename)

@app.route('/scrape', methods=['POST'])
def scrape_route():
    """Endpoint para scrapear carreras desde una URL"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
        
        url = data['url'].strip()
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL cannot be empty'
            }), 400
        
        logger.info(f"Iniciando scraping para URL: {url}")
        
        # Usar el servicio de scraping modular
        result = scrape_races_from_url(url)
        
        if result['success']:
            logger.info(f"Scraping completado exitosamente: {result['total_races']} carreras encontradas")
            return jsonify(result)
        else:
            logger.error(f"Error en scraping: {result.get('error', 'Unknown error')}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error en scrape_route: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/races')
def get_races():
    """API para obtener carreras de la base de datos"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT race_id, track_code, race_date, race_number, 
                   race_name, distance, surface, race_type, 
                   purse_text, created_at
            FROM races 
            ORDER BY race_date DESC, race_number ASC
            LIMIT 50
        """)
        
        races = []
        for row in cursor.fetchall():
            races.append({
                'race_id': row[0],
                'track_code': row[1],
                'race_date': row[2].strftime('%Y-%m-%d') if row[2] else 'N/A',
                'race_number': row[3],
                'race_name': row[4],
                'distance': row[5],
                'surface': row[6],
                'race_type': row[7],
                'purse_text': row[8],
                'created_at': row[9].strftime('%Y-%m-%d %H:%M:%S') if row[9] else 'N/A'
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'races': races,
            'total': len(races)
        })
        
    except Exception as e:
        logger.error(f"Error en get_races: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/race/<race_id>/entries')
def get_race_entries(race_id):
    """API para obtener las entradas de una carrera específica"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT re.horse_name, re.horse_id, 
                   re.sire, re.trainer, re.jockey,
                   h.age, h.sex, h.color, h.owner
            FROM race_entries re
            LEFT JOIN horses h ON re.horse_id = h.horse_id
            WHERE re.race_id = %s
            ORDER BY re.horse_name
        """, (race_id,))
        
        entries = []
        for row in cursor.fetchall():
            entries.append({
                'horse_name': row[0],
                'horse_id': row[1],
                'sire': row[2],
                'trainer': row[3],
                'jockey': row[4],
                'age': row[5],
                'sex': row[6],
                'color': row[7],
                'owner': row[8]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'race_id': race_id,
            'entries': entries,
            'total': len(entries)
        })
        
    except Exception as e:
        logger.error(f"Error en get_race_entries: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Endpoint de salud para verificar que el servidor está funcionando"""
    return jsonify({
        'status': 'healthy',
        'service': 'Horse Racing Scraper',
        'version': '2.0.0-modular'
    })

if __name__ == '__main__':
    logger.info("Iniciando aplicación Flask modular...")
    logger.info("Servidor disponible en: http://127.0.0.1:5005")
    
    # Ejecutar en modo debug para desarrollo
    app.run(
        host='127.0.0.1',
        port=5005,
        debug=True,
        use_reloader=True
    ) 