# utils/horse_ipa_generator.py - Generador de pronunciaciones IPA para nombres de caballos

import logging
try:
    import epitran
    EPITRAN_AVAILABLE = True
except ImportError:
    EPITRAN_AVAILABLE = False
    logging.warning("epitran no está disponible. Se usarán solo reglas básicas.")

logger = logging.getLogger(__name__)

def generate_horse_ipa(horse_name):
    """Generar pronunciación IPA para nombres de caballos"""
    if not horse_name:
        return None
    
    # Diccionario de pronunciaciones específicas para nombres de caballos famosos
    horse_ipa_dict = {
        # Caballos famosos históricos
        'Secretariat': '/sɛkrɪtɛriət/',
        'Man o War': '/mæn oʊ wɔːr/',
        'Seabiscuit': '/siːbɪskɪt/',
        'Citation': '/saɪteɪʃən/',
        'Affirmed': '/əfɜːrmd/',
        'Alydar': '/ælɪdɑːr/',
        'Seattle Slew': '/siætəl sluː/',
        'American Pharoah': '/əmɛrɪkən fɛroʊ/',
        'Justify': '/dʒʌstɪfaɪ/',
        'Barbaro': '/bɑːrbəroʊ/',
        'Smarty Jones': '/smɑːrti dʒoʊnz/',
        'Funny Cide': '/fʌni saɪd/',
        'War Admiral': '/wɔːr ædmərəl/',
        'Whirlaway': '/wɜːrləweɪ/',
        'Count Fleet': '/kaʊnt fliːt/',
        'Assault': '/əsɔːlt/',
        'Gallant Fox': '/gælənt fɑːks/',
        'Omaha': '/oʊməhɑː/',
        'War Admiral': '/wɔːr ædmərəl/',
        'Triple Crown': '/trɪpəl kraʊn/',
        
        # Nombres comunes de caballos
        'Thunder': '/θʌndər/',
        'Lightning': '/laɪtnɪŋ/',
        'Storm': '/stɔːrm/',
        'Fire': '/faɪər/',
        'Flame': '/fleɪm/',
        'Spirit': '/spɪrɪt/',
        'Shadow': '/ʃædoʊ/',
        'Midnight': '/mɪdnaɪt/',
        'Starlight': '/stɑːrlaɪt/',
        'Moonbeam': '/muːnbiːm/',
        'Golden': '/goʊldən/',
        'Silver': '/sɪlvər/',
        'Diamond': '/daɪəmənd/',
        'Ruby': '/ruːbi/',
        'Emerald': '/ɛmərəld/',
        'Sapphire': '/sæfaɪər/',
        'Crystal': '/krɪstəl/',
        'Pearl': '/pɜːrl/',
        'Ivory': '/aɪvəri/',
        'Ebony': '/ɛbəni/',
        'Copper': '/kɑːpər/',
        'Bronze': '/brɑːnz/',
        'Steel': '/stiːl/',
        'Iron': '/aɪərn/',
        'Titan': '/taɪtən/',
        'Champion': '/tʃæmpiən/',
        'Victory': '/vɪktəri/',
        'Glory': '/glɔːri/',
        'Honor': '/ɑːnər/',
        'Pride': '/praɪd/',
        'Noble': '/noʊbəl/',
        'Royal': '/rɔɪəl/',
        'Majestic': '/məʤɛstɪk/',
        'Regal': '/riːgəl/',
        'Imperial': '/ɪmpɪriəl/',
        'Supreme': '/səpriːm/',
        'Elite': '/ɪliːt/',
        'Premier': '/prɪmɪər/',
        'Ultimate': '/ʌltəmət/',
        'Maximum': '/mæksɪməm/',
        'Optimal': '/ɑːptɪməl/',
        'Perfect': '/pɜːrfɪkt/',
        'Flawless': '/flɔːləs/',
        'Brilliant': '/brɪljənt/',
        'Radiant': '/reɪdiənt/',
        'Luminous': '/luːmɪnəs/',
        'Dazzling': '/dæzəlɪŋ/',
        'Sparkling': '/spɑːrkəlɪŋ/',
        'Shimmering': '/ʃɪmərɪŋ/',
        'Glittering': '/glɪtərɪŋ/',
        'Gleaming': '/gliːmɪŋ/',
        'Blazing': '/bleɪzɪŋ/',
        'Burning': '/bɜːrnɪŋ/',
        'Scorching': '/skɔːrtʃɪŋ/',
        'Searing': '/sɪrɪŋ/',
        'Fierce': '/fɪrs/',
        'Wild': '/waɪld/',
        'Free': '/friː/',
        'Swift': '/swɪft/',
        'Fast': '/fæst/',
        'Quick': '/kwɪk/',
        'Rapid': '/ræpɪd/',
        'Speedy': '/spiːdi/',
        'Fleet': '/fliːt/',
        'Dash': '/dæʃ/',
        'Rush': '/rʌʃ/',
        'Bolt': '/boʊlt/',
        'Flash': '/flæʃ/',
        'Zoom': '/zuːm/',
        'Rocket': '/rɑːkɪt/',
        'Comet': '/kɑːmɪt/',
        'Meteor': '/miːtiər/',
        'Star': '/stɑːr/',
        'Galaxy': '/gæləksi/',
        'Universe': '/juːnɪvɜːrs/',
        'Cosmos': '/kɑːzmoʊs/',
        'Infinity': '/ɪnfɪnəti/',
        'Eternity': '/ɪtɜːrnəti/',
        'Forever': '/fərɛvər/',
        'Always': '/ɔːlweɪz/',
        'Never': '/nɛvər/',
        'Ever': '/ɛvər/',
        'Once': '/wʌns/',
        'Twice': '/twaɪs/',
        'Thrice': '/θraɪs/',
        'Triple': '/trɪpəl/',
        'Double': '/dʌbəl/',
        'Single': '/sɪŋgəl/',
        'Solo': '/soʊloʊ/',
        'Lone': '/loʊn/',
        'Only': '/oʊnli/',
        'Unique': '/juːniːk/',
        'Special': '/spɛʃəl/',
        'Rare': '/rɛr/',
        'Precious': '/prɛʃəs/',
        'Valuable': '/væljuəbəl/',
        'Priceless': '/praɪsləs/',
        'Treasure': '/trɛʒər/',
        'Jewel': '/dʒuːəl/',
        'Gem': '/dʒɛm/',
        'Stone': '/stoʊn/',
        'Rock': '/rɑːk/',
        'Mountain': '/maʊntən/',
        'Hill': '/hɪl/',
        'Valley': '/væli/',
        'River': '/rɪvər/',
        'Ocean': '/oʊʃən/',
        'Sea': '/siː/',
        'Lake': '/leɪk/',
        'Pond': '/pɑːnd/',
        'Stream': '/striːm/',
        'Creek': '/kriːk/',
        'Brook': '/brʊk/',
        'Spring': '/sprɪŋ/',
        'Well': '/wɛl/',
        'Source': '/sɔːrs/',
        'Origin': '/ɔːrɪdʒɪn/',
        'Beginning': '/bɪgɪnɪŋ/',
        'Start': '/stɑːrt/',
        'End': '/ɛnd/',
        'Finish': '/fɪnɪʃ/',
        'Complete': '/kəmpliːt/',
        'Total': '/toʊtəl/',
        'Whole': '/hoʊl/',
        'Full': '/fʊl/',
        'Empty': '/ɛmpti/',
        'Void': '/vɔɪd/',
        'Null': '/nʌl/',
        'Zero': '/zɪroʊ/',
        'One': '/wʌn/',
        'First': '/fɜːrst/',
        'Last': '/læst/',
        'Final': '/faɪnəl/',
        'Ultimate': '/ʌltəmət/',
        'Supreme': '/səpriːm/',
        'Top': '/tɑːp/',
        'Best': '/bɛst/',
        'Greatest': '/greɪtəst/',
        'Finest': '/faɪnəst/',
        'Excellent': '/ɛksələnt/',
        'Outstanding': '/aʊtstændɪŋ/',
        'Exceptional': '/ɪksɛpʃənəl/',
        'Extraordinary': '/ɪkstrɔːrdənɛri/',
        'Remarkable': '/rɪmɑːrkəbəl/',
        'Amazing': '/əmeɪzɪŋ/',
        'Incredible': '/ɪnkrɛdəbəl/',
        'Fantastic': '/fæntæstɪk/',
        'Wonderful': '/wʌndərfəl/',
        'Marvelous': '/mɑːrvələs/',
        'Magnificent': '/mægnɪfəsənt/',
        'Splendid': '/splɛndɪd/',
        'Superb': '/səpɜːrb/',
        'Terrific': '/tərɪfɪk/',
        'Awesome': '/ɔːsəm/',
        'Fabulous': '/fæbjələs/',
        'Sensational': '/sɛnseɪʃənəl/',
        'Spectacular': '/spɛktækjələr/',
        'Phenomenal': '/fənɑːmənəl/',
        'Miraculous': '/mɪrækjələs/',
        'Divine': '/dɪvaɪn/',
        'Heavenly': '/hɛvənli/',
        'Celestial': '/səlɛstʃəl/',
        'Angelic': '/ændʒɛlɪk/',
        'Sacred': '/seɪkrəd/',
        'Holy': '/hoʊli/',
        'Blessed': '/blɛsəd/',
        'Pure': '/pjʊr/',
        'Clean': '/kliːn/',
        'Fresh': '/frɛʃ/',
        'New': '/nuː/',
        'Young': '/jʌŋ/',
        'Old': '/oʊld/',
        'Ancient': '/eɪnʃənt/',
        'Vintage': '/vɪntɪdʒ/',
        'Classic': '/klæsɪk/',
        'Traditional': '/trədɪʃənəl/',
        'Modern': '/mɑːdərn/',
        'Contemporary': '/kəntɛmpərɛri/',
        'Current': '/kɜːrənt/',
        'Present': '/prɛzənt/',
        'Future': '/fjuːtʃər/',
        'Past': '/pæst/',
        'History': '/hɪstəri/',
        'Legacy': '/lɛgəsi/',
        'Heritage': '/hɛrɪtɪdʒ/',
        'Tradition': '/trədɪʃən/',
        'Culture': '/kʌltʃər/',
        'Art': '/ɑːrt/',
        'Music': '/mjuːzɪk/',
        'Song': '/sɔːŋ/',
        'Dance': '/dæns/',
        'Poetry': '/poʊətri/',
        'Story': '/stɔːri/',
        'Tale': '/teɪl/',
        'Legend': '/lɛdʒənd/',
        'Myth': '/mɪθ/',
        'Dream': '/driːm/',
        'Vision': '/vɪʒən/',
        'Hope': '/hoʊp/',
        'Faith': '/feɪθ/',
        'Love': '/lʌv/',
        'Peace': '/piːs/',
        'Joy': '/dʒɔɪ/',
        'Happiness': '/hæpinəs/',
        'Bliss': '/blɪs/',
        'Harmony': '/hɑːrməni/',
        'Unity': '/juːnəti/',
        'Balance': '/bæləns/',
        'Equilibrium': '/iːkwəlɪbriəm/',
        'Stability': '/stəbɪləti/',
        'Strength': '/strɛŋθ/',
        'Power': '/paʊər/',
        'Force': '/fɔːrs/',
        'Energy': '/ɛnərdʒi/',
        'Vitality': '/vaɪtæləti/',
        'Life': '/laɪf/',
        'Soul': '/soʊl/',
        'Heart': '/hɑːrt/',
        'Mind': '/maɪnd/',
        'Spirit': '/spɪrɪt/',
        'Essence': '/ɛsəns/',
        'Nature': '/neɪtʃər/',
        'Earth': '/ɜːrθ/',
        'Sky': '/skaɪ/',
        'Heaven': '/hɛvən/',
        'Paradise': '/pærədaɪs/',
        'Eden': '/iːdən/',
        'Utopia': '/juːtoʊpiə/',
        'Nirvana': '/nɪrvɑːnə/',
        'Zen': '/zɛn/',
        'Karma': '/kɑːrmə/',
        'Destiny': '/dɛstəni/',
        'Fate': '/feɪt/',
        'Fortune': '/fɔːrtʃən/',
        'Luck': '/lʌk/',
        'Chance': '/tʃæns/',
        'Opportunity': '/ɑːpərtunəti/',
        'Possibility': '/pɑːsəbɪləti/',
        'Potential': '/pətɛnʃəl/',
        'Promise': '/prɑːməs/',
        'Future': '/fjuːtʃər/',
        'Tomorrow': '/təmɑːroʊ/',
        'Today': '/tədeɪ/',
        'Yesterday': '/jɛstərdeɪ/',
        'Now': '/naʊ/',
        'Then': '/ðɛn/',
        'When': '/wɛn/',
        'Where': '/wɛr/',
        'Why': '/waɪ/',
        'How': '/haʊ/',
        'What': '/wʌt/',
        'Who': '/huː/',
        'Which': '/wɪtʃ/',
        'Whose': '/huːz/',
        'Whom': '/huːm/',
        
        # Nombres de caballos del log actual
        'Strengthnguidance': '/strɛŋθ gaɪdəns/',
        'Top Maverick': '/tɑːp mævərɪk/',
        'Captain Cajun': '/kæptən keɪdʒən/',
        'Back Em Up': '/bæk ɛm ʌp/',
        'Loyal Clement': '/lɔɪəl klemɛnt/',
        'Lawler': '/lɔːlər/',
        'Divo d\'Oro': '/diːvoʊ dɔːroʊ/',
        'Losecontrol': '/luːz kəntroʊl/',
        'Anacapri': '/ænəkæpri/',
        'Crafty Collector': '/kræfti kəlɛktər/',
        'Smooth Claret': '/smuːð klærət/',
        'Money Trail': '/mʌni treɪl/',
        'Bubbles Up': '/bʌbəlz ʌp/',
        'Moonscape': '/muːnskeɪp/',
        'Worth Considering': '/wɜːrθ kənsɪdərɪŋ/',
    }
    
    # Buscar coincidencia exacta primero
    if horse_name in horse_ipa_dict:
        return horse_ipa_dict[horse_name]
    
    # Buscar coincidencias parciales
    for horse_key, ipa in horse_ipa_dict.items():
        if horse_name.lower() in horse_key.lower() or horse_key.lower() in horse_name.lower():
            return ipa
    
    # Si epitran está disponible, usarlo para traducción automática
    if EPITRAN_AVAILABLE:
        try:
            epi_eng = epitran.Epitran('eng-Latn')
            ipa_result = epi_eng.transliterate(horse_name)
            if ipa_result and ipa_result.strip():
                # Formatear con barras y espacios apropiados
                formatted_ipa = f'/{ipa_result.strip()}/'
                return formatted_ipa
        except Exception as e:
            logger.warning(f"Error usando epitran para '{horse_name}': {e}")
    
    # Si no se encuentra, generar una aproximación básica
    logger.warning(f"No se encontró pronunciación IPA específica para el caballo: {horse_name}")
    basic_ipa = generate_basic_horse_ipa(horse_name)
    return basic_ipa

