// ----- Helper per mostrare tab (usato dal pulsante "Vai a Clienti") -----
function showTabById(tabButtonSelector) {
    const tabEl = document.querySelector(tabButtonSelector);
    if (tabEl) new bootstrap.Tab(tabEl).show();
}

document.addEventListener('DOMContentLoaded', function() {
    // Inizializzazione bottone vai a clienti
    const gotoClientsBtn = document.getElementById('gotoClientsBtn');
    if (gotoClientsBtn) {
        gotoClientsBtn.addEventListener('click', function () {
            showTabById('#clients-tab');
        });
    }
});

// ----- Inizializzazione Select2 (per i select clienti nelle fatture) -----
$(document).ready(function () {
    // Select2 per aggiunta fattura
    if ($('#cliente_id').length) {
        $('#cliente_id').select2({
            dropdownParent: $('#addInvoiceModal'),
            placeholder: "Seleziona un cliente",
            allowClear: true,
            width: '100%'
        });
    }
    
    // Select2 per modifica fattura
    if ($('#edit-cliente_id').length) {
        $('#edit-cliente_id').select2({
            dropdownParent: $('#editInvoiceModal'),
            placeholder: "Seleziona un cliente",
            allowClear: true,
            width: '100%'
        });
    }
});

// ===========================
// ====== CLIENTI CRUD =======
// ===========================
let clientToDelete = null;

// Aggiunta nuovo cliente
const addClientForm = document.getElementById('addClientForm');
if (addClientForm) {
    addClientForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());

        fetch('/api/clients', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
            .then(response => {
                if (!response.ok) throw new Error('Errore durante l\'aggiunta del cliente.');
                window.location.reload();
            })
            .catch(error => {
                console.error('Errore:', error);
                alert('Si è verificato un errore durante l\'aggiunta del cliente.');
            });
    });
}

// Apertura modale modifica cliente
function openEditClientModal(clientId) {
    fetch(`/api/clients/${clientId}`)
        .then(response => {
            if (!response.ok) throw new Error('Errore recupero cliente');
            return response.json();
        })
        .then(data => {
            document.getElementById('edit-client-id').value = data.id;
            document.getElementById('edit-nome').value = data.nome;
            document.getElementById('edit-cognome').value = data.cognome;
            document.getElementById('edit-codice_fiscale').value = data.codice_fiscale;
            document.getElementById('edit-indirizzo').value = data.indirizzo || '';
            document.getElementById('edit-citta').value = data.citta || '';
            document.getElementById('edit-cap').value = data.cap || '';

            new bootstrap.Modal(document.getElementById('editClientModal')).show();
        })
        .catch(error => {
            console.error('Errore:', error);
            alert('Errore nel recupero dei dati del cliente.');
        });
}

