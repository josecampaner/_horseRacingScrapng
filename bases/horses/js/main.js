// JavaScript para scraping de caballos
document.addEventListener('DOMContentLoaded', function() {
    console.log('Página de scraping de caballos cargada');
});

async function scrapeHorse() {
    const horseUrl = document.getElementById('horseUrl').value.trim();
    const resultsDiv = document.getElementById('scrapeResults');
    
    if (!horseUrl) {
        alert('Por favor ingresa la URL del caballo');
        return;
    }
    
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
    const resultsDiv = document.getElementById('scrapeResults');
    
    let html = `
        <div class="horse-profile">
            <h2>🐎 ${horseData.horse_name || 'N/A'}</h2>
            <div class="horse-details">
                <div class="detail-row">
                    <strong>Horse ID:</strong> ${horseData.horse_id || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Nombre IPA:</strong> ${horseData.horse_name_ipa || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Edad:</strong> ${horseData.age || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Sexo:</strong> ${horseData.sex || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Color:</strong> ${horseData.color || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Propietario:</strong> ${horseData.owner || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Propietario IPA:</strong> ${horseData.owner_ipa || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Entrenador:</strong> ${horseData.trainer || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Entrenador IPA:</strong> ${horseData.trainer_ipa || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Criador:</strong> ${horseData.breeder || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Criador IPA:</strong> ${horseData.breeder_ipa || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>País de Nacimiento:</strong> ${horseData.country_of_birth || 'N/A'}
                </div>
                <div class="detail-row">
                    <strong>Estado:</strong> ${horseData.status || 'N/A'}
                </div>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
}