// ====== DASHBOARD ========
let chartPerMeseInstance = null;
let chartPerClienteInstance = null;

const MESE_MAPPINGS = {
    1: 'Gen', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mag', 6: 'Giu',
    7: 'Lug', 8: 'Ago', 9: 'Set', 10: 'Ott', 11: 'Nov', 12: 'Dic'
};

export function fetchDashboardStats(year = null) {
    const url = year ? `/api/invoices/stats?year=${year}` : '/api/invoices/stats';
    fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { 
                    throw new Error(err.message || 'Errore nel recupero dei dati delle statistiche.'); 
                });
            }
            return response.json();
        })
        .then(data => {
            const statsContainer = document.getElementById('dashboard-stats');
            if (statsContainer) {
                const yearText = year ? `Anno ${year}` : 'Tutti gli anni';
                
                statsContainer.innerHTML = `
                    <div class="col-md-4">
                        <div class="card stat-card text-center">
                            <div class="card-body">
                                <i class="fas fa-file-invoice-dollar stat-icon"></i>
                                <h5 class="card-title mt-2">Totale Fatture</h5>
                                <p class="card-text fs-4">${data.totale_fatture}</p>
                                <small class="text-muted">${yearText}</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card stat-card text-center">
                            <div class="card-body">
                                <i class="fas fa-euro-sign stat-icon"></i>
                                <h5 class="card-title mt-2">Totale ${year ? 'Annuo' : 'Complessivo'}</h5>
                                <p class="card-text fs-4">€${data.totale_annuo.toFixed(2)}</p>
                                <small class="text-muted">${yearText}</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card stat-card text-center">
                            <div class="card-body">
                                <i class="fas fa-users stat-icon"></i>
                                <h5 class="card-title mt-2">Clienti Fatturati</h5>
                                <p class="card-text fs-4">${data.clienti_con_fatture}</p>
                                <small class="text-muted">${yearText}</small>
                            </div>
                        </div>
                    </div>
                `;
            }

            setTimeout(() => {
                renderCharts(data);
            }, 100);
        })
        .catch(error => {
            console.error('Errore nel recupero delle statistiche:', error);
            const statsContainer = document.getElementById('dashboard-stats');
            if (statsContainer) {
                statsContainer.innerHTML = '<div class="col-12"><p class="alert alert-danger">Errore nel caricare le statistiche: ' + error.message + '</p></div>';
            }
        });
}

function renderCharts(data) {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js non è caricato!');
        return;
    }
    
    const isSpecificYear = data.anno_selezionato !== null && data.anno_selezionato !== undefined;
    
    const chartTitle = document.getElementById('chartPerMeseTitle');
    if (chartTitle) {
        chartTitle.textContent = isSpecificYear 
            ? `Totale Fatturato per Mese - ${data.anno_selezionato}`
            : 'Totale Fatturato per Anno';
    }
    
    const chartPerMese = document.getElementById('chartPerMese');
    
    if (chartPerMese && data.per_mese && Array.isArray(data.per_mese)) {
        try {
            if (chartPerMeseInstance) {
                chartPerMeseInstance.destroy();
            }
            
            const labels = data.per_mese.map(item => {
                if (isSpecificYear) {
                    return MESE_MAPPINGS[item.mese] || `Mese ${item.mese}`;
                } else {
                    return `${item.mese}`;
                }
            });
            
            const values = data.per_mese.map(item => {
                return parseFloat(item.totale) || 0;
            });
            
            const dynamicChartTitle = isSpecificYear ? 'Fatturato per Mese' : 'Fatturato per Anno';
            
            chartPerMeseInstance = new Chart(chartPerMese, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Fatturato (€)',
                        data: values,
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: dynamicChartTitle
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Errore creazione grafico per mese:', error);
        }
    }

    const chartPerCliente = document.getElementById('chartPerCliente');
    
    if (chartPerCliente && data.per_cliente && Array.isArray(data.per_cliente)) {
        try {
            if (chartPerClienteInstance) {
                chartPerClienteInstance.destroy();
            }
            
            const labels = data.per_cliente.map(item => {
                return item.cliente || 'Cliente sconosciuto';
            });
            
            const values = data.per_cliente.map(item => {
                return parseInt(item.conteggio) || 0;
            });
            
            chartPerClienteInstance = new Chart(chartPerCliente, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Fatture per Cliente',
                        data: values,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.5)',
                            'rgba(54, 162, 235, 0.5)',
                            'rgba(255, 206, 86, 0.5)',
                            'rgba(75, 192, 192, 0.5)',
                            'rgba(153, 102, 255, 0.5)',
                            'rgba(255, 159, 64, 0.5)',
                            'rgba(255, 99, 255, 0.5)',
                            'rgba(99, 255, 132, 0.5)',
                            'rgba(132, 99, 255, 0.5)',
                            'rgba(255, 206, 132, 0.5)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)',
                            'rgba(255, 159, 64, 1)',
                            'rgba(255, 99, 255, 1)',
                            'rgba(99, 255, 132, 1)',
                            'rgba(132, 99, 255, 1)',
                            'rgba(255, 206, 132, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Distribuzione Fatture per Cliente'
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Errore creazione grafico per cliente:', error);
        }
    }
}

export function initializeDashboard() {
    populateYearSelector();
    fetchDashboardStats();
}

function populateYearSelector() {
    fetch('/api/invoices/years')
        .then(response => response.json())
        .then(years => {
            const yearSelector = document.getElementById('yearSelector');
            if (yearSelector) {
                yearSelector.innerHTML = '<option value="">Tutti gli anni</option>';
                years.forEach(year => {
                    const option = document.createElement('option');
                    option.value = year;
                    option.textContent = year;
                    yearSelector.appendChild(option);
                });
                
                yearSelector.addEventListener('change', function() {
                    const selectedYear = this.value || null;
                    fetchDashboardStats(selectedYear);
                });
            }
        })
        .catch(error => {
            console.error('Errore nel recupero degli anni:', error);
        });
}