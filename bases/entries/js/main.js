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
        const response = await fetch('/api/scrape', {
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
        
        // Mostrar la sección de carreras guardadas con el botón de scraping automático
        document.getElementById('carrerasGuardadas').style.display = 'block';
        document.getElementById('totalCarreras').textContent = data.total_races;
        
        // Calcular total de caballos
        let totalCaballos = 0;
        data.races.forEach(race => {
            if (race.participants && Array.isArray(race.participants)) {
                totalCaballos += race.participants.length;
            }
        });
        document.getElementById('totalCaballos').textContent = totalCaballos;
        
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
                html += `<thead><tr><th>Caballo</th><th>Entrenador</th><th>Jinete</th><th>Estado</th><th>Historial</th></tr></thead>`;
                html += `<tbody>`;
                if (race.participants && race.participants.length > 0) {
                    race.participants.forEach(p => {
                        const horseId = p.horse_id || 'N/A';
                        const status = p.status || 'active';
                        const statusText = status === 'scratched' ? '❌ Retirado' : status === 'withdrawn' ? '⚠️ Retirado' : '✅ OK';
                        const rowClass = status === 'scratched' || status === 'withdrawn' ? 'style="opacity: 0.6; background: #ffebee;"' : '';
                        
                        // Status History - MEJORADO
                        let historyHtml = '';
                        if (p.status_history) {
                            const historyLines = p.status_history.split('\n');
                            if (historyLines.length > 0) {
                                const latestHistory = historyLines[historyLines.length - 1];
                                if (latestHistory.includes('inicial → active')) {
                                    historyHtml = '<span style="color: #28a745; font-size: 0.9em;">🆕 Nuevo (Activo)</span>';
                                } else if (latestHistory.includes('inicial') || latestHistory.includes('scratched')) {
                                    historyHtml = '<span style="color: #dc3545; font-size: 0.9em;">🔄 Retirado inicial</span>';
                                } else if (latestHistory.includes('→')) {
                                    // Cambio de status detectado
                                    historyHtml = `<span style="color: #fd7e14; font-size: 0.9em;">📝 ${latestHistory.split(': ')[1]}</span>`;
                                } else {
                                    historyHtml = `<small style="color: #6c757d;">${latestHistory}</small>`;
                                }
                            }
                        } else {
                            // Sin historial - para backward compatibility
                            if (status === 'scratched') {
                                historyHtml = '<span style="color: #dc3545; font-size: 0.9em;">🔄 Retirado (sin historial)</span>';
                            } else {
                                historyHtml = '<span style="color: #6c757d; font-size: 0.9em;">⚠️ Sin historial</span>';
                            }
                        }
                        
                        html += `<tr ${rowClass}>`;
                        html += `<td><strong><code onclick="copyToClipboard('${horseId}')" style="cursor: pointer; background: #f0f0f0; padding: 2px 4px; border-radius: 3px;" title="Click para copiar Horse ID">${horseId}</code></strong></td>`;
                        html += `<td>${p.trainer || 'N/A'}</td>`;
                        html += `<td>${p.jockey || 'N/A'}</td>`;
                        html += `<td>${statusText}</td>`;
                        html += `<td>${historyHtml}</td>`;
                        html += `</tr>`;
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
                html += `<thead><tr><th>Caballo</th><th>Entrenador</th><th>Jinete</th><th>Estado</th><th>Historial</th></tr></thead>`;
                html += `<tbody>`;
                if (race.participants && race.participants.length > 0) {
                    race.participants.forEach(p => {
                        const horseId = p.horse_id || 'N/A';
                        const status = p.status || 'active';
                        const statusText = status === 'scratched' ? '❌ Retirado' : status === 'withdrawn' ? '⚠️ Retirado' : '✅ OK';
                        const rowClass = status === 'scratched' || status === 'withdrawn' ? 'style="opacity: 0.6; background: #ffebee;"' : '';
                        
                        // Status History - MEJORADO
                        let historyHtml = '';
                        if (p.status_history) {
                            const historyLines = p.status_history.split('\n');
                            if (historyLines.length > 0) {
                                const latestHistory = historyLines[historyLines.length - 1];
                                if (latestHistory.includes('inicial → active')) {
                                    historyHtml = '<span style="color: #28a745; font-size: 0.9em;">🆕 Nuevo (Activo)</span>';
                                } else if (latestHistory.includes('inicial') || latestHistory.includes('scratched')) {
                                    historyHtml = '<span style="color: #dc3545; font-size: 0.9em;">🔄 Retirado inicial</span>';
                                } else if (latestHistory.includes('→')) {
                                    // Cambio de status detectado
                                    historyHtml = `<span style="color: #fd7e14; font-size: 0.9em;">📝 ${latestHistory.split(': ')[1]}</span>`;
                                } else {
                                    historyHtml = `<small style="color: #6c757d;">${latestHistory}</small>`;
                                }
                            }
                        } else {
                            // Sin historial - para backward compatibility
                            if (status === 'scratched') {
                                historyHtml = '<span style="color: #dc3545; font-size: 0.9em;">🔄 Retirado (sin historial)</span>';
                            } else {
                                historyHtml = '<span style="color: #6c757d; font-size: 0.9em;">⚠️ Sin historial</span>';
                            }
                        }
                        
                        html += `<tr ${rowClass}><td><strong><code onclick="copyToClipboard('${horseId}')" style="cursor: pointer; background: #f0f0f0; padding: 2px 4px; border-radius: 3px;" title="Click para copiar Horse ID">${horseId}</code></strong><br><small>${p.horse_name || p.horse || 'N/A'}</small></td><td>${p.trainer || 'N/A'}</td><td>${p.jockey || 'N/A'}</td><td>${statusText}</td><td>${historyHtml}</td></tr>`;
                    });
                } else {
                    html += `<tr><td colspan="5">No se encontraron participantes para esta carrera.</td></tr>`;
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
        
        let totalCaballos = 0;  // Contador para todos los caballos
        
        if (data.races && data.races.length > 0) {
            let html = '';
            
            for (const race of data.races) {
                // Obtener participantes de cada carrera
                const entriesResponse = await fetch(`/api/races/${race.race_id}/entries`);
                const entriesData = await entriesResponse.json();
                
                // Contar caballos de esta carrera
                const caballosEnCarrera = entriesData.entries ? entriesData.entries.length : 0;
                totalCaballos += caballosEnCarrera;
                
                html += `<div class="race">`;
                html += `<h2>Carrera #${race.race_number}</h2>`;
                html += `<p><strong>Race ID:</strong> ${race.race_id}</p>`;
                html += `<p><strong>Tipo de Carrera:</strong> ${race.race_type}</p>`;
                html += `<p><strong>Distancia:</strong> ${race.distance} | <strong>Superficie:</strong> ${race.surface}</p>`;
                html += `<p><strong>Condiciones:</strong> ${race.conditions}</p>`;
                html += `<p><strong>Edad:</strong> ${race.age_restriction}</p>`;
                html += `<p><strong>URL:</strong> <a href="${race.specific_race_url}" target="_blank">${race.specific_race_url}</a></p>`;
                html += `<div style="display: flex; gap: 10px; margin: 10px 0;">`;
                html += `<button onclick="scrapearCaballosCarrera('${race.race_id}')" class="action-btn">🐎 Scrapear Caballos de esta Carrera</button>`;
                html += `</div>`;
                
                if (entriesData.entries && entriesData.entries.length > 0) {
                    html += `<table class="participants-table">`;
                    html += `<thead><tr><th>Caballo</th><th>Entrenador</th><th>Jinete</th><th>Estado</th><th>Historial</th></tr></thead>`;
                    html += `<tbody>`;
                    
                    entriesData.entries.forEach(entry => {
                        const status = entry.status || 'active';
                        const statusText = status === 'scratched' ? '❌ Retirado' : status === 'withdrawn' ? '⚠️ Retirado' : '✅ Activo';
                        const rowClass = status === 'scratched' || status === 'withdrawn' ? 'style="opacity: 0.6; background: #ffebee;"' : '';
                        
                        // Status History - MEJORADO
                        let historyHtml = '';
                        if (entry.status_history) {
                            const historyLines = entry.status_history.split('\n');
                            if (historyLines.length > 0) {
                                const latestHistory = historyLines[historyLines.length - 1];
                                if (latestHistory.includes('inicial → active')) {
                                    historyHtml = '<span style="color: #28a745; font-size: 0.9em;">🆕 Nuevo (Activo)</span>';
                                } else if (latestHistory.includes('inicial') || latestHistory.includes('scratched')) {
                                    historyHtml = '<span style="color: #dc3545; font-size: 0.9em;">🔄 Retirado inicial</span>';
                                } else if (latestHistory.includes('→')) {
                                    // Cambio de status detectado
                                    historyHtml = `<span style="color: #fd7e14; font-size: 0.9em;">📝 ${latestHistory.split(': ')[1]}</span>`;
                                } else {
                                    historyHtml = `<small style="color: #6c757d;">${latestHistory}</small>`;
                                }
                            }
                        } else {
                            // Sin historial - para backward compatibility
                            if (status === 'scratched') {
                                historyHtml = '<span style="color: #dc3545; font-size: 0.9em;">🔄 Retirado (sin historial)</span>';
                            } else {
                                historyHtml = '<span style="color: #6c757d; font-size: 0.9em;">⚠️ Sin historial</span>';
                            }
                        }
                        
                        html += `<tr ${rowClass}>`;
                        html += `<td><strong>${entry.horse_name || 'N/A'}</strong></td>`;
                        html += `<td>${entry.trainer || 'N/A'}</td>`;
                        html += `<td>${entry.jockey || 'N/A'}</td>`;
                        html += `<td>${statusText}</td>`;
                        html += `<td>${historyHtml}</td>`;
                        html += `</tr>`;
                    });
                    
                    html += `</tbody></table>`;
                }
                
                html += `</div>`;
            }
            
            listaDiv.innerHTML = html;
            
            // Actualizar contador de caballos
            document.getElementById('totalCaballos').textContent = totalCaballos;
        } else {
            listaDiv.innerHTML = '<p class="info-message">No hay carreras guardadas.</p>';
            // Si no hay carreras, poner contador de caballos en 0
            document.getElementById('totalCaballos').textContent = 0;
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

// Función para verificar retiros de última hora en una carrera
async function verificarRetirosCarrera(raceId) {
    try {
        // Mostrar indicador de carga
        const progressDiv = document.createElement('div');
        progressDiv.id = 'checking-scratches';
        progressDiv.innerHTML = `
            <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                        background: white; padding: 20px; border: 2px solid #17a2b8; border-radius: 10px; 
                        box-shadow: 0 4px 8px rgba(0,0,0,0.3); z-index: 1000; text-align: center;">
                <h3>🔍 Verificando Retiros...</h3>
                <p>Comprobando estado actual de los caballos en la carrera ${raceId}</p>
                <div style="width: 200px; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden;">
                    <div style="width: 100%; height: 100%; background: #17a2b8; animation: pulse 1.5s infinite;"></div>
                </div>
            </div>
        `;
        document.body.appendChild(progressDiv);
        
        const response = await fetch(`/api/races/${raceId}/check-scratches`, {
            method: 'POST'
        });
        const data = await response.json();
        
        // Remover indicador de progreso
        document.body.removeChild(progressDiv);
        
        if (data.success) {
            let mensaje = `🔍 Verificación de retiros completada!\n\n`;
            mensaje += `🐎 Caballos activos: ${data.active_horses ? data.active_horses.length : 0}\n`;
            mensaje += `❌ Caballos retirados: ${data.total_scratched}\n`;
            
            if (data.scratched_horses && data.scratched_horses.length > 0) {
                mensaje += `\n🚫 Retirados:\n`;
                data.scratched_horses.forEach(horse => {
                    mensaje += `• ${horse.horse_name} (${horse.horse_id})\n`;
                });
            }
            
            alert(mensaje);
            
            // Recargar la lista de carreras para mostrar estados actualizados
            setTimeout(() => {
                if (document.getElementById('listaCarreras')) {
                    cargarCarrerasGuardadas();
                }
            }, 1000);
        } else {
            alert(`❌ Error verificando retiros: ${data.error}`);
        }
    } catch (error) {
        // Remover indicador de progreso en caso de error
        if (document.getElementById('checking-scratches')) {
            document.body.removeChild(document.getElementById('checking-scratches'));
        }
        alert(`❌ Error verificando retiros: ${error.message}`);
        console.error('Error:', error);
    }
}

// Función para scrapear TODOS los caballos de todas las carreras mostradas en pantalla
async function scrapearTodosLosCaballos() {
    // Buscar todos los botones de scrapear carreras en la página
    const botonesScraping = document.querySelectorAll('button[onclick*="scrapearCaballosCarrera"]');
    
    if (botonesScraping.length === 0) {
        alert('❌ No se encontraron carreras para scrapear. Primero busca carreras usando la URL.');
        return;
    }
    
    if (!confirm(`¿Estás seguro de que quieres scrapear TODOS los caballos de las ${botonesScraping.length} carreras mostradas? Esto puede tomar varios minutos.`)) {
        return;
    }
    
    let totalCaballos = 0;
    let carrerasExitosas = 0;
    let errores = [];
    
    // Mostrar progreso
    const progressDiv = document.createElement('div');
    progressDiv.id = 'scraping-progress';
    progressDiv.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    background: white; padding: 20px; border: 2px solid #007bff; border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3); z-index: 1000; text-align: center;">
            <h3>🐎 Scrapeando Caballos...</h3>
            <p id="progress-text">Iniciando...</p>
            <div style="width: 300px; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden;">
                <div id="progress-bar" style="width: 0%; height: 100%; background: #007bff; transition: width 0.3s;"></div>
            </div>
            <p><small>Carrera <span id="current-race">0</span> de ${botonesScraping.length}</small></p>
        </div>
    `;
    document.body.appendChild(progressDiv);
    
    try {
        for (let i = 0; i < botonesScraping.length; i++) {
            const boton = botonesScraping[i];
            const onclickAttr = boton.getAttribute('onclick');
            const raceIdMatch = onclickAttr.match(/scrapearCaballosCarrera\('([^']+)'\)/);
            
            if (!raceIdMatch) continue;
            
            const raceId = raceIdMatch[1];
            
            // Actualizar progreso
            document.getElementById('progress-text').textContent = `Scrapeando carrera: ${raceId}`;
            document.getElementById('current-race').textContent = i + 1;
            document.getElementById('progress-bar').style.width = `${((i + 1) / botonesScraping.length) * 100}%`;
            
            try {
                const response = await fetch(`/api/scrape-horses/${raceId}`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    totalCaballos += data.scraped_count;
                    carrerasExitosas++;
                    console.log(`✅ Carrera ${raceId}: ${data.scraped_count} caballos scrapeados`);
                } else {
                    errores.push(`Carrera ${raceId}: ${data.error}`);
                    console.error(`❌ Error en carrera ${raceId}: ${data.error}`);
                }
            } catch (error) {
                errores.push(`Carrera ${raceId}: ${error.message}`);
                console.error(`❌ Error scrapeando carrera ${raceId}:`, error);
            }
            
            // Pequeña pausa entre carreras para no sobrecargar el servidor
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        // Remover indicador de progreso
        document.body.removeChild(progressDiv);
        
        // Mostrar resultado final
        let mensaje = `✅ Scraping completado!\n\n`;
        mensaje += `🐎 Total de caballos scrapeados: ${totalCaballos}\n`;
        mensaje += `🏁 Carreras exitosas: ${carrerasExitosas}/${botonesScraping.length}\n`;
        
        if (errores.length > 0) {
            mensaje += `\n❌ Errores encontrados:\n${errores.slice(0, 5).join('\n')}`;
            if (errores.length > 5) {
                mensaje += `\n... y ${errores.length - 5} errores más (ver consola)`;
            }
        }
        
        alert(mensaje);
        
    } catch (error) {
        // Remover indicador de progreso en caso de error
        if (document.getElementById('scraping-progress')) {
            document.body.removeChild(progressDiv);
        }
        alert(`❌ Error general scrapeando caballos: ${error.message}`);
        console.error('Error:', error);
    }
}

// Función para revisar y actualizar caballos que no se han actualizado en los últimos 20 días
async function revisarYActualizarCaballos() {
    if (!confirm('¿Quieres revisar y actualizar todos los caballos que no se han actualizado en los últimos 20 días? Esto puede tomar varios minutos.')) {
        return;
    }
    
    // Mostrar progreso
    const progressDiv = document.createElement('div');
    progressDiv.id = 'updating-progress';
    progressDiv.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    background: white; padding: 20px; border: 2px solid #f39c12; border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3); z-index: 1000; text-align: center;">
            <h3>🔍 Revisando y Actualizando Caballos...</h3>
            <p id="update-progress-text">Iniciando revisión...</p>
            <div style="width: 300px; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden;">
                <div id="update-progress-bar" style="width: 0%; height: 100%; background: #f39c12; transition: width 0.3s;"></div>
            </div>
            <p><small>Por favor espera...</small></p>
        </div>
    `;
    document.body.appendChild(progressDiv);
    
    try {
        document.getElementById('update-progress-text').textContent = 'Revisando caballos que necesitan actualización...';
        document.getElementById('update-progress-bar').style.width = '30%';
        
        const response = await fetch('/api/check-and-update-horses', {
            method: 'POST'
        });
        
        document.getElementById('update-progress-bar').style.width = '100%';
        
        const data = await response.json();
        
        // Remover indicador de progreso
        document.body.removeChild(progressDiv);
        
        if (data.success) {
            let mensaje = `✅ Revisión completada!\n\n`;
            mensaje += `🔍 Caballos que necesitaban actualización: ${data.horses_to_update}\n`;
            mensaje += `✅ Caballos ya actualizados: ${data.already_updated}\n`;
            mensaje += `🐎 Caballos actualizados exitosamente: ${data.scraped_count}\n`;
            
            if (data.errors && data.errors.length > 0) {
                mensaje += `\n❌ Errores encontrados: ${data.errors.length}\n`;
                mensaje += `${data.errors.slice(0, 3).join('\n')}`;
                if (data.errors.length > 3) {
                    mensaje += `\n... y ${data.errors.length - 3} errores más (ver consola)`;
                }
            }
            
            alert(mensaje);
            console.log('Resultado completo:', data);
        } else {
            alert(`❌ Error: ${data.error}`);
        }
        
    } catch (error) {
        // Remover indicador de progreso en caso de error
        if (document.getElementById('updating-progress')) {
            document.body.removeChild(progressDiv);
        }
        alert(`❌ Error revisando caballos: ${error.message}`);
        console.error('Error:', error);
    }
}

// Función para verificar retiros de TODAS las carreras de una vez
async function verificarTodosLosRetiros() {
    if (!confirm('¿Estás seguro de que quieres verificar retiros de TODAS las carreras? Esto puede tomar varios minutos.')) {
        return;
    }
    
    // Mostrar progreso
    const progressDiv = document.createElement('div');
    progressDiv.id = 'checking-all-scratches';
    progressDiv.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    background: white; padding: 20px; border: 2px solid #17a2b8; border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3); z-index: 1000; text-align: center;">
            <h3>🔍 Verificando Retiros de TODAS las Carreras...</h3>
            <p>Comprobando estado actual de los caballos en todas las carreras</p>
            <div style="width: 200px; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden;">
                <div style="width: 100%; height: 100%; background: #17a2b8; animation: pulse 1.5s infinite;"></div>
            </div>
        </div>
    `;
    document.body.appendChild(progressDiv);
    
    try {
        const response = await fetch('/api/check-all-scratches', {
            method: 'POST'
        });
        const data = await response.json();
        
        // Remover indicador de progreso
        document.body.removeChild(progressDiv);
        
        if (data.success) {
            let mensaje = `🔍 Verificación de retiros completada!\n\n`;
            mensaje += `🐎 Caballos activos: ${data.active_horses ? data.active_horses.length : 0}\n`;
            mensaje += `❌ Caballos retirados: ${data.total_scratched}\n`;
            
            if (data.scratched_horses && data.scratched_horses.length > 0) {
                mensaje += `\n🚫 Retirados:\n`;
                data.scratched_horses.forEach(horse => {
                    mensaje += `• ${horse.horse_name} (${horse.horse_id})\n`;
                });
            }
            
            alert(mensaje);
            
            // Recargar la lista de carreras para mostrar estados actualizados
            setTimeout(() => {
                if (document.getElementById('listaCarreras')) {
                    cargarCarrerasGuardadas();
                }
            }, 1000);
        } else {
            alert(`❌ Error verificando retiros: ${data.error}`);
        }
    } catch (error) {
        // Remover indicador de progreso en caso de error
        if (document.getElementById('checking-all-scratches')) {
            document.body.removeChild(document.getElementById('checking-all-scratches'));
        }
        alert(`❌ Error verificando retiros: ${error.message}`);
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

// Función para copiar texto al portapapeles
function copyToClipboard(text) {
    if (text === 'N/A') {
        alert('❌ No hay Horse ID válido para copiar');
        return;
    }
    
    navigator.clipboard.writeText(text).then(function() {
        // Mostrar confirmación visual temporal
        const notification = document.createElement('div');
        notification.innerHTML = `✅ Horse ID copiado: <strong>${text}</strong>`;
        notification.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10000;
            background: #28a745; color: white; padding: 10px 15px;
            border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            font-size: 14px; font-weight: bold;
        `;
        document.body.appendChild(notification);
        
        // Remover después de 2 segundos
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 2000);
    }).catch(function(err) {
        console.error('Error copiando al portapapeles: ', err);
        alert(`❌ Error copiando. Horse ID: ${text}`);
    });
}

// Función para revisar pedigree y añadir caballos faltantes
async function revisarPedigreeYAñadirCaballos() {
    console.log('🧬 Iniciando revisión de pedigree...');
    
    try {
        const response = await fetch('/api/pedigree/check-missing-horses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();
        
        if (data.success) {
            const message = `✅ Proceso completado:
            
📊 Resumen:
• Caballos encontrados en pedigree: ${data.total_pedigree_horses}
• Caballos ya existentes en horses: ${data.horses_already_exist}
• Nuevos caballos añadidos: ${data.horses_added}

${data.horses_added > 0 ? '🎉 ¡Se añadieron nuevos caballos a la tabla horses!' : '✅ Todos los caballos del pedigree ya estaban en la tabla horses.'}`;
            
            alert(message);
            
            // Recargar contador de caballos si estamos en la vista de carreras
            setTimeout(() => {
                if (document.getElementById('listaCarreras')) {
                    cargarCarrerasGuardadas();
                }
            }, 1000);
        } else {
            alert(`❌ Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Error al revisar pedigree:', error);
        alert(`❌ Error de conexión: ${error.message}`);
    }
}

// Función para revisar y scrapear solo caballos con campos NULL
async function revisarCaballosNull() {
    if (!confirm('¿Quieres revisar y scrapear solo los caballos que tienen campos NULL (updated_at IS NULL)? Esto puede tomar varios minutos.')) {
        return;
    }
    
    // Mostrar progreso
    const progressDiv = document.createElement('div');
    progressDiv.id = 'null-horses-progress';
    progressDiv.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    background: white; padding: 20px; border: 2px solid #f39c12; border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3); z-index: 1000; text-align: center;">
            <h3>⚠️ Scrapeando Caballos NULL...</h3>
            <p id="null-progress-text">Buscando caballos con campos NULL...</p>
            <div style="width: 300px; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden;">
                <div id="null-progress-bar" style="width: 0%; height: 100%; background: #f39c12; transition: width 0.3s;"></div>
            </div>
            <p><small>Por favor espera...</small></p>
        </div>
    `;
    document.body.appendChild(progressDiv);
    
    try {
        document.getElementById('null-progress-text').textContent = 'Procesando caballos con updated_at NULL...';
        document.getElementById('null-progress-bar').style.width = '50%';
        
        const response = await fetch('/api/scrape-null-horses', {
            method: 'POST'
        });
        
        document.getElementById('null-progress-bar').style.width = '100%';
        
        const data = await response.json();
        
        // Remover indicador de progreso
        document.body.removeChild(progressDiv);
        
        if (data.success) {
            let mensaje = `✅ Scraping de caballos NULL completado!\n\n`;
            mensaje += `🔍 Caballos NULL encontrados: ${data.null_horses_found}\n`;
            mensaje += `✅ Caballos scrapeados exitosamente: ${data.scraped_count}\n`;
            
            if (data.errors && data.errors.length > 0) {
                mensaje += `\n❌ Errores encontrados: ${data.errors.length}\n`;
                mensaje += `${data.errors.slice(0, 3).join('\n')}`;
                if (data.errors.length > 3) {
                    mensaje += `\n... y ${data.errors.length - 3} errores más (ver consola)`;
                }
            }
            
            alert(mensaje);
            console.log('Resultado completo:', data);
            
            // Recargar contador de caballos
            setTimeout(() => {
                if (document.getElementById('listaCarreras')) {
                    cargarCarrerasGuardadas();
                }
            }, 1000);
        } else {
            alert(`❌ Error: ${data.error}`);
        }
        
    } catch (error) {
        // Remover indicador de progreso en caso de error
        if (document.getElementById('null-horses-progress')) {
            document.body.removeChild(progressDiv);
        }
        alert(`❌ Error scrapeando caballos NULL: ${error.message}`);
        console.error('Error:', error);
    }
}