// Salvataggio modifiche cliente
const editClientForm = document.getElementById('editClientForm');
if (editClientForm) {
    editClientForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const clientId = document.getElementById('edit-client-id').value;
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());

        fetch(`/api/clients/${clientId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
            .then(response => {
                if (!response.ok) return response.json().then(err => { throw new Error(err.message || 'Errore'); });
                window.location.reload();
            })
            .catch(error => {
                console.error('Errore:', error);
                alert(error.message || 'Errore durante il salvataggio.');
            });
    });
}

// Conferma eliminazione cliente
function confirmDeleteClient(clientId) {
    clientToDelete = clientId;
    new bootstrap.Modal(document.getElementById('confirmDeleteClientModal')).show();
}

const confirmDeleteClientBtn = document.getElementById('confirmDeleteClientBtn');
if (confirmDeleteClientBtn) {
    confirmDeleteClientBtn.addEventListener('click', function () {
        if (!clientToDelete) return;

        fetch(`/api/clients/${clientToDelete}`, {
            method: 'DELETE'
        })
            .then(response => {
                if (!response.ok) throw new Error('Errore durante l\'eliminazione del cliente.');
                window.location.reload();
            })
            .catch(error => {
                console.error('Errore:', error);
                alert(error.message || 'Errore durante l\'eliminazione.');
            });
    });
}

// Ricerca clienti (live)
const clientSearch = document.getElementById('clientSearch');
if (clientSearch) {
    clientSearch.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase().trim();
        const clientItems = document.querySelectorAll('.client-item');
        const noClientsMessage = document.querySelector('.no-clients');
        let visibleCount = 0;

        if (noClientsMessage && searchTerm !== '') {
            noClientsMessage.classList.add('d-none');
        }

        clientItems.forEach((item, index) => {
            const itemText = item.textContent.toLowerCase();
            if (searchTerm === '' || itemText.includes(searchTerm)) {
                item.classList.remove('d-none');
                item.style.display = 'flex';
                visibleCount++;
            } else {
                item.classList.add('d-none');
                item.style.display = 'none';
            }
        });

        if (searchTerm === '' && noClientsMessage) {
            noClientsMessage.classList.remove('d-none');
        }
    });
}

// ===========================
// ====== FATTURE CRUD =======
// ===========================
// Sincronizza la data della fattura con la data del pagamento
const dataFatturaInput = document.getElementById('data_fattura');
const dataPagamentoInput = document.getElementById('data_pagamento');

if (dataFatturaInput && dataPagamentoInput) {
    dataFatturaInput.addEventListener('change', function() {
        dataPagamentoInput.value = this.value;
    });
}

// Resetta il form della nuova fattura quando la modale viene aperta
const addInvoiceModal = document.getElementById('addInvoiceModal');
const addInvoiceForm = document.getElementById('addInvoiceForm');

if (addInvoiceModal && addInvoiceForm) {
    addInvoiceModal.addEventListener('show.bs.modal', function () {
        addInvoiceForm.reset();
        
        // Per Select2, devi resettarlo manualmente
        // Questo deseleziona l'opzione
        $('#cliente_id').val(null).trigger('change');
    });
}

// Aggiunta nuova fattura
if (addInvoiceForm) {
    addInvoiceForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const formData = new FormData(event.target);
        const data = {};
        for (const [key, value] of formData.entries()) {
            data[key] = value;
        }

        // Gestisci il checkbox in modo esplicito
        const inviataSnsCheckbox = document.getElementById('inviata_sns');
        if (inviataSnsCheckbox) {
            data['inviata_sns'] = inviataSnsCheckbox.checked;
        }

        fetch('/api/invoices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
            .then(response => {
                if (!response.ok) throw new Error('Errore durante l\'aggiunta della fattura.');
                window.location.reload();
            })
            .catch(error => {
                console.error('Errore:', error);
                alert('Si è verificato un errore durante l\'aggiunta della fattura.');
            });
    });
}

// Apertura modale modifica fattura
function openEditInvoiceModal(invoiceId) {
    fetch(`/api/invoices/${invoiceId}`)
        .then(response => {
            if (!response.ok) throw new Error('Errore recupero fattura');
            return response.json();
        })
        .then(data => {
            document.getElementById('edit-invoice-id').value = data.id;
            
            const editClienteSelect = document.getElementById('edit-cliente_id');
            if (editClienteSelect) {
                editClienteSelect.value = data.cliente_id;
                $('#edit-cliente_id').trigger('change');
            }
            
            document.getElementById('edit-data_fattura').value = data.data_fattura;
            document.getElementById('edit-numero_sedute').value = data.numero_sedute;
            document.getElementById('edit-metodo_pagamento').value = data.metodo_pagamento;
            document.getElementById('edit-data_pagamento').value = data.data_pagamento || '';
            
            const editInviataSns = document.getElementById('edit-inviata-sns');
            if (editInviataSns) {
                editInviataSns.checked = data.inviata_sns;
            }

            const editModal = new bootstrap.Modal(document.getElementById('editInvoiceModal'));
            editModal.show();
        })
        .catch(error => {
            console.error('Errore:', error);
            alert('Errore nel recupero dei dati della fattura.');
        });
}

// Salvataggio modifiche fattura
const editInvoiceForm = document.getElementById('editInvoiceForm');
if (editInvoiceForm) {
    editInvoiceForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const invoiceId = document.getElementById('edit-invoice-id').value;
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());

        // Gestione del checkbox di modifica
        const editInviataSns = document.getElementById('edit-inviata-sns');
        if (editInviataSns) {
            data['inviata_sns'] = editInviataSns.checked;
        }

        fetch(`/api/invoices/${invoiceId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
            .then(response => {
                if (!response.ok) throw new Error('Errore durante l\'aggiornamento della fattura.');
                window.location.reload();
            })
            .catch(error => {
                console.error('Errore:', error);
                alert('Si è verificato un errore durante l\'aggiornamento della fattura.');
            });
    });
}

// Funzione per filtrare le fatture
const invoiceSearch = document.getElementById('invoiceSearch');
if (invoiceSearch) {
    invoiceSearch.addEventListener('input', function (event) {
        const searchTerm = event.target.value.toLowerCase();
        const rows = document.querySelectorAll('#invoicesAccordion tbody tr');

        rows.forEach(row => {
            const textContent = row.textContent.toLowerCase();
            if (textContent.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
}

// ===========================
// ======== DASHBOARD ========
// ===========================

// Variabili per i grafici
let chartPerMeseInstance = null;
let chartPerClienteInstance = null;

const MESE_MAPPINGS = {
    1: 'Gen', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mag', 6: 'Giu',
    7: 'Lug', 8: 'Ago', 9: 'Set', 10: 'Ott', 11: 'Nov', 12: 'Dic'
};

function fetchDashboardStats(year = null) {
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
                const selectedYear = year || 'tutti gli anni';
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

// Quando il tab della dashboard è attivato, carica le statistiche
const dashboardTab = document.getElementById('dashboard-tab');
if (dashboardTab) {
    dashboardTab.addEventListener('shown.bs.tab', function(event) {
        initializeDashboard();
    });
}

// Funzione per inizializzare la dashboard
function initializeDashboard() {
    // Prima popola il selettore degli anni
    populateYearSelector();
    // Poi carica le statistiche
    fetchDashboardStats();
}

// Funzione per popolare il selettore degli anni
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
                
                // Event listener per il cambio di anno
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

// Carica le statistiche anche se la dashboard è già attiva al caricamento della pagina
document.addEventListener('DOMContentLoaded', function() {
    // Controlla se il tab dashboard è già attivo
    const dashboardTab = document.getElementById('dashboard-tab');
    const statsContainer = document.getElementById('dashboard-stats');
    if ((dashboardTab && dashboardTab.classList.contains('active')) || statsContainer) {
        initializeDashboard();
    }
});