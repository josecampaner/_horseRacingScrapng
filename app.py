# app.py - Archivo principal limpio y organizado

from flask import Flask, send_from_directory
import logging

# Importar blueprints de las APIs
from api.horses import horses_bp
from api.races import races_bp
from api.scraping import scraping_bp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)

# Registrar blueprints
app.register_blueprint(horses_bp, url_prefix='/api')
app.register_blueprint(races_bp, url_prefix='/api')
app.register_blueprint(scraping_bp, url_prefix='/api')

# Rutas principales para servir páginas
@app.route('/')
def index():
    """Página principal de carreras"""
    return send_from_directory('bases/entries', 'index.html')

@app.route('/horses')
def horses_page():
    """Página de caballos"""
    return send_from_directory('bases/horses', 'caballos.html')

@app.route('/dashboard')
def dashboard_page():
    """Página del dashboard"""
    return send_from_directory('bases/dashboard', 'index.html')

# Rutas para servir archivos estáticos
@app.route('/css/<path:filename>')
def serve_css(filename):
    """Servir archivos CSS"""
    return send_from_directory('bases/entries/css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Servir archivos JavaScript"""
    return send_from_directory('bases/entries/js', filename)

@app.route('/horses/css/<path:filename>')
def serve_horses_css(filename):
    """Servir archivos CSS de caballos"""
    return send_from_directory('bases/horses/css', filename)

@app.route('/horses/js/<path:filename>')
def serve_horses_js(filename):
    """Servir archivos JS de caballos"""
    return send_from_directory('bases/horses/js', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)