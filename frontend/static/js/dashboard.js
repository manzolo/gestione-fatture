// ====== DASHBOARD CON NOTIFICHE UNIFICATE - VERSIONE CORRETTA ========
import { notifications } from './notifications.js';

let chartPerMeseInstance = null;
let chartPerClienteInstance = null;
let isInitialized = false; // Flag per evitare inizializzazioni multiple
let currentRequest = null; // Per cancellare richieste precedenti

const MESE_MAPPINGS = {
    1: 'Gen', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mag', 6: 'Giu',
    7: 'Lug', 8: 'Ago', 9: 'Set', 10: 'Ott', 11: 'Nov', 12: 'Dic'
};

export async function fetchDashboardStats(year = null, showLoadingNotification = true) {
    // Cancella la richiesta precedente se esiste
    if (currentRequest) {
        currentRequest.abort();
    }

    // Pulisci le notifiche esistenti per evitare accumulo
    notifications.clearAll();

    const yearText = year ? `Anno ${year}` : 'Tutti gli anni';
    const statsContainer = document.getElementById('dashboard-stats');

    if (statsContainer) {
        statsContainer.innerHTML = `
            <div class="col-12"><p class="alert alert-info text-center">Caricamento statistiche in corso...</p></div>
        `;
    }

    // Mostra notifica di caricamento solo se richiesto
    let loadingNotification = null;
    if (showLoadingNotification) {
        loadingNotification = notifications.info('Caricamento statistiche dashboard...', 0); // 0 = non auto-remove
    }

    try {
        // Crea un AbortController per questa richiesta
        const controller = new AbortController();
        currentRequest = controller;

        const urlInvoices = year ? `/api/invoices/stats?year=${year}` : '/api/invoices/stats';
        const urlCosts = year ? `/api/costs/stats?year=${year}` : '/api/costs/stats';

        const [invoicesResponse, costsResponse] = await Promise.all([
            fetch(urlInvoices, { signal: controller.signal }),
            fetch(urlCosts, { signal: controller.signal })
        ]);

        // Controlla se la richiesta è stata cancellata
        if (controller.signal.aborted) {
            return;
        }

        if (!invoicesResponse.ok) {
            const err = await invoicesResponse.json();
            throw new Error(err.message || 'Errore nel recupero dei dati delle fatture.');
        }

        if (!costsResponse.ok) {
            const err = await costsResponse.json();
            throw new Error(err.message || 'Errore nel recupero dei dati dei costi.');
        }

        const invoicesData = await invoicesResponse.json();
        const costsData = await costsResponse.json();
        
        if (statsContainer && !controller.signal.aborted) {
            // Estrae i dati corretti dalle rispettive API
            const totaleAnnualeFatturato = parseFloat(invoicesData.totale_annuo) || 0;
            const totaleCostiAnnuali = parseFloat(costsData.totale_annuo) || 0;
            const totaleFatture = parseInt(invoicesData.totale_fatture) || 0;
            const clientiFatturati = parseInt(invoicesData.clienti_con_fatture) || 0;
            const profitto = totaleAnnualeFatturato - totaleCostiAnnuali;

            statsContainer.innerHTML = `
                <div class="col-md-3">
                    <div class="card stat-card text-center">
                        <div class="card-body">
                            <i class="fas fa-file-invoice-dollar stat-icon"></i>
                            <h5 class="card-title mt-2">Totale Fatture</h5>
                            <p class="card-text fs-4">${totaleFatture}</p>
                            <small class="text-muted">${yearText}</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card text-center">
                        <div class="card-body">
                            <i class="fas fa-euro-sign stat-icon"></i>
                            <h5 class="card-title mt-2">Fatturato ${year ? 'Annuo' : 'Complessivo'}</h5>
                            <p class="card-text fs-4 text-success">€${totaleAnnualeFatturato.toFixed(2)}</p>
                            <small class="text-muted">${yearText}</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card text-center">
                        <div class="card-body">
                            <i class="fas fa-hand-holding-usd stat-icon"></i>
                            <h5 class="card-title mt-2">Costi ${year ? 'Annuali' : 'Complessivi'}</h5>
                            <p class="card-text fs-4 text-danger">€${totaleCostiAnnuali.toFixed(2)}</p>
                            <small class="text-muted">${yearText}</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card text-center">
                        <div class="card-body">
                            <i class="fas fa-chart-line stat-icon"></i>
                            <h5 class="card-title mt-2">Profitto ${year ? 'Annuo' : 'Complessivo'}</h5>
                            <p class="card-text fs-4 ${profitto >= 0 ? 'text-success' : 'text-danger'}">€${profitto.toFixed(2)}</p>
                            <small class="text-muted">${yearText}</small>
                        </div>
                    </div>
                </div>
            `;
        }

        // Renderizza i grafici solo se la richiesta non è stata cancellata
        if (!controller.signal.aborted) {
            setTimeout(() => {
                renderCharts(invoicesData, costsData);
            }, 100);
        }

        // Rimuovi la notifica di caricamento e mostra successo
        if (loadingNotification) {
            notifications.remove(loadingNotification);
        }
        
        if (!controller.signal.aborted) {
            notifications.success('Statistiche dashboard caricate con successo!', 3000);
        }

    } catch (error) {
        // Se l'errore è dovuto a cancellazione, non mostrare nulla
        if (error.name === 'AbortError') {
            return;
        }

        console.error('Errore nel recupero delle statistiche:', error);
        
        // Rimuovi la notifica di caricamento
        if (loadingNotification) {
            notifications.remove(loadingNotification);
        }

        if (statsContainer) {
            statsContainer.innerHTML = '<div class="col-12"><p class="alert alert-danger">Errore nel caricare le statistiche: ' + error.message + '</p></div>';
        }
        notifications.error('Errore nel caricamento delle statistiche: ' + error.message);
    } finally {
        // Reset del currentRequest
        if (currentRequest && currentRequest.signal && !currentRequest.signal.aborted) {
            currentRequest = null;
        }
    }
}

