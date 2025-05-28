#!/usr/bin/env python3
"""
Script para actualizar todos los caballos en la base de datos
Extrae datos completos y pedigree de HorseRacingNation.com

Uso:
    python scripts/update_all_horses.py
    python scripts/update_all_horses.py --batch-size 10 --delay 2
"""

import sys
import os
import time
import argparse
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.database import get_db_connection
from services.scraping_service import scrape_horse_profile, update_horse_data
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/update_all_horses.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_all_horse_ids():
    """Obtener todos los horse_id de la base de datos"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT horse_id FROM horses ORDER BY horse_id")
        results = cursor.fetchall()
        
        horse_ids = [row[0] for row in results]
        
        cursor.close()
        connection.close()
        
        logger.info(f"Encontrados {len(horse_ids)} caballos en la base de datos")
        return horse_ids
        
    except Exception as e:
        logger.error(f"Error obteniendo horse_ids: {e}")
        return []

def update_single_horse(horse_id, retry_count=3):
    """Actualizar un solo caballo con reintentos"""
    for attempt in range(retry_count):
        try:
            logger.info(f"Procesando {horse_id} (intento {attempt + 1}/{retry_count})")
            
            # Generar nombre del caballo desde el ID
            horse_name = horse_id.replace('_', ' ')
            
            # Scrapear datos del caballo
            horse_data = scrape_horse_profile(horse_id, horse_name)
            
            if horse_data:
                # Guardar en base de datos
                connection = get_db_connection()
                cursor = connection.cursor()
                
                update_horse_data(cursor, horse_id, horse_data)
                connection.commit()
                
                cursor.close()
                connection.close()
                
                logger.info(f"✅ {horse_id} actualizado correctamente")
                return True
            else:
                logger.warning(f"⚠️ No se pudieron extraer datos para {horse_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error procesando {horse_id} (intento {attempt + 1}): {e}")
            if attempt < retry_count - 1:
                time.sleep(5)  # Esperar antes del siguiente intento
            
    logger.error(f"❌ Falló definitivamente: {horse_id}")
    return False

def main():
    parser = argparse.ArgumentParser(description='Actualizar todos los caballos de la base de datos')
    parser.add_argument('--batch-size', type=int, default=5, help='Número de caballos a procesar por lote (default: 5)')
    parser.add_argument('--delay', type=float, default=3.0, help='Segundos de espera entre caballos (default: 3.0)')
    parser.add_argument('--start-from', type=str, help='Horse ID desde donde empezar (para continuar proceso interrumpido)')
    parser.add_argument('--limit', type=int, help='Límite de caballos a procesar (para pruebas)')
    
    args = parser.parse_args()
    
    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)
    
    logger.info("🚀 Iniciando actualización masiva de caballos")
    logger.info(f"Configuración: batch_size={args.batch_size}, delay={args.delay}s")
    
    # Obtener todos los horse_ids
    horse_ids = get_all_horse_ids()
    
    if not horse_ids:
        logger.error("No se encontraron caballos para procesar")
        return
    
    # Filtrar desde donde empezar si se especifica
    if args.start_from:
        try:
            start_index = horse_ids.index(args.start_from)
            horse_ids = horse_ids[start_index:]
            logger.info(f"Continuando desde {args.start_from} ({len(horse_ids)} caballos restantes)")
        except ValueError:
            logger.error(f"Horse ID {args.start_from} no encontrado")
            return
    
    # Aplicar límite si se especifica
    if args.limit:
        horse_ids = horse_ids[:args.limit]
        logger.info(f"Limitando a {args.limit} caballos")
    
    # Estadísticas
    total_horses = len(horse_ids)
    successful = 0
    failed = 0
    start_time = datetime.now()
    
    logger.info(f"📊 Procesando {total_horses} caballos...")
    
    # Procesar caballos
    for i, horse_id in enumerate(horse_ids, 1):
        logger.info(f"🐎 [{i}/{total_horses}] Procesando: {horse_id}")
        
        success = update_single_horse(horse_id)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Mostrar progreso cada 10 caballos
        if i % 10 == 0:
            elapsed = datetime.now() - start_time
            rate = i / elapsed.total_seconds() * 60  # caballos por minuto
            eta_minutes = (total_horses - i) / rate if rate > 0 else 0
            
            logger.info(f"📈 Progreso: {i}/{total_horses} ({i/total_horses*100:.1f}%) - "
                       f"Exitosos: {successful}, Fallidos: {failed} - "
                       f"Velocidad: {rate:.1f} caballos/min - "
                       f"ETA: {eta_minutes:.1f} min")
        
        # Esperar entre caballos para no sobrecargar el servidor
        if i < total_horses:  # No esperar después del último
            time.sleep(args.delay)
    
    # Estadísticas finales
    end_time = datetime.now()
    total_time = end_time - start_time
    
    logger.info("🏁 Actualización completada!")
    logger.info(f"📊 Estadísticas finales:")
    logger.info(f"   Total procesados: {total_horses}")
    logger.info(f"   Exitosos: {successful}")
    logger.info(f"   Fallidos: {failed}")
    logger.info(f"   Tasa de éxito: {successful/total_horses*100:.1f}%")
    logger.info(f"   Tiempo total: {total_time}")
    logger.info(f"   Velocidad promedio: {total_horses/total_time.total_seconds()*60:.1f} caballos/min")
    
    # Guardar lista de fallidos para reprocesar
    if failed > 0:
        failed_file = f"logs/failed_horses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        # Aquí podrías guardar la lista de caballos que fallaron
        logger.info(f"💾 Lista de fallidos guardada en: {failed_file}")

if __name__ == "__main__":
    main() 