def generate_basic_horse_ipa(horse_name):
    """Generar pronunciación IPA básica para nombres de caballos no reconocidos"""
    if not horse_name:
        return None
    
    # Aplicar reglas fonéticas básicas del inglés
    words = horse_name.split()
    ipa_parts = []
    
    for word in words:
        word_clean = word.lower().strip()
        if not word_clean:
            continue
            
        # Reglas básicas simplificadas para nombres de caballos
        ipa_word = ''
        i = 0
        while i < len(word_clean):
            char = word_clean[i]
            
            if char == 'a':
                # 'a' puede ser /æ/, /eɪ/, /ɑː/ dependiendo del contexto
                if i < len(word_clean) - 1 and word_clean[i+1] == 'r':
                    ipa_word += 'ɑːr'
                    i += 1  # saltar la 'r'
                elif i < len(word_clean) - 1 and word_clean[i+1] in 'wy':
                    ipa_word += 'eɪ'
                else:
                    ipa_word += 'æ'
            elif char == 'e':
                if i == len(word_clean) - 1:
                    pass  # e final silenciosa en muchos casos
                elif i < len(word_clean) - 1 and word_clean[i+1] == 'r':
                    ipa_word += 'ɜːr'
                    i += 1  # saltar la 'r'
                else:
                    ipa_word += 'ɛ'
            elif char == 'i':
                if i < len(word_clean) - 1 and word_clean[i+1] in 'gh':
                    ipa_word += 'aɪ'
                else:
                    ipa_word += 'ɪ'
            elif char == 'o':
                if i < len(word_clean) - 1 and word_clean[i+1] == 'r':
                    ipa_word += 'ɔːr'
                    i += 1  # saltar la 'r'
                elif i < len(word_clean) - 1 and word_clean[i+1] in 'wy':
                    ipa_word += 'oʊ'
                else:
                    ipa_word += 'ɑː'
            elif char == 'u':
                if i < len(word_clean) - 1 and word_clean[i+1] == 'r':
                    ipa_word += 'ɜːr'
                    i += 1  # saltar la 'r'
                else:
                    ipa_word += 'ʌ'
            elif char == 'y':
                if i == 0:  # y al inicio
                    ipa_word += 'j'
                else:  # y en medio o final
                    ipa_word += 'aɪ'
            elif char == 'c':
                if i < len(word_clean) - 1 and word_clean[i+1] in 'ei':
                    ipa_word += 's'
                else:
                    ipa_word += 'k'
            elif char == 'g':
                if i < len(word_clean) - 1 and word_clean[i+1] in 'ei':
                    ipa_word += 'dʒ'
                else:
                    ipa_word += 'g'
            elif char == 'ph':
                ipa_word += 'f'
            elif char == 'th':
                ipa_word += 'θ'  # th sorda por defecto
            elif char == 'sh':
                ipa_word += 'ʃ'
            elif char == 'ch':
                ipa_word += 'tʃ'
            elif char in 'bcdfhjklmnpqrstvwxz':
                ipa_word += char
            
            i += 1
        
        if ipa_word:
            ipa_parts.append(ipa_word)
    
    # Unir con espacios y agregar barras solo al principio y final
    ipa_result = f'/{" ".join(ipa_parts)}/'
    return ipa_result 