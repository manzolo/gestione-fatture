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

const COMPARE_STORAGE_KEY = 'dashboard_compare_prev_year';

function isCompareEnabled() {
    return localStorage.getItem(COMPARE_STORAGE_KEY) === '1';
}

// Badge delta % rispetto all'anno precedente. Con invert=true un aumento è
// negativo (es. costi: se salgono, badge rosso).
function buildDeltaBadge(current, prev, { invert = false } = {}) {
    if (!prev) {
        return '<span class="badge bg-secondary">n/d</span>';
    }
    const pct = ((current - prev) / Math.abs(prev)) * 100;
    if (Math.abs(pct) < 0.05) {
        return '<span class="badge bg-secondary">=</span>';
    }
    const up = pct > 0;
    const good = invert ? !up : up;
    const cls = good ? 'bg-success' : 'bg-danger';
    const arrow = up ? '▲' : '▼';
    return `<span class="badge ${cls}">${arrow} ${Math.abs(pct).toFixed(1)}%</span>`;
}

export async function fetchDashboardStats(year = null, showLoadingNotification = true) {
    // Cancella la richiesta precedente se esiste
    if (currentRequest) {
        currentRequest.abort();
    }

    // Pulisci le notifiche esistenti per evitare accumulo
    notifications.clearAll();

    // Se year non è specificato, usa l'anno corrente
    if (year === null) {
        year = new Date().getFullYear();
    }
    year = parseInt(year, 10);

    const compare = isCompareEnabled();
    const prevYear = year - 1;

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

        const fetches = [
            fetch(urlInvoices, { signal: controller.signal }),
            fetch(urlCosts, { signal: controller.signal })
        ];

        // Con il confronto attivo, chiede anche le statistiche dell'anno precedente
        if (compare) {
            fetches.push(
                fetch(`/api/invoices/stats?year=${prevYear}`, { signal: controller.signal }),
                fetch(`/api/costs/stats?year=${prevYear}`, { signal: controller.signal })
            );
        }

        const [invoicesResponse, costsResponse, prevInvoicesResponse, prevCostsResponse] = await Promise.all(fetches);

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

        // I dati dell'anno precedente sono opzionali: se falliscono, il resto
        // della dashboard funziona comunque (badge "n/d", nessun layer nel grafico)
        let prevInvoicesData = null;
        let prevCostsData = null;
        if (compare && prevInvoicesResponse && prevInvoicesResponse.ok) {
            prevInvoicesData = await prevInvoicesResponse.json();
        }
        if (compare && prevCostsResponse && prevCostsResponse.ok) {
            prevCostsData = await prevCostsResponse.json();
        }

        const prevHasData = compare && (
            (prevInvoicesData && (parseInt(prevInvoicesData.totale_fatture) || 0) > 0) ||
            (prevCostsData && (parseFloat(prevCostsData.totale_annuo) || 0) > 0)
        );
        const comparison = prevHasData ? { prevYear, prevInvoicesData, prevCostsData } : null;

        if (compare && !prevHasData && !controller.signal.aborted) {
            notifications.info(`Nessun dato disponibile per il ${prevYear}: confronto non applicato.`, 4000);
        }

        if (statsContainer && !controller.signal.aborted) {
            // Estrae i dati corretti dalle rispettive API
            const totaleAnnualeFatturato = parseFloat(invoicesData.totale_annuo) || 0;
            const totaleCostiAnnuali = parseFloat(costsData.totale_annuo) || 0;
            const totaleFatture = parseInt(invoicesData.totale_fatture) || 0;
            const clientiFatturati = parseInt(invoicesData.clienti_con_fatture) || 0;
            const profitto = totaleAnnualeFatturato - totaleCostiAnnuali;

            // Riga delta sotto il valore della card (solo con confronto attivo)
            let deltaLine = () => '';
            if (compare) {
                const prevFatturato = parseFloat(prevInvoicesData?.totale_annuo) || 0;
                const prevCosti = parseFloat(prevCostsData?.totale_annuo) || 0;
                const prevValues = {
                    fatture: parseInt(prevInvoicesData?.totale_fatture) || 0,
                    clienti: parseInt(prevInvoicesData?.clienti_con_fatture) || 0,
                    fatturato: prevFatturato,
                    costi: prevCosti,
                    profitto: prevFatturato - prevCosti
                };
                deltaLine = (key, current, opts) => `
                    <div class="mb-1">${buildDeltaBadge(current, prevValues[key], opts)} <small class="text-muted">vs ${prevYear}</small></div>`;
            }

            statsContainer.innerHTML = `
                <div class="col-md-2-4">
                    <div class="card stat-card text-center">
                        <div class="card-body">
                            <i class="fas fa-file-invoice-dollar stat-icon text-primary"></i>
                            <h5 class="card-title mt-2">Totale Fatture</h5>
                            <p class="card-text fs-4 fw-bold mb-1">${totaleFatture}</p>
                            ${deltaLine('fatture', totaleFatture)}
                            <small class="text-muted">${yearText}</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-2-4">
                    <div class="card stat-card text-center">
                        <div class="card-body">
                            <i class="fas fa-users stat-icon text-info"></i>
                            <h5 class="card-title mt-2">Clienti Fatturati</h5>
                            <p class="card-text fs-4 fw-bold mb-1">${clientiFatturati}</p>
                            ${deltaLine('clienti', clientiFatturati)}
                            <small class="text-muted">${yearText}</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-2-4">
                    <div class="card stat-card text-center">
                        <div class="card-body">
                            <i class="fas fa-euro-sign stat-icon text-success"></i>
                            <h5 class="card-title mt-2">Fatturato ${year ? 'Annuo' : 'Complessivo'}</h5>
                            <p class="card-text fs-4 fw-bold text-success mb-1">€${totaleAnnualeFatturato.toFixed(2)}</p>
                            ${deltaLine('fatturato', totaleAnnualeFatturato)}
                            <small class="text-muted">${yearText}</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-2-4">
                    <div class="card stat-card text-center">
                        <div class="card-body">
                            <i class="fas fa-hand-holding-usd stat-icon text-danger"></i>
                            <h5 class="card-title mt-2">Costi ${year ? 'Annuali' : 'Complessivi'}</h5>
                            <p class="card-text fs-4 fw-bold text-danger mb-1">€${totaleCostiAnnuali.toFixed(2)}</p>
                            ${deltaLine('costi', totaleCostiAnnuali, { invert: true })}
                            <small class="text-muted">${yearText}</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-2-4">
                    <div class="card stat-card text-center">
                        <div class="card-body">
                            <i class="fas fa-chart-line stat-icon ${profitto >= 0 ? 'text-success' : 'text-danger'}"></i>
                            <h5 class="card-title mt-2">Profitto ${year ? 'Annuo' : 'Complessivo'}</h5>
                            <p class="card-text fs-4 fw-bold ${profitto >= 0 ? 'text-success' : 'text-danger'} mb-1">€${profitto.toFixed(2)}</p>
                            ${deltaLine('profitto', profitto)}
                            <small class="text-muted">${yearText}</small>
                        </div>
                    </div>
                </div>
            `;
        }

        // Renderizza i grafici solo se la richiesta non è stata cancellata
        if (!controller.signal.aborted) {
            setTimeout(() => {
                renderCharts(invoicesData, costsData, comparison);
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

function renderCharts(invoicesData, costsData, comparison = null) {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js non è caricato!');
        notifications.error('Errore: libreria grafici non disponibile.');
        return;
    }

    // Controlla se l'anno è stato selezionato
    const isSpecificYear = invoicesData.anno_selezionato !== null && invoicesData.anno_selezionato !== undefined;

    // Grafico combinato Fatturato e Costi per Mese/Anno
    const chartPerMese = document.getElementById('chartPerMese');
    if (chartPerMese) {
        try {
            if (chartPerMeseInstance) {
                chartPerMeseInstance.destroy();
            }

            let labels = [];
            let fatturatoValues = [];
            let costiValues = [];

            // Gestione dati per mese (quando è selezionato un anno specifico)
            if (isSpecificYear && invoicesData.per_mese && Array.isArray(invoicesData.per_mese)) {
                // Crea un array per tutti i 12 mesi
                const monthlyData = new Array(12).fill(0);
                const monthlyCosts = new Array(12).fill(0);

                // Popola i dati delle fatture
                invoicesData.per_mese.forEach(item => {
                    const monthIndex = parseInt(item.mese) - 1; // Converti a indice array (0-11)
                    if (monthIndex >= 0 && monthIndex < 12) {
                        monthlyData[monthIndex] = parseFloat(item.totale) || 0;
                    }
                });

                // Popola i dati dei costi
                if (costsData.per_mese && Array.isArray(costsData.per_mese)) {
                    costsData.per_mese.forEach(item => {
                        const monthIndex = parseInt(item.mese) - 1;
                        if (monthIndex >= 0 && monthIndex < 12) {
                            monthlyCosts[monthIndex] = parseFloat(item.totale) || 0;
                        }
                    });
                }

                labels = Object.values(MESE_MAPPINGS);
                fatturatoValues = monthlyData;
                costiValues = monthlyCosts;

            } else if (invoicesData.per_anno && Array.isArray(invoicesData.per_anno)) {
                // Gestione dati per anno
                const yearlyInvoices = new Map(invoicesData.per_anno.map(item => [parseInt(item.anno), parseFloat(item.totale) || 0]));
                const yearlyCosts = new Map();

                if (costsData.per_anno && Array.isArray(costsData.per_anno)) {
                    costsData.per_anno.forEach(item => {
                        yearlyCosts.set(parseInt(item.anno), parseFloat(item.totale) || 0);
                    });
                }

                // Ottieni tutti gli anni dalle fatture e dai costi
                const allYears = new Set([...yearlyInvoices.keys(), ...yearlyCosts.keys()]);
                const sortedYears = Array.from(allYears).sort();

                labels = sortedYears.map(year => year.toString());
                fatturatoValues = sortedYears.map(year => yearlyInvoices.get(year) || 0);
                costiValues = sortedYears.map(year => yearlyCosts.get(year) || 0);
            }

            // Layer di confronto: anno precedente come linee tratteggiate
            // sovrapposte alle barre (solo in vista mensile)
            let prevYearDatasets = [];
            if (isSpecificYear && comparison) {
                const prevMonthlyFatturato = new Array(12).fill(0);
                const prevMonthlyCosti = new Array(12).fill(0);

                (comparison.prevInvoicesData?.per_mese || []).forEach(item => {
                    const monthIndex = parseInt(item.mese) - 1;
                    if (monthIndex >= 0 && monthIndex < 12) {
                        prevMonthlyFatturato[monthIndex] = parseFloat(item.totale) || 0;
                    }
                });

                (comparison.prevCostsData?.per_mese || []).forEach(item => {
                    const monthIndex = parseInt(item.mese) - 1;
                    if (monthIndex >= 0 && monthIndex < 12) {
                        prevMonthlyCosti[monthIndex] = parseFloat(item.totale) || 0;
                    }
                });

                prevYearDatasets = [{
                    type: 'line',
                    label: `Fatturato ${comparison.prevYear} (€)`,
                    data: prevMonthlyFatturato,
                    borderColor: 'rgba(54, 162, 235, 0.9)',
                    backgroundColor: 'rgba(54, 162, 235, 0.9)',
                    borderDash: [6, 4],
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.25,
                    fill: false
                },
                {
                    type: 'line',
                    label: `Costi ${comparison.prevYear} (€)`,
                    data: prevMonthlyCosti,
                    borderColor: 'rgba(255, 99, 132, 0.9)',
                    backgroundColor: 'rgba(255, 99, 132, 0.9)',
                    borderDash: [6, 4],
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.25,
                    fill: false
                }];
            }

            const dynamicChartTitle = isSpecificYear
                ? (comparison
                    ? `Fatturato e Costi per Mese - ${invoicesData.anno_selezionato} vs ${comparison.prevYear}`
                    : `Fatturato e Costi per Mese - ${invoicesData.anno_selezionato}`)
                : 'Fatturato e Costi per Anno';

            chartPerMeseInstance = new Chart(chartPerMese, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Fatturato (€)',
                        data: fatturatoValues,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 2,
                        borderRadius: 4
                    },
                    {
                        label: 'Costi (€)',
                        data: costiValues,
                        backgroundColor: 'rgba(255, 99, 132, 0.6)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 2,
                        borderRadius: 4
                    },
                    ...prevYearDatasets]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 800,
                        easing: 'easeOutQuart'
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: dynamicChartTitle,
                            font: { size: 18, weight: 'bold' },
                            padding: { top: 10, bottom: 20 }
                        },
                        legend: {
                            position: 'top',
                            labels: {
                                font: { size: 12 },
                                color: '#444'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            titleFont: { size: 14, weight: 'bold' },
                            bodyFont: { size: 13 },
                            callbacks: {
                                label: ctx => `${ctx.dataset.label}: €${ctx.parsed.y.toLocaleString()}`
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0,0,0,0.05)',
                                drawBorder: false
                            },
                            ticks: {
                                font: { size: 12 },
                                callback: value => `€${value.toLocaleString()}`
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { font: { size: 12 } }
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

            // Colori più moderni e accattivanti
            const colors = [
                'rgba(255, 99, 132, 0.8)',
                'rgba(54, 162, 235, 0.8)',
                'rgba(255, 206, 86, 0.8)',
                'rgba(75, 192, 192, 0.8)',
                'rgba(153, 102, 255, 0.8)',
                'rgba(255, 159, 64, 0.8)',
                'rgba(255, 99, 255, 0.8)',
                'rgba(99, 255, 132, 0.8)',
                'rgba(132, 99, 255, 0.8)',
                'rgba(255, 206, 132, 0.8)'
            ];

            chartPerClienteInstance = new Chart(chartPerCliente, {
                type: 'doughnut', // Cambiato da 'pie' a 'doughnut' per un aspetto più moderno
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Fatture per Cliente',
                        data: values,
                        backgroundColor: colors,
                        borderColor: colors.map(color => color.replace('0.8', '1')),
                        borderWidth: 2,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    //cutout: '35%',
                    plugins: {
                        title: {
                            display: true,
                            text: 'Distribuzione Fatture per Cliente',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((context.parsed / total) * 100).toFixed(1);
                                    return `${context.label}: ${context.parsed} fatture (${percentage}%)`;
                                }
                            }
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

export async function initializeDashboard() {
    if (!isInitialized) {
        await setupDashboard();
        isInitialized = true;
    } else {
        const yearSelector = document.getElementById('yearSelector');
        const selectedYear = yearSelector ? (yearSelector.value || new Date().getFullYear()) : new Date().getFullYear();
        await fetchDashboardStats(selectedYear, false);
    }
}

async function setupDashboard() {
    const yearSelector = document.getElementById('yearSelector');
    if (!yearSelector) return;

    try {
        const response = await fetch('/api/invoices/years');
        const years = await response.json();
        const currentYear = new Date().getFullYear();

        // Pulisce le opzioni esistenti
        yearSelector.innerHTML = '';
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearSelector.appendChild(option);
        });

        // Imposta l'anno corrente come predefinito SEMPRE
        if (years.includes(currentYear)) {
            yearSelector.value = currentYear;
        } else {
            // Se l'anno corrente non ha fatture, prendi l'anno più recente
            const mostRecentYear = Math.max(...years);
            yearSelector.value = mostRecentYear;
        }

        // Rimuovi tutti i listener precedenti e aggiungi quello nuovo
        const newYearSelector = yearSelector.cloneNode(true);
        yearSelector.parentNode.replaceChild(newYearSelector, yearSelector);

        newYearSelector.addEventListener('change', onYearChange);

        // Switch confronto anno precedente (stato persistito in localStorage)
        const compareSwitch = document.getElementById('comparePrevYearSwitch');
        if (compareSwitch) {
            compareSwitch.checked = isCompareEnabled();
            compareSwitch.addEventListener('change', () => {
                localStorage.setItem(COMPARE_STORAGE_KEY, compareSwitch.checked ? '1' : '0');
                const ys = document.getElementById('yearSelector');
                const selected = ys ? (ys.value || new Date().getFullYear()) : new Date().getFullYear();
                fetchDashboardStats(selected, true);
            });
        }

        // Carica la dashboard con l'anno predefinito (sempre un anno specifico, mai "tutti gli anni")
        const selectedYear = newYearSelector.value || currentYear;
        await fetchDashboardStats(selectedYear);

    } catch (error) {
        console.error('Errore durante la configurazione della dashboard:', error);
        notifications.error('Errore nella configurazione della dashboard.');

        // Fallback: carica comunque la dashboard con l'anno corrente
        await fetchDashboardStats(new Date().getFullYear());
    }
}

function onYearChange() {
    const selectedYear = this.value || new Date().getFullYear();
    fetchDashboardStats(selectedYear, true); // true = mostra notifica di caricamento
}