// JavaScript para scraping de caballos
document.addEventListener('DOMContentLoaded', function() {
    console.log('Página de scraping de caballos cargada');
});

// Función para manejar teclas de acceso rápido
function handleKeyPress(event) {
    // Enter en el campo de horse_id
    if (event.key === 'Enter' && event.target.id === 'horseId') {
        scrapeHorse();
    }
}

async function scrapeHorse() {
    const horseId = document.getElementById('horseId').value.trim();
    const resultsDiv = document.getElementById('horseResults');
    
    if (!horseId) {
        alert('Por favor ingresa el Horse ID');
        return;
    }
    
    // Construir la URL automáticamente
    const horseUrl = `https://www.horseracingnation.com/horse/${horseId}`;
    
    // Mostrar loading
    resultsDiv.innerHTML = '<div class="loading">🔍 Scrapeando datos del caballo...</div>';
    
    try {
        const response = await fetch('/api/scrape-horse-profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                horse_url: horseUrl
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayHorseData(result.horse_data);
        } else {
            resultsDiv.innerHTML = `<div class="error">❌ Error: ${result.error}</div>`;
        }
        
    } catch (error) {
        console.error('Error:', error);
        resultsDiv.innerHTML = `<div class="error">❌ Error al scrapear: ${error.message}</div>`;
    }
}

function displayHorseData(horseData) {
    const resultsDiv = document.getElementById('horseResults');
    
    let html = `
        <div class="horse-profile">
            <h2>🐎 ${horseData.horse_name || '-'}</h2>
            <div class="horse-details-grid">
                <div class="column-left">
                    <div class="detail-row">
                        <strong>Horse ID:</strong> ${horseData.horse_id || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>Propietario:</strong> ${horseData.owner || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>Entrenador:</strong> ${horseData.trainer || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>Criador:</strong> ${horseData.breeder || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>Color:</strong> ${horseData.color || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>Estado:</strong> ${horseData.status || '-'}
                    </div>
                </div>
                <div class="column-right">
                    <div class="detail-row">
                        <strong>Nombre IPA:</strong> ${horseData.horse_name_ipa || ''}
                    </div>
                    <div class="detail-row">
                        <strong>Propietario IPA:</strong> ${horseData.owner_ipa || ''}
                    </div>
                    <div class="detail-row">
                        <strong>Entrenador IPA:</strong> ${horseData.trainer_ipa || ''}
                    </div>
                    <div class="detail-row">
                        <strong>Criador IPA:</strong> ${horseData.breeder_ipa || ''}
                    </div>
                    <div class="detail-row">
                        <strong>Edad:</strong> ${horseData.age || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>Sexo:</strong> ${horseData.sex || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>País de Nacimiento:</strong> ${horseData.country_of_birth || '-'}
                    </div>
                </div>
            </div>
            ${displayPedigreeData(horseData.pedigree)}
        </div>
    `;
    
    resultsDiv.innerHTML = html;
}

function displayPedigreeData(pedigreeData) {
    if (!pedigreeData) {
        return '<div class="pedigree-section"><h3>🌳 Pedigree</h3><p>No hay datos de pedigree disponibles</p></div>';
    }
    
    // Función para limpiar valores inválidos
    function cleanPedigreeValue(value) {
        if (!value || value === 'N/A' || value.includes('horseedit.aspx')) {
            return '-';
        }
        return value;
    }
    
    return `
        <div class="pedigree-section">
            <h3>🌳 Pedigree</h3>
            <div class="pedigree-grid">
                <div class="pedigree-generation">
                    <h4>Padres</h4>
                    <div class="pedigree-row">
                        <strong>Padre (Sire):</strong> ${cleanPedigreeValue(pedigreeData.sire_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Madre (Dam):</strong> ${cleanPedigreeValue(pedigreeData.dam_id)}
                    </div>
                </div>
                
                <div class="pedigree-generation">
                    <h4>Abuelos</h4>
                    <div class="pedigree-row">
                        <strong>Abuelo Paterno:</strong> ${cleanPedigreeValue(pedigreeData.paternal_grandsire_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Abuela Paterna:</strong> ${cleanPedigreeValue(pedigreeData.paternal_granddam_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Abuelo Materno:</strong> ${cleanPedigreeValue(pedigreeData.maternal_grandsire_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Abuela Materna:</strong> ${cleanPedigreeValue(pedigreeData.maternal_granddam_id)}
                    </div>
                </div>
                
                <div class="pedigree-generation">
                    <h4>Bisabuelos</h4>
                    <div class="pedigree-row">
                        <strong>Bisabuelo Paterno (Sire):</strong> ${cleanPedigreeValue(pedigreeData.paternal_gg_sire_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Bisabuela Paterna (Dam):</strong> ${cleanPedigreeValue(pedigreeData.paternal_gg_dam_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Bisabuelo Paterno (Dam Sire):</strong> ${cleanPedigreeValue(pedigreeData.paternal_gd_sire_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Bisabuela Paterna (Dam Dam):</strong> ${cleanPedigreeValue(pedigreeData.paternal_gd_dam_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Bisabuelo Materno (Sire):</strong> ${cleanPedigreeValue(pedigreeData.maternal_gg_sire_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Bisabuela Materna (Dam):</strong> ${cleanPedigreeValue(pedigreeData.maternal_gg_dam_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Bisabuelo Materno (Dam Sire):</strong> ${cleanPedigreeValue(pedigreeData.maternal_gd_sire_id)}
                    </div>
                    <div class="pedigree-row">
                        <strong>Bisabuela Materna (Dam Dam):</strong> ${cleanPedigreeValue(pedigreeData.maternal_gd_dam_id)}
                    </div>
                </div>
            </div>
        </div>
    `;
}