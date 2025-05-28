# utils/track_ipa_generator.py - Generador de pronunciaciones IPA para pistas de carreras

import logging

logger = logging.getLogger(__name__)

def generate_track_ipa_and_country(track_name):
    """Generar pronunciación IPA y país para nombres de pistas de carreras"""
    if not track_name:
        return None, None
    
    # Diccionario de pronunciaciones de pistas con país de origen
    track_data_dict = {
        # Estados Unidos
        'Gulfstream Park': ('/gʌlfstriːm pɑːrk/', 'USA'),
        'Churchill Downs': ('/tʃɜːrtʃɪl daʊnz/', 'USA'),
        'Belmont Park': ('/belmɑːnt pɑːrk/', 'USA'),
        'Santa Anita Park': ('/sæntə ænɪtə pɑːrk/', 'USA'),
        'Saratoga Race Course': ('/særətoʊgə reɪs kɔːrs/', 'USA'),
        'Saratoga': ('/ˌsærəˈtoʊgə/', 'USA'),
        'Thistledown': ('/ˈθɪsəldaʊn/', 'USA'),
        'Del Mar': ('/del mɑːr/', 'USA'),
        'Keeneland': ('/kiːnlænd/', 'USA'),
        'Oaklawn Park': ('/oʊklɔːn pɑːrk/', 'USA'),
        'Fair Grounds': ('/fɛr graʊndz/', 'USA'),
        'Aqueduct': ('/ækwɪdʌkt/', 'USA'),
        'Pimlico': ('/pɪmlɪkoʊ/', 'USA'),
        'Monmouth Park': ('/mɑːnməθ pɑːrk/', 'USA'),
        'Laurel Park': ('/lɔːrəl pɑːrk/', 'USA'),
        'Tampa Bay Downs': ('/tæmpə beɪ daʊnz/', 'USA'),
        'Woodbine': ('/wʊdbaɪn/', 'Canada'),
        'Hastings Racecourse': ('/heɪstɪŋz reɪskɔːrs/', 'Canada'),
        
        # Reino Unido
        'Ascot': ('/æskət/', 'UK'),
        'Epsom Downs': ('/epsəm daʊnz/', 'UK'),
        'Newmarket': ('/nuːmɑːrkɪt/', 'UK'),
        'Cheltenham': ('/tʃeltənəm/', 'UK'),
        'Aintree': ('/eɪntriː/', 'UK'),
        'York': ('/jɔːrk/', 'UK'),
        'Goodwood': ('/gʊdwʊd/', 'UK'),
        'Doncaster': ('/dɑːnkæstər/', 'UK'),
        
        # Francia
        'Longchamp': ('/lɔ̃ʃɑ̃/', 'France'),
        'Chantilly': ('/ʃɑ̃tiˈji/', 'France'),
        'Deauville': ('/doˈvil/', 'France'),
        'Saint-Cloud': ('/sɛ̃kluː/', 'France'),
        
        # Irlanda
        'Curragh': ('/kʌrə/', 'Ireland'),
        'Leopardstown': ('/lepərdztaʊn/', 'Ireland'),
        'Fairyhouse': ('/fɛrihaʊs/', 'Ireland'),
        
        # Australia
        'Flemington': ('/flemɪŋtən/', 'Australia'),
        'Randwick': ('/rændwɪk/', 'Australia'),
        'Caulfield': ('/kɔːlfiːld/', 'Australia'),
        'Moonee Valley': ('/muːniː væli/', 'Australia'),
        
        # Japón
        'Tokyo Racecourse': ('/toʊkioʊreɪskɔːrs/', 'Japan'),
        'Kyoto Racecourse': ('/kjoʊtoʊreɪskɔːrs/', 'Japan'),
        'Nakayama': ('/nækəjæmə/', 'Japan'),
        
        # Hong Kong
        'Sha Tin': ('/ʃɑːtɪn/', 'Hong Kong'),
        'Happy Valley': ('/hæpivæli/', 'Hong Kong'),
        
        # Emiratos Árabes Unidos
        'Meydan': ('/meɪdæn/', 'UAE'),
        
        # Argentina
        'Hipódromo de San Isidro': ('/ipoːdromodəsænɪsɪdro/', 'Argentina'),
        'Hipódromo de Palermo': ('/ipoːdromodəpælermo/', 'Argentina'),
        
        # Brasil
        'Jockey Club Brasileiro': ('/dʒɑːkikləbbrəzɪleɪro/', 'Brazil'),
        'Hipódromo da Gávea': ('/ipoːdromodəgæveə/', 'Brazil'),
        
        # Chile
        'Club Hípico de Santiago': ('/kləbipikodesæntiægo/', 'Chile'),
        'Valparaíso Sporting Club': ('/vælpəraɪsospɔːrtɪŋkləb/', 'Chile'),
        
        # México
        'Hipódromo de las Américas': ('/ipoːdromodəlæsæmerɪkəs/', 'Mexico'),
        
        # Perú
        'Hipódromo de Monterrico': ('/ipoːdromodəmɑːnterikoʊ/', 'Peru'),
        
        # España
        'Hipódromo de la Zarzuela': ('/ipoːdromodəlæzærzwelə/', 'Spain'),
        
        # Sudáfrica
        'Kenilworth': ('/kenɪlwərθ/', 'South Africa'),
        'Turffontein': ('/tərfɑːnteɪn/', 'South Africa'),
    }
    
    # Buscar coincidencia exacta primero
    if track_name in track_data_dict:
        ipa, country = track_data_dict[track_name]
        return ipa, country
    
    # Buscar coincidencias parciales (para casos como "Gulfstream" vs "Gulfstream Park")
    for track_key, (ipa, country) in track_data_dict.items():
        if track_name.lower() in track_key.lower() or track_key.lower() in track_name.lower():
            return ipa, country
    
    # Si no se encuentra, generar una aproximación básica
    logger.warning(f"No se encontró pronunciación IPA específica para la pista: {track_name}")
    basic_ipa = generate_basic_track_ipa(track_name)
    return basic_ipa, 'Unknown'

def generate_track_ipa(track_name):
    """Función de compatibilidad que solo devuelve el IPA sin país"""
    ipa, country = generate_track_ipa_and_country(track_name)
    return ipa

def generate_basic_track_ipa(track_name):
    """Generar pronunciación IPA básica para pistas no reconocidas"""
    if not track_name:
        return None
    
    # Aplicar reglas fonéticas básicas del inglés
    words = track_name.split()
    ipa_parts = []
    
    for word in words:
        word_clean = word.lower().strip()
        if not word_clean:
            continue
            
        # Reglas básicas simplificadas
        ipa_word = ''
        i = 0
        while i < len(word_clean):
            char = word_clean[i]
            
            if char == 'a':
                ipa_word += 'æ'
            elif char == 'e':
                if i == len(word_clean) - 1:
                    pass  # e final silenciosa
                else:
                    ipa_word += 'e'
            elif char == 'i':
                ipa_word += 'ɪ'
            elif char == 'o':
                ipa_word += 'oʊ'
            elif char == 'u':
                ipa_word += 'ʌ'
            elif char == 'y':
                ipa_word += 'aɪ'
            elif char in 'bcdfghjklmnpqrstvwxz':
                ipa_word += char
            
            i += 1
        
        if ipa_word:
            ipa_parts.append(ipa_word)
    
    # Unir con espacios y agregar barras solo al principio y final
    ipa_result = f'/{" ".join(ipa_parts)}/'
    return ipa_result 