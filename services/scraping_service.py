# services/scraping_service.py - Servicio de scraping de caballos
#
# NOTA: La estructura HTML del pedigree está documentada en:
# docs/pedigree_html_structure.html
#
# Consultar ese archivo para entender la estructura exacta del HTML
# que se usa para extraer los datos de ancestros en la función scrape_horse_profile()

import logging
from datetime import datetime
from utils.ipa_generator import generate_english_ipa, generate_french_ipa, generate_japanese_ipa
import psycopg2
from playwright.sync_api import sync_playwright
import re

logger = logging.getLogger(__name__)

def scrape_horse_profile(horse_id, horse_name):
    """Función para scrapear el perfil de un caballo desde HorseRacingNation"""
    try:
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
                
                # Limpiar campos que contengan "[Add Data]" antes de generar IPA
                def clean_add_data(value):
                    if value and '[Add Data]' in str(value):
                        return None
                    return value
                
                horse_data['owner'] = clean_add_data(horse_data.get('owner'))
                horse_data['trainer'] = clean_add_data(horse_data.get('trainer'))
                horse_data['breeder'] = clean_add_data(horse_data.get('breeder'))
                
                # Generar traducciones IPA
                country_of_birth = horse_data.get('country_of_birth', 'Estados Unidos')  # Default a Estados Unidos
                
                # Siempre generar IPA para el nombre del caballo
                if country_of_birth in ['Estados Unidos', 'Canadá', 'Reino Unido', 'Irlanda', 'Australia'] or not country_of_birth:
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
                
                # Extraer datos de pedigree usando la estructura exacta del HTML
                pedigree_data = {}
                
                try:
                    # Buscar la estructura específica del pedigree con las dos filas
                    pedigree_rows = page.query_selector_all('div.row.mx-0.display-flex')
                    
                    if len(pedigree_rows) >= 2:
                        # Primera fila: lado paterno (sire)
                        paternal_row = pedigree_rows[0]
                        
                        # Extraer sire (padre) - col-4 px-0 text-center
                        sire_link = paternal_row.query_selector('a.parent.sire')
                        if sire_link:
                            href = sire_link.get_attribute('href')
                            horse_id_extracted = extract_horse_id_from_url(href)
                            if horse_id_extracted:
                                pedigree_data['sire_id'] = horse_id_extracted
                        
                        # Extraer abuelos paternos - segunda columna
                        paternal_grandparents = paternal_row.query_selector_all('a.grandparent')
                        if len(paternal_grandparents) >= 2:
                            # Primer abuelo paterno (sire)
                            if paternal_grandparents[0]:
                                href = paternal_grandparents[0].get_attribute('href')
                                horse_id_extracted = extract_horse_id_from_url(href)
                                if horse_id_extracted:
                                    pedigree_data['paternal_grandsire_id'] = horse_id_extracted
                            
                            # Primera abuela paterna (dam)
                            if paternal_grandparents[1]:
                                href = paternal_grandparents[1].get_attribute('href')
                                horse_id_extracted = extract_horse_id_from_url(href)
                                if horse_id_extracted:
                                    pedigree_data['paternal_granddam_id'] = horse_id_extracted
                        
                        # Extraer bisabuelos paternos - tercera columna
                        paternal_greatgrandparents = paternal_row.query_selector_all('a.greatgrandparent')
                        if len(paternal_greatgrandparents) >= 4:
                            # Bisabuelos del lado del sire paterno
                            if paternal_greatgrandparents[0]:
                                href = paternal_greatgrandparents[0].get_attribute('href')
                                horse_id_extracted = extract_horse_id_from_url(href)
                                if horse_id_extracted:
                                    pedigree_data['paternal_gg_sire_id'] = horse_id_extracted
                            
                            if paternal_greatgrandparents[1]:
                                href = paternal_greatgrandparents[1].get_attribute('href')
                                horse_id_extracted = extract_horse_id_from_url(href)
                                if horse_id_extracted:
                                    pedigree_data['paternal_gg_dam_id'] = horse_id_extracted
                            
                            # Bisabuelos del lado de la dam paterna
                            if paternal_greatgrandparents[2]:
                                href = paternal_greatgrandparents[2].get_attribute('href')
                                horse_id_extracted = extract_horse_id_from_url(href)
                                if horse_id_extracted:
                                    pedigree_data['paternal_gd_sire_id'] = horse_id_extracted
                            
                            if paternal_greatgrandparents[3]:
                                href = paternal_greatgrandparents[3].get_attribute('href')
                                horse_id_extracted = extract_horse_id_from_url(href)
                                if horse_id_extracted:
                                    pedigree_data['paternal_gd_dam_id'] = horse_id_extracted
                        
                        # Segunda fila: lado materno (dam)
                        maternal_row = pedigree_rows[1]
                        
                        # Extraer dam (madre) - col-4 px-0 text-center
                        dam_link = maternal_row.query_selector('a.parent.dam')
                        if dam_link:
                            href = dam_link.get_attribute('href')
                            horse_id_extracted = extract_horse_id_from_url(href)
                            if horse_id_extracted:
                                pedigree_data['dam_id'] = horse_id_extracted
                        
                        # Extraer abuelos maternos - segunda columna
                        maternal_grandparents = maternal_row.query_selector_all('a.grandparent')
                        maternal_gp_valid = []
                        for gp in maternal_grandparents:
                            href = gp.get_attribute('href')
                            text = gp.text_content().strip()
                            # Filtrar enlaces de edición
                            if href and 'horseedit.aspx' not in href and '[Add Data]' not in text:
                                maternal_gp_valid.append(gp)
                        
                        if len(maternal_gp_valid) >= 1:
                            # Abuelo materno (sire)
                            href = maternal_gp_valid[0].get_attribute('href')
                            horse_id_extracted = extract_horse_id_from_url(href)
                            if horse_id_extracted:
                                pedigree_data['maternal_grandsire_id'] = horse_id_extracted
                        
                        if len(maternal_gp_valid) >= 2:
                            # Abuela materna (dam)
                            href = maternal_gp_valid[1].get_attribute('href')
                            horse_id_extracted = extract_horse_id_from_url(href)
                            if horse_id_extracted:
                                pedigree_data['maternal_granddam_id'] = horse_id_extracted
                        
                        # Extraer bisabuelos maternos - tercera columna
                        maternal_greatgrandparents = maternal_row.query_selector_all('a.greatgrandparent')
                        maternal_ggp_valid = []
                        for ggp in maternal_greatgrandparents:
                            href = ggp.get_attribute('href')
                            text = ggp.text_content().strip()
                            # Filtrar enlaces de edición
                            if href and 'horseedit.aspx' not in href and '[Add Data]' not in text:
                                maternal_ggp_valid.append(ggp)
                        
                        if len(maternal_ggp_valid) >= 2:
                            # Bisabuelos del lado del sire materno
                            href = maternal_ggp_valid[0].get_attribute('href')
                            horse_id_extracted = extract_horse_id_from_url(href)
                            if horse_id_extracted:
                                pedigree_data['maternal_gg_sire_id'] = horse_id_extracted
                            
                            href = maternal_ggp_valid[1].get_attribute('href')
                            horse_id_extracted = extract_horse_id_from_url(href)
                            if horse_id_extracted:
                                pedigree_data['maternal_gg_dam_id'] = horse_id_extracted
                        
                        if len(maternal_ggp_valid) >= 4:
                            # Bisabuelos del lado de la dam materna
                            href = maternal_ggp_valid[2].get_attribute('href')
                            horse_id_extracted = extract_horse_id_from_url(href)
                            if horse_id_extracted:
                                pedigree_data['maternal_gd_sire_id'] = horse_id_extracted
                            
                            href = maternal_ggp_valid[3].get_attribute('href')
                            horse_id_extracted = extract_horse_id_from_url(href)
                            if horse_id_extracted:
                                pedigree_data['maternal_gd_dam_id'] = horse_id_extracted
                
                except Exception as e:
                    logger.warning(f"Error extrayendo pedigree para {horse_name}: {e}")
                
                # Agregar pedigree a horse_data si se encontró
                if pedigree_data:
                    horse_data['pedigree'] = pedigree_data
                    logger.info(f"Pedigree extraído para {horse_name}: {pedigree_data}")
                
                # Agregar URL del perfil
                horse_data['profile_url'] = profile_url
                
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
        # Hacer una copia de los datos de pedigree antes de procesarlos
        pedigree_data = horse_data.get('pedigree', None)
        
        # Primero, obtener los datos actuales del caballo para comparar
        cursor.execute("""
            SELECT age, sex, color, owner, breeder, country_of_birth, status, 
                   horse_name_ipa, owner_ipa, trainer_ipa, breeder_ipa, trainer,
                   profile_url
            FROM horses 
            WHERE horse_id = %s
        """, (horse_id,))
        
        current_data = cursor.fetchone()
        
        # Actualizar datos generales del caballo (excluyendo pedigree)
        update_fields = []
        values = []
        has_changes = False
        
        if current_data:
            # Comparar cada campo para detectar cambios reales
            field_mapping = {
                'age': 0, 'sex': 1, 'color': 2, 'owner': 3, 'breeder': 4, 
                'country_of_birth': 5, 'status': 6, 'horse_name_ipa': 7, 
                'owner_ipa': 8, 'trainer_ipa': 9, 'breeder_ipa': 10, 
                'trainer': 11, 'profile_url': 12
            }
            
            for field, value in horse_data.items():
                if field in field_mapping:
                    current_value = current_data[field_mapping[field]]
                    
                    # Comparar valores (considerando NULL vs None)
                    if current_value != value:
                        update_fields.append(f"{field} = %s")
                        values.append(value)
                        has_changes = True
                        logger.info(f"Cambio detectado en {field}: '{current_value}' → '{value}'")
                        
            # Solo actualizar updated_at si hay cambios reales en un registro existente
            if update_fields and has_changes:
                update_fields.append("updated_at = %s")
                values.append(datetime.now())
                values.append(horse_id)
                
                query = f"""
                    UPDATE horses 
                    SET {', '.join(update_fields)}
                    WHERE horse_id = %s
                """
                
                cursor.execute(query, values)
                logger.info(f"✅ Datos actualizados en BD para {horse_id} (cambios detectados)")
            else:
                logger.info(f"ℹ️ No hay cambios para {horse_id} - updated_at no modificado")
        else:
            # Si current_data es None, significa que el caballo no existe en la BD
            # Esto NO debería pasar si usamos find_or_create_horse correctamente
            logger.warning(f"⚠️ Caballo {horse_id} no encontrado en BD - esto no debería ocurrir")
        
        # Guardar datos de pedigree si existen
        if pedigree_data:
            save_pedigree_data(cursor, horse_id, pedigree_data)
            
    except Exception as e:
        logger.error(f"Error actualizando datos para {horse_id}: {e}")
        raise

