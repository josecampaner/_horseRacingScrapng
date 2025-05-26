# services/scraping_service.py - Servicio de scraping de caballos

import logging
from datetime import datetime
from utils.ipa_generator import generate_english_ipa, generate_french_ipa, generate_japanese_ipa

logger = logging.getLogger(__name__)

def scrape_horse_profile(horse_id, horse_name):
    """Función para scrapear el perfil de un caballo desde HorseRacingNation"""
    try:
        from playwright.sync_api import sync_playwright
        import re
        
        # Construir URL del perfil del caballo
        profile_url = f"https://www.horseracingnation.com/horse/{horse_id}"
        
        logger.info(f"Scrapeando perfil de {horse_name}: {profile_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(profile_url, timeout=30000)
                page.wait_for_load_state('networkidle', timeout=10000)
                
                # Extraer datos del perfil
                horse_data = {}
                
                # Buscar la sección horse-stats
                horse_stats = page.query_selector('.horse-stats')
                if horse_stats:
                    dt_elements = horse_stats.query_selector_all('dt')
                    dd_elements = horse_stats.query_selector_all('dd')
                    
                    for i, dt in enumerate(dt_elements):
                        if i < len(dd_elements):
                            label = dt.text_content().strip().replace(':', '')
                            value = dd_elements[i].text_content().strip()
                            
                            # Procesar cada campo según su etiqueta
                            if label == 'Age':
                                age_match = re.search(r'(\d+)\s+years?\s+old', value)
                                if age_match:
                                    horse_data['age'] = int(age_match.group(1))
                                
                                # Extraer sexo
                                if 'Filly' in value:
                                    horse_data['sex'] = 'Potra'
                                elif 'Colt' in value:
                                    horse_data['sex'] = 'Potro'
                                elif 'Mare' in value:
                                    horse_data['sex'] = 'Yegua'
                                elif 'Stallion' in value:
                                    horse_data['sex'] = 'Semental'
                                elif 'Gelding' in value:
                                    horse_data['sex'] = 'Castrado'
                            
                            elif label == 'Status':
                                if value == 'Active':
                                    horse_data['status'] = 'Activo'
                                elif value == 'Retired':
                                    horse_data['status'] = 'Retirado'
                                elif value == 'Dead':
                                    horse_data['status'] = 'Fallecido'
                                else:
                                    horse_data['status'] = value
                            
                            elif label == 'Owner(s)':
                                horse_data['owner'] = value
                            
                            elif label == 'Trainer':
                                horse_data['trainer'] = value
                            
                            elif label == 'Bred':
                                bred_parts = value.split(' by ')
                                if len(bred_parts) >= 2:
                                    location = bred_parts[0].strip()
                                    breeder = bred_parts[1].strip()
                                    
                                    horse_data['breeder'] = breeder
                                    
                                    # Extraer país de nacimiento
                                    if 'Kentucky, US' in location or 'US' in location:
                                        horse_data['country_of_birth'] = 'Estados Unidos'
                                    elif 'Canada' in location:
                                        horse_data['country_of_birth'] = 'Canadá'
                                    elif 'Ireland' in location:
                                        horse_data['country_of_birth'] = 'Irlanda'
                                    elif 'England' in location or 'UK' in location:
                                        horse_data['country_of_birth'] = 'Reino Unido'
                                    elif 'France' in location:
                                        horse_data['country_of_birth'] = 'Francia'
                                    elif 'Japan' in location:
                                        horse_data['country_of_birth'] = 'Japón'
                                    elif 'Australia' in location:
                                        horse_data['country_of_birth'] = 'Australia'
                                    else:
                                        horse_data['country_of_birth'] = location
                
                # Buscar color del caballo
                try:
                    page_content = page.content()
                    color_patterns = [
                        r'Bay\b', r'Chestnut\b', r'Brown\b', r'Black\b', 
                        r'Gray\b', r'Grey\b', r'Palomino\b', r'Pinto\b'
                    ]
                    
                    color_translations = {
                        'Bay': 'Bayo', 'Chestnut': 'Castaño', 'Brown': 'Marrón',
                        'Black': 'Negro', 'Gray': 'Gris', 'Grey': 'Gris'
                    }
                    
                    for pattern in color_patterns:
                        match = re.search(pattern, page_content, re.IGNORECASE)
                        if match:
                            color_en = match.group(0)
                            horse_data['color'] = color_translations.get(color_en, color_en)
                            break
                
                except Exception as e:
                    logger.warning(f"Error buscando color para {horse_name}: {e}")
                
                # Generar traducciones IPA
                country_of_birth = horse_data.get('country_of_birth', '')
                if country_of_birth in ['Estados Unidos', 'Canadá', 'Reino Unido', 'Irlanda', 'Australia']:
                    horse_data['horse_name_ipa'] = generate_english_ipa(horse_name)
                    if horse_data.get('owner'):
                        horse_data['owner_ipa'] = generate_english_ipa(horse_data['owner'])
                    if horse_data.get('trainer'):
                        horse_data['trainer_ipa'] = generate_english_ipa(horse_data['trainer'])
                    if horse_data.get('breeder'):
                        horse_data['breeder_ipa'] = generate_english_ipa(horse_data['breeder'])
                
                elif country_of_birth == 'Francia':
                    horse_data['horse_name_ipa'] = generate_french_ipa(horse_name)
                    if horse_data.get('owner'):
                        horse_data['owner_ipa'] = generate_french_ipa(horse_data['owner'])
                    if horse_data.get('trainer'):
                        horse_data['trainer_ipa'] = generate_french_ipa(horse_data['trainer'])
                    if horse_data.get('breeder'):
                        horse_data['breeder_ipa'] = generate_french_ipa(horse_data['breeder'])
                
                elif country_of_birth == 'Japón':
                    horse_data['horse_name_ipa'] = generate_japanese_ipa(horse_name)
                    if horse_data.get('owner'):
                        horse_data['owner_ipa'] = generate_japanese_ipa(horse_data['owner'])
                    if horse_data.get('trainer'):
                        horse_data['trainer_ipa'] = generate_japanese_ipa(horse_data['trainer'])
                    if horse_data.get('breeder'):
                        horse_data['breeder_ipa'] = generate_japanese_ipa(horse_data['breeder'])
                
                # Agregar URL del perfil y timestamp
                horse_data['profile_url'] = profile_url
                horse_data['last_scraped_at'] = datetime.now()
                
                browser.close()
                
                if horse_data:
                    logger.info(f"Datos extraídos para {horse_name}: {horse_data}")
                    return horse_data
                else:
                    logger.warning(f"No se pudieron extraer datos para {horse_name}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error navegando a {profile_url}: {e}")
                browser.close()
                return None
                
    except Exception as e:
        logger.error(f"Error en scrape_horse_profile para {horse_name}: {e}")
        return None

def update_horse_data(cursor, horse_id, horse_data):
    """Actualizar datos del caballo en la base de datos"""
    try:
        update_fields = []
        values = []
        
        for field, value in horse_data.items():
            if field in ['age', 'sex', 'color', 'owner', 'breeder', 'country_of_birth', 'status', 
                        'horse_name_ipa', 'owner_ipa', 'trainer_ipa', 'breeder_ipa', 'country',
                        'profile_url', 'last_scraped_at', 'trainer']:
                update_fields.append(f"{field} = %s")
                values.append(value)
        
        if update_fields:
            update_fields.append("updated_at = %s")
            values.append(datetime.now())
            values.append(horse_id)
            
            query = f"""
                UPDATE horses 
                SET {', '.join(update_fields)}
                WHERE horse_id = %s
            """
            
            cursor.execute(query, values)
            logger.info(f"Datos actualizados en BD para {horse_id}")
            
    except Exception as e:
        logger.error(f"Error actualizando datos para {horse_id}: {e}")
        raise