function renderCharts(invoicesData, costsData) {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js non è caricato!');
        notifications.error('Errore: libreria grafici non disponibile.');
        return;
    }
    
    // Controlla se l'anno è stato selezionato
    const isSpecificYear = invoicesData.anno_selezionato !== null && invoicesData.anno_selezionato !== undefined;
    
    // Grafico combinato Fatturato e Costi per Mese/Anno
    const chartPerMese = document.getElementById('chartPerMese');
    if (chartPerMese && invoicesData.per_mese && Array.isArray(invoicesData.per_mese) && costsData.per_mese && Array.isArray(costsData.per_mese)) {
        try {
            if (chartPerMeseInstance) {
                chartPerMeseInstance.destroy();
            }

            const labels = invoicesData.per_mese.map(item => {
                if (isSpecificYear) {
                    return MESE_MAPPINGS[item.mese] || `Mese ${item.mese}`;
                } else {
                    return `${item.anno}`;
                }
            });
            
            const fatturatoValues = invoicesData.per_mese.map(item => parseFloat(item.totale) || 0);
            
            // Mappa i costi per mese per allinearsi con i mesi del fatturato
            const costsMap = new Map(costsData.per_mese.map(item => [isSpecificYear ? item.mese : item.anno, parseFloat(item.totale) || 0]));
            const costiValues = labels.map(label => {
                let key = isSpecificYear ? Object.keys(MESE_MAPPINGS).find(k => MESE_MAPPINGS[k] === label) : parseInt(label);
                return costsMap.get(key) || 0;
            });
            
            const dynamicChartTitle = isSpecificYear 
                ? `Fatturato e Costi per Mese - ${invoicesData.anno_selezionato}` 
                : 'Fatturato e Costi per Anno';
            
            chartPerMeseInstance = new Chart(chartPerMese, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Fatturato (€)',
                        data: fatturatoValues,
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Costi (€)',
                        data: costiValues,
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderColor: 'rgba(255, 99, 132, 1)',
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
            notifications.error('Errore nella creazione del grafico fatturato/costi.');
        }
    }

    // Grafico a torta delle fatture per cliente
    const chartPerCliente = document.getElementById('chartPerCliente');
    
    if (chartPerCliente && invoicesData.per_cliente && Array.isArray(invoicesData.per_cliente)) {
        try {
            if (chartPerClienteInstance) {
                chartPerClienteInstance.destroy();
            }
            
            const labels = invoicesData.per_cliente.map(item => {
                return item.cliente || 'Cliente sconosciuto';
            });
            
            const values = invoicesData.per_cliente.map(item => {
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
            notifications.error('Errore nella creazione del grafico per cliente.');
        }
    }
}

export function initializeDashboard() {
    const dashboardTab = document.getElementById('dashboard-tab');
    if (dashboardTab) {
        // Rimuovi eventuali listener precedenti
        const newDashboardTab = dashboardTab.cloneNode(true);
        dashboardTab.parentNode.replaceChild(newDashboardTab, dashboardTab);
        
        newDashboardTab.addEventListener('shown.bs.tab', async function () {
            // Pulisci le notifiche quando si entra nella dashboard
            notifications.clearAll();
            
            if (!isInitialized) {
                await setupDashboard();
                isInitialized = true;
            } else {
                // Se già inizializzato, ricarica solo i dati
                const yearSelector = document.getElementById('yearSelector');
                const selectedYear = yearSelector ? yearSelector.value || null : null;
                await fetchDashboardStats(selectedYear, false); // false = non mostrare notifica di caricamento
            }
        });
        
        // Pulisci le notifiche quando si esce dalla dashboard
        newDashboardTab.addEventListener('hide.bs.tab', function () {
            notifications.clearAll();
        });
    }
}

async function setupDashboard() {
    const yearSelector = document.getElementById('yearSelector');
    if (!yearSelector) return;
    
    try {
        const response = await fetch('/api/invoices/years');
        const years = await response.json();
        
        // Pulisce le opzioni esistenti
        yearSelector.innerHTML = '<option value="">Tutti gli anni</option>';
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearSelector.appendChild(option);
        });
        
        // Imposta l'anno corrente come predefinito
        const currentYear = new Date().getFullYear();
        if (years.includes(currentYear)) {
            yearSelector.value = currentYear;
        } else {
            yearSelector.value = '';
        }
        
        // Rimuovi tutti i listener precedenti e aggiungi quello nuovo
        const newYearSelector = yearSelector.cloneNode(true);
        yearSelector.parentNode.replaceChild(newYearSelector, yearSelector);
        
        newYearSelector.addEventListener('change', onYearChange);

        // Carica la dashboard con l'anno predefinito
        await fetchDashboardStats(newYearSelector.value || null);

    } catch (error) {
        console.error('Errore durante la configurazione della dashboard:', error);
        notifications.error('Errore nella configurazione della dashboard.');
    }
}

function onYearChange() {
    const selectedYear = this.value || null;
    fetchDashboardStats(selectedYear, true); // true = mostra notifica di caricamento
}