def save_pedigree_data(cursor, horse_id, pedigree_data):
    """Guardar datos de pedigree en la tabla pedigree"""
    try:
        logger.info(f"Guardando pedigree para {horse_id}: {pedigree_data}")
        
        # Verificar si ya existe un registro de pedigree para este caballo usando horse_id
        cursor.execute("""
            SELECT sire_id, dam_id, maternal_grandsire_id, paternal_grandsire_id, 
                   paternal_granddam_id, maternal_granddam_id, paternal_gg_sire_id,
                   paternal_gg_dam_id, paternal_gd_sire_id, paternal_gd_dam_id,
                   maternal_gg_sire_id, maternal_gg_dam_id, maternal_gd_sire_id,
                   maternal_gd_dam_id
            FROM pedigree 
            WHERE horse_id = %s
        """, (horse_id,))
        
        current_pedigree = cursor.fetchone()
        
        if current_pedigree:
            # Actualizar registro existente - solo si hay cambios
            update_fields = []
            values = []
            has_changes = False
            
            # Mapeo de campos para comparación
            field_mapping = {
                'sire_id': 0, 'dam_id': 1, 'maternal_grandsire_id': 2, 'paternal_grandsire_id': 3,
                'paternal_granddam_id': 4, 'maternal_granddam_id': 5, 'paternal_gg_sire_id': 6,
                'paternal_gg_dam_id': 7, 'paternal_gd_sire_id': 8, 'paternal_gd_dam_id': 9,
                'maternal_gg_sire_id': 10, 'maternal_gg_dam_id': 11, 'maternal_gd_sire_id': 12,
                'maternal_gd_dam_id': 13
            }
            
            for field, value in pedigree_data.items():
                if field in field_mapping:
                    current_value = current_pedigree[field_mapping[field]]
                    
                    # Comparar valores (considerando NULL vs None)
                    if current_value != value:
                        update_fields.append(f"{field} = %s")
                        values.append(value)
                        has_changes = True
                        logger.info(f"Cambio en pedigree {field}: '{current_value}' → '{value}'")
            
            if has_changes:
                # Solo actualizar updated_at si hay cambios reales
                update_fields.append("updated_at = %s")
                values.append(datetime.now())
                values.append(horse_id)
                
                query = f"""
                    UPDATE pedigree 
                    SET {', '.join(update_fields)}
                    WHERE horse_id = %s
                """
                cursor.execute(query, values)
                logger.info(f"✅ Pedigree actualizado en BD para {horse_id} (cambios detectados)")
            else:
                logger.info(f"ℹ️ No hay cambios en pedigree para {horse_id} - updated_at no modificado")
        else:
            # Crear nuevo registro - establecer created_at y updated_at
            fields = ['horse_id']
            values = [horse_id]
            
            for field, value in pedigree_data.items():
                if field in ['sire_id', 'dam_id', 'maternal_grandsire_id', 'paternal_grandsire_id', 
                           'paternal_granddam_id', 'maternal_granddam_id', 'paternal_gg_sire_id',
                           'paternal_gg_dam_id', 'paternal_gd_sire_id', 'paternal_gd_dam_id',
                           'maternal_gg_sire_id', 'maternal_gg_dam_id', 'maternal_gd_sire_id',
                           'maternal_gd_dam_id']:
                    fields.append(field)
                    values.append(value)
            
            # Agregar timestamps para nuevo registro
            fields.extend(['created_at'])
            current_time = datetime.now()
            values.extend([current_time])
            
            placeholders = ', '.join(['%s'] * len(values))
            query = f"""
                INSERT INTO pedigree ({', '.join(fields)})
                VALUES ({placeholders})
            """
            cursor.execute(query, values)
            logger.info(f"✅ Pedigree insertado en BD para {horse_id}")
            
    except Exception as e:
        logger.error(f"Error guardando pedigree para {horse_id}: {e}")
        raise

def extract_horse_id_from_url(href):
    """Extrae el horse_id desde una URL de HorseRacingNation"""
    if not href:
        return None
    
    # Patrón para URLs como: /horse/Horse_Name o /horse/Horse_Name_1
    match = re.search(r'/horse/([^/?]+)', href)
    if match:
        return match.group(1)
    
    return None