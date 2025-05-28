# 🏇 Horse Racing Scraping - Instrucciones de Instalación

## 📋 Requisitos Previos
- Python 3.8+
- PostgreSQL
- Git

## 🚀 Instalación Completa

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd _horseRacingScrapng
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias Python
```bash
pip install -r requirements.txt
```

### 4. ⚠️ IMPORTANTE: Instalar navegadores de Playwright
```bash
playwright install
```

### 5. Configurar base de datos PostgreSQL
```bash
# Crear base de datos
createdb -U macm1 caballos_db

# Ejecutar migraciones (si las hay)
python database/create_tables.py
```

### 6. Ejecutar la aplicación
```bash
python app.py
```

## 🔧 Solución de Problemas

### Error: "Executable doesn't exist at .../chromium_headless_shell"
**Solución:** Ejecutar `playwright install`

### Error de conexión a PostgreSQL
**Solución:** Verificar que PostgreSQL esté corriendo y las credenciales sean correctas

### Error de importación de módulos
**Solución:** Verificar que el entorno virtual esté activado

## 📝 Notas
- Playwright requiere dos pasos: instalar el paquete Python Y los navegadores
- Los navegadores de Playwright ocupan ~300MB de espacio
- La primera ejecución puede tardar más mientras se descargan los navegadores 