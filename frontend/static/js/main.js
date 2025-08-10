// Importa le funzioni di inizializzazione dagli altri moduli
import { initializeClients } from './clienti.js';
import { initializeInvoices } from './fatture.js';
import { initializeDashboard, fetchDashboardStats } from './dashboard.js';

// ----- Helper per mostrare tab -----
function showTabById(tabButtonSelector) {
    const tabEl = document.querySelector(tabButtonSelector);
    if (tabEl) new bootstrap.Tab(tabEl).show();
}

// Inizializzazione principale
document.addEventListener('DOMContentLoaded', function() {
    // Inizializzazione bottone vai a clienti
    const gotoClientsBtn = document.getElementById('gotoClientsBtn');
    if (gotoClientsBtn) {
        gotoClientsBtn.addEventListener('click', function () {
            showTabById('#clients-tab');
        });
    }

    // Inizializzazione dei moduli
    initializeClients();
    initializeInvoices();

    // Quando il tab della dashboard è attivato, carica le statistiche
    const dashboardTab = document.getElementById('dashboard-tab');
    if (dashboardTab) {
        dashboardTab.addEventListener('shown.bs.tab', function(event) {
            initializeDashboard();
        });
    }

    // Carica le statistiche anche se la dashboard è già attiva al caricamento della pagina
    const statsContainer = document.getElementById('dashboard-stats');
    if (statsContainer) {
        initializeDashboard();
    }
});