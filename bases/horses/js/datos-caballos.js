/**
 * Módulo JavaScript para datos de caballos integrado con pedigree
 * Maneja la visualización completa de datos de caballos y pedigree
 */

class DatosCaballos {
    constructor() {
        console.log('🐎 DatosCaballos módulo inicializado');
        this.currentHorseData = null;
        this.currentPedigreeData = null;
    }

    /**
     * Realizar scraping de un caballo
     * @param {string} horseId - ID del caballo
     */
    async scrapeHorse(horseId) {
        console.log(`🔍 Iniciando scraping para: ${horseId}`);
        
        const resultsDiv = document.getElementById('horseResults');
        
        try {
            // Mostrar loading
            resultsDiv.innerHTML = this.generateLoadingHTML();
            
            // Hacer la petición de scraping
            const response = await fetch(`/api/scrape-horse/${encodeURIComponent(horseId)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }

            const result = await response.json();
            console.log('📊 Datos recibidos:', result);

            // Guardar datos actuales
            this.currentHorseData = result;

            // Generar HTML completo con datos y pedigree
            const htmlContent = this.generateCompleteHorseHTML(result);
            resultsDiv.innerHTML = htmlContent;

        } catch (error) {
            console.error('❌ Error en scraping:', error);
            resultsDiv.innerHTML = this.generateErrorHTML(error.message);
        }
    }

    /**
     * Generar HTML completo del caballo con pedigree integrado
     * @param {Object} result - Resultado del scraping
     * @returns {string} HTML completo
     */
    generateCompleteHorseHTML(result) {
        if (!result.success) {
            return this.generateErrorHTML(result.message || 'Error en el scraping');
        }

        const formattedData = this.formatHorseData(result);
        
        return `
            <div class="complete-horse-profile">
                ${this.generateHorseDataHTML(formattedData)}
                ${this.generatePedigreeSection(result)}
            </div>
        `;
    }

    /**
     * Formatear datos del caballo
     * @param {Object} result - Resultado de la API
     * @returns {Object} Datos formateados
     */
    formatHorseData(result) {
        const horseData = result.data_updated || {};
        const horseId = result.horse_id || horseData.horse_id || '-';
        
        // Crear nombre limpio: quitar _ y cualquier número al final
        const cleanName = horseId.replace(/_/g, ' ').replace(/\s*\d+$/, '').trim();
        
        return {
            horseId,
            cleanName,
            age: horseData.age || 'No disponible',
            sex: horseData.sex || 'No disponible',
            color: horseData.color || 'No disponible',
            owner: horseData.owner || 'No disponible',
            trainer: horseData.trainer || 'No disponible',
            breeder: horseData.breeder || 'No disponible',
            countryOfBirth: horseData.country_of_birth || 'No disponible',
            status: horseData.status || 'No disponible',
            profileUrl: horseData.profile_url || result.profile_url || '#',
            horseNameIPA: horseData.horse_name_ipa || 'No disponible',
            ownerIPA: horseData.owner_ipa || 'No disponible',
            trainerIPA: horseData.trainer_ipa || 'No disponible',
            breederIPA: horseData.breeder_ipa || 'No disponible'
        };
    }

    /**
     * Generar HTML para los datos básicos del caballo
     * @param {Object} data - Datos formateados del caballo
     * @returns {string} HTML de los datos
     */
    generateHorseDataHTML(data) {
        return `
            <div class="horse-profile">
                <h2>🐎 ${data.horseId}</h2>
                <div class="horse-details-grid">
                    <div class="horse-details-column">
                        <div class="detail-item">
                            <strong>Nombre:</strong> <span class="value">${data.cleanName}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Propietario:</strong> <span class="value">${data.owner}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Entrenador:</strong> <span class="value">${data.trainer}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Criador:</strong> <span class="value">${data.breeder}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Sexo:</strong> <span class="value">${data.sex}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Color:</strong> <span class="value">${data.color}</span>
                        </div>
                        <div class="detail-item">
                            <strong>URL:</strong> <a href="${data.profileUrl}" target="_blank" class="profile-link">Ver perfil</a>
                        </div>
                    </div>
                    <div class="horse-details-column">
                        <div class="detail-item">
                            <strong>Nombre IPA:</strong> <span class="ipa-text">${data.horseNameIPA}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Propietario IPA:</strong> <span class="ipa-text">${data.ownerIPA}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Entrenador IPA:</strong> <span class="ipa-text">${data.trainerIPA}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Criador IPA:</strong> <span class="ipa-text">${data.breederIPA}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Edad:</strong> <span class="value">${data.age}</span>
                        </div>
                        <div class="detail-item">
                            <strong>País:</strong> <span class="value">${data.countryOfBirth}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Estado:</strong> <span class="value">${data.status}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Generar sección de pedigree usando el módulo de pedigree
     * @param {Object} result - Resultado del scraping con datos de pedigree
     * @returns {string} HTML del pedigree
     */
    generatePedigreeSection(result) {
        // Verificar si hay datos de pedigree
        const pedigreeData = result.data_updated?.pedigree || result.pedigree;
        
        if (!pedigreeData) {
            return `
                <div class="pedigree-section">
                    <h3>🌳 Pedigree</h3>
                    <div class="pedigree-empty">
                        <p>No hay datos de pedigree disponibles</p>
                    </div>
                </div>
            `;
        }

        // Formatear datos para el módulo de pedigree
        const formattedPedigree = this.formatPedigreeForViewer(pedigreeData, result.horse_id);
        
        // Usar el visor de pedigree si está disponible
        if (window.pedigreeViewer) {
            return window.pedigreeViewer.generatePedigreeHTML(formattedPedigree);
        }

        // Fallback si el módulo de pedigree no está disponible
        return this.generateBasicPedigreeHTML(pedigreeData);
    }

    /**
     * Formatear datos de pedigree para el visor
     * @param {Object} pedigreeData - Datos de pedigree
     * @param {string} horseId - ID del caballo
     * @returns {Object} Datos formateados para el visor
     */
    formatPedigreeForViewer(pedigreeData, horseId) {
        // Función para limpiar valores
        const cleanValue = (value) => {
            if (!value || value === 'N/A' || value.includes('horseedit.aspx')) {
                return null;
            }
            return value.replace('_', ' ');
        };

        const generations = {
            parents: {
                sire: cleanValue(pedigreeData.sire_id),
                dam: cleanValue(pedigreeData.dam_id)
            },
            grandparents: {
                paternal_grandsire: cleanValue(pedigreeData.paternal_grandsire_id),
                paternal_granddam: cleanValue(pedigreeData.paternal_granddam_id),
                maternal_grandsire: cleanValue(pedigreeData.maternal_grandsire_id),
                maternal_granddam: cleanValue(pedigreeData.maternal_granddam_id)
            },
            great_grandparents: {
                paternal_gg_sire: cleanValue(pedigreeData.paternal_gg_sire_id),
                paternal_gg_dam: cleanValue(pedigreeData.paternal_gg_dam_id),
                maternal_gg_sire: cleanValue(pedigreeData.maternal_gg_sire_id),
                maternal_gg_dam: cleanValue(pedigreeData.maternal_gg_dam_id)
            }
        };

        // Calcular completitud
        const totalFields = 14;
        const filledFields = Object.values(generations).reduce((count, gen) => {
            return count + Object.values(gen).filter(v => v !== null).length;
        }, 0);
        const completeness = Math.round((filledFields / totalFields) * 100);

        return {
            exists: true,
            horse_id: horseId,
            completeness,
            formatted_data: {
                horse_id: horseId,
                generations,
                completeness
            },
            inbreeding_analysis: {
                inbreeding_coefficient: 0,
                common_ancestors: [],
                total_ancestors: filledFields,
                duplicates: 0
            }
        };
    }

    /**
     * Generar HTML básico de pedigree (fallback)
     * @param {Object} pedigreeData - Datos de pedigree
     * @returns {string} HTML básico del pedigree
     */
    generateBasicPedigreeHTML(pedigreeData) {
        const cleanValue = (value) => value && value !== 'N/A' ? value.replace('_', ' ') : 'Desconocido';

        return `
            <div class="pedigree-section">
                <h3>🌳 Pedigree</h3>
                <div class="basic-pedigree">
                    <div class="pedigree-generation">
                        <h4>Padres</h4>
                        <div class="parent-info">
                            <div><strong>Padre:</strong> ${cleanValue(pedigreeData.sire_id)}</div>
                            <div><strong>Madre:</strong> ${cleanValue(pedigreeData.dam_id)}</div>
                        </div>
                    </div>
                    <div class="pedigree-generation">
                        <h4>Abuelos</h4>
                        <div class="grandparent-info">
                            <div><strong>Abuelo Paterno:</strong> ${cleanValue(pedigreeData.paternal_grandsire_id)}</div>
                            <div><strong>Abuela Paterna:</strong> ${cleanValue(pedigreeData.paternal_granddam_id)}</div>
                            <div><strong>Abuelo Materno:</strong> ${cleanValue(pedigreeData.maternal_grandsire_id)}</div>
                            <div><strong>Abuela Materna:</strong> ${cleanValue(pedigreeData.maternal_granddam_id)}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Generar HTML de loading
     * @returns {string} HTML de loading
     */
    generateLoadingHTML() {
        return `
            <div class="loading">
                <p>🔍 Scrapeando datos del caballo...</p>
                <p>Por favor espera mientras obtenemos la información completa.</p>
            </div>
        `;
    }

    /**
     * Generar HTML de error
     * @param {string} message - Mensaje de error
     * @returns {string} HTML de error
     */
    generateErrorHTML(message) {
        return `
            <div class="error">
                <h3>❌ Error en el Scraping</h3>
                <p><strong>Mensaje:</strong> ${message}</p>
                <p>Por favor verifica el Horse ID e intenta nuevamente.</p>
            </div>
        `;
    }

    /**
     * Limpiar resultados
     */
    clearResults() {
        const resultsDiv = document.getElementById('horseResults');
        if (resultsDiv) {
            resultsDiv.innerHTML = '';
        }
        this.currentHorseData = null;
        this.currentPedigreeData = null;
    }
}

// Instancia global
window.datosCaballos = new DatosCaballos();

// Funciones globales para compatibilidad
window.scrapeHorse = function() {
    const horseId = document.getElementById('horseId').value.trim();
    if (!horseId) {
        alert('Por favor ingresa el Horse ID');
        return;
    }
    window.datosCaballos.scrapeHorse(horseId);
};

window.clearResults = function() {
    window.datosCaballos.clearResults();
};

// Manejar tecla Enter
function handleKeyPress(event) {
    if (event.key === 'Enter' && event.target.id === 'horseId') {
        scrapeHorse();
    }
}

console.log('🐎 Módulo DatosCaballos cargado exitosamente'); 