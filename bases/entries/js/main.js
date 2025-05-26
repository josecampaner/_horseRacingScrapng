/**
 * Funciones principales para la página de carreras
 */

// Función para buscar carreras mediante scraping
async function searchRaces() {
    const queryInput = document.getElementById('searchQuery');
    const urlToScrape = queryInput.value.trim();
    const resultsDiv = document.getElementById('raceResults');
    resultsDiv.innerHTML = '<p>Buscando...</p>';

    if (!urlToScrape) {
        resultsDiv.innerHTML = '<p>Por favor, introduce una URL para scrapear.</p>';
        return;
    }

    try {
        const response = await fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: urlToScrape })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Error del servidor: ${response.status}`);
        }
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        resultsDiv.innerHTML = `<p class="error-message">Error al buscar: ${error.message}</p>`;
        console.error('Error:', error);
    }
}

// Función para mostrar los resultados del scraping
function displayResults(data) {
    const resultsDiv = document.getElementById('raceResults');
    let html = '';

    // Manejar el formato de respuesta del endpoint /scrape
    if (data.success && data.races && Array.isArray(data.races)) {
        // Mostrar información de la página
        html += `<div class="success-message">`;
        html += `<h3>✅ Scraping Exitoso</h3>`;
        html += `<p><strong>Página:</strong> ${data.page_title || 'N/A'}</p>`;
        html += `<p><strong>Total de Carreras:</strong> ${data.total_races}</p>`;
        html += `<p><strong>URL:</strong> ${data.url}</p>`;
        html += `</div>`;
        
        // Procesar las carreras
        const races = data.races;
        if (races.length === 0) {
            html += '<p class="info-message">No se encontraron carreras en la página.</p>';
        } else {
            races.forEach((race, index) => {
                html += `<div class="race">`;
                html += `<h2>${race.title || race.raceTitle}</h2>`;
                
                // Mostrar todos los datos de la carrera organizados
                if (race.race_id) html += `<p><strong>Race ID:</strong> ${race.race_id}</p>`;
                if (race.distance) html += `<p><strong>Distancia:</strong> ${race.distance}</p>`;
                if (race.surface) html += `<p><strong>Superficie:</strong> ${race.surface}</p>`;
                if (race.race_type_from_detail || race.race_type) html += `<p><strong>Tipo:</strong> ${race.race_type_from_detail || race.race_type}</p>`;
                if (race.conditions_clean || race.conditions) html += `<p><strong>Condiciones:</strong> ${race.conditions_clean || race.conditions}</p>`;
                if (race.age_restriction_scraped || race.age_restriction) html += `<p><strong>Edad:</strong> ${race.age_restriction_scraped || race.age_restriction}</p>`;
                if (race.specific_race_url || race.url) html += `<p><strong>URL:</strong> <a href="${race.specific_race_url || race.url}" target="_blank">${race.specific_race_url || race.url}</a></p>`;

                
                // Agregar botón de scrapear caballos si tenemos race_id
                if (race.race_id) {
                    html += `<button onclick="scrapearCaballosCarrera('${race.race_id}')" class="action-btn">Scrapear Caballos de esta Carrera</button>`;
                }
                
                html += `<table class="participants-table">`;
                html += `<thead><tr><th>PP</th><th>Caballo</th><th>Sire</th><th>Entrenador</th><th>Jinete</th></tr></thead>`;
                html += `<tbody>`;
                if (race.participants && race.participants.length > 0) {
                    race.participants.forEach(p => {
                        html += `<tr><td>${p.pp || 'N/A'}</td><td><strong>${p.horse_name || p.horse || 'N/A'}</strong></td><td>${p.sire || 'N/A'}</td><td>${p.trainer || 'N/A'}</td><td>${p.jockey || 'N/A'}</td></tr>`;
                    });
                } else {
                    html += `<tr><td colspan="5">No se encontraron participantes para esta carrera.</td></tr>`;
                }
                html += `</tbody></table></div>`;
            });
        }
    } else if (data.message) { 
        html = `<p class="info-message">${data.message}</p>`;
        if(data.page_title) html += `<p>Título de la página: ${data.page_title}</p>`;
        if(data.url_processed) html += `<p>URL Procesada: ${data.url_processed}</p>`;
        if(data.data_found && data.data_found.length === 0) html += `<p>No se encontraron datos estructurados.</p>`;
    } else if (Array.isArray(data)) {
        // Formato antiguo (por compatibilidad)
        if (data.length === 0) {
            html += '<p class="info-message">No se encontraron carreras o no se pudo extraer la información con el formato esperado.</p>';
        } else {
            data.forEach(race => {
                html += `<div class="race">`;
                html += `<h2>${race.title || race.raceTitle}</h2>`;
                
                // Agregar botón de scrapear caballos si tenemos race_id
                if (race.race_id) {
                    html += `<button onclick="scrapearCaballosCarrera('${race.race_id}')" class="action-btn">🐎 Scrapear Caballos de esta Carrera</button>`;
                }
                
                html += `<table class="participants-table">`;
                html += `<thead><tr><th>Caballo</th><th>Sire</th><th>Entrenador</th><th>Jinete</th></tr></thead>`;
                html += `<tbody>`;
                if (race.participants && race.participants.length > 0) {
                    race.participants.forEach(p => {
                        html += `<tr><td><strong>${p.horse_name || p.horse || 'N/A'}</strong></td><td>${p.sire || 'N/A'}</td><td>${p.trainer || 'N/A'}</td><td>${p.jockey || 'N/A'}</td></tr>`;
                    });
                } else {
                    html += `<tr><td colspan="4">No se encontraron participantes para esta carrera.</td></tr>`;
                }
                html += `</tbody></table></div>`;
            });
        }
    } else {
         html = '<p class="error-message">Respuesta inesperada del servidor.</p>';
    }
    resultsDiv.innerHTML = html;
}

// Función para cargar carreras guardadas
async function cargarCarrerasGuardadas() {
    const listaDiv = document.getElementById('listaCarreras');
    const totalSpan = document.getElementById('totalCarreras');
    
    try {
        const response = await fetch('/api/races');
        const data = await response.json();
        
        totalSpan.textContent = data.total;
        
        if (data.races && data.races.length > 0) {
            let html = '';
            
            for (const race of data.races) {
                // Obtener participantes de cada carrera
                const entriesResponse = await fetch(`/api/races/${race.race_id}/entries`);
                const entriesData = await entriesResponse.json();
                
                html += `<div class="race">`;
                html += `<h2>Carrera #${race.race_number}</h2>`;
                html += `<p><strong>Race ID:</strong> ${race.race_id}</p>`;
                html += `<p><strong>Tipo de Carrera:</strong> ${race.race_type}</p>`;
                html += `<p><strong>Distancia:</strong> ${race.distance} | <strong>Superficie:</strong> ${race.surface}</p>`;
                html += `<p><strong>Condiciones:</strong> ${race.conditions}</p>`;
                html += `<p><strong>Edad:</strong> ${race.age_restriction}</p>`;
                html += `<p><strong>URL:</strong> <a href="${race.specific_race_url}" target="_blank">${race.specific_race_url}</a></p>`;
                html += `<button onclick="scrapearCaballosCarrera('${race.race_id}')" class="action-btn">🐎 Scrapear Caballos de esta Carrera</button>`;
                
                if (entriesData.entries && entriesData.entries.length > 0) {
                    html += `<table class="participants-table">`;
                    html += `<thead><tr><th>PP</th><th>Caballo</th><th>Sire</th><th>Entrenador</th><th>Jinete</th></tr></thead>`;
                    html += `<tbody>`;
                    
                    entriesData.entries.forEach(entry => {
                        html += `<tr>`;
                        html += `<td>${entry.post_position || 'N/A'}</td>`;
                        html += `<td><strong>${entry.horse_name || 'N/A'}</strong></td>`;
                        html += `<td>${entry.sire || 'N/A'}</td>`;
                        html += `<td>${entry.trainer || 'N/A'}</td>`;
                        html += `<td>${entry.jockey || 'N/A'}</td>`;
                        html += `</tr>`;
                    });
                    
                    html += `</tbody></table>`;
                }
                
                html += `</div>`;
            }
            
            listaDiv.innerHTML = html;
        } else {
            listaDiv.innerHTML = '<p class="info-message">No hay carreras guardadas.</p>';
        }
        
    } catch (error) {
        listaDiv.innerHTML = `<p class="error-message">Error cargando carreras: ${error.message}</p>`;
        console.error('Error:', error);
    }
}

// Función para scrapear caballos de una carrera específica
async function scrapearCaballosCarrera(raceId) {
    try {
        const response = await fetch(`/api/scrape-horses/${raceId}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert(`✅ Scraping completado: ${data.scraped_count} caballos procesados de la carrera ${raceId}`);
        } else {
            alert(`❌ Error: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Error scrapeando caballos: ${error.message}`);
        console.error('Error:', error);
    }
}

// Función para scrapear TODOS los caballos de todas las carreras
async function scrapearTodosLosCaballos() {
    if (!confirm('¿Estás seguro de que quieres scrapear TODOS los caballos de todas las carreras? Esto puede tomar varios minutos.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/scrape-all-horses', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert(`✅ Scraping masivo completado: ${data.total_horses} caballos procesados de ${data.total_races} carreras`);
        } else {
            alert(`❌ Error: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Error scrapeando todos los caballos: ${error.message}`);
        console.error('Error:', error);
    }
}

// Función para manejar teclas de acceso rápido
function handleKeyPress(event) {
    // Enter en el campo de búsqueda
    if (event.key === 'Enter' && event.target.id === 'searchQuery') {
        searchRaces();
    }
}

// Función para mostrar/ocultar loading
function showLoading(element, show = true) {
    if (show) {
        element.innerHTML = '<p class="info-message">⏳ Cargando...</p>';
    }
}

// Función para formatear fechas
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Función para validar URL
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Event listeners cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    // NO cargar carreras automáticamente - solo aparecen después del scraping
    
    // Agregar event listener para teclas
    document.addEventListener('keypress', handleKeyPress);
    
    // Agregar validación al campo de búsqueda
    const searchInput = document.getElementById('searchQuery');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const url = this.value.trim();
            const searchButton = document.querySelector('.search-container button');
            
            if (url && isValidUrl(url)) {
                searchButton.disabled = false;
                searchButton.style.opacity = '1';
            } else {
                searchButton.disabled = true;
                searchButton.style.opacity = '0.6';
            }
        });
    }
    
    console.log('🏇 Sistema de carreras cargado correctamente');
});