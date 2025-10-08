// ====== MAIN.JS CON SISTEMA NOTIFICHE UNIFICATE ======

// Importa le funzioni di inizializzazione dagli altri moduli
import { initializeClients } from './clienti.js';
import { initializeInvoices } from './fatture.js';
import { initializeDashboard, fetchDashboardStats } from './dashboard.js';
import { notifications } from './notifications.js';

// Rendi il sistema di notifiche disponibile globalmente
window.notifications = notifications;

// Funzione per salvare la tab attiva
function saveActiveTab() {
    const activeTab = document.querySelector('.nav-link.active');
    if (activeTab) {
        localStorage.setItem('activeTab', activeTab.id);
        //console.log('Tab salvata:', activeTab.id); // Debug
    }
}

// Funzione per ripristinare la tab attiva
function restoreActiveTab() {
    const activeTabId = localStorage.getItem('activeTab');
    //console.log('Tab da ripristinare:', activeTabId); // Debug
    if (activeTabId) {
        const tabElement = document.getElementById(activeTabId);
        if (tabElement) {
            const tab = new bootstrap.Tab(tabElement);
            tab.show();
            //console.log('Tab ripristinata:', activeTabId); // Debug
        }
    }
}

// ----- Helper per mostrare tab -----
function showTabById(tabButtonSelector) {
    const tabEl = document.querySelector(tabButtonSelector);
    if (tabEl) {
        new bootstrap.Tab(tabEl).show();
        // Mostra notifica di navigazione
        notifications.info('Navigazione completata', 2000);
    }
}

// Inizializzazione principale
document.addEventListener('DOMContentLoaded', function() {
    // Ripristina la tab attiva se presente
    restoreActiveTab();
    
    // Aggiungi listener per salvare automaticamente la tab quando cambia
    const tabButtons = document.querySelectorAll('.nav-tabs button[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', function(event) {
            //console.log('Tab cambiata a:', event.target.id); // Debug
            saveActiveTab();
        });
    });
    
    // Inizializzazione bottone vai a clienti
    const gotoClientsBtn = document.getElementById('gotoClientsBtn');
    if (gotoClientsBtn) {
        gotoClientsBtn.addEventListener('click', function () {
            showTabById('#clients-tab');
        });
    }
    
    // Inizializzazione dei moduli
    try {
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
        
    } catch (error) {
        console.error('Errore durante l\'inizializzazione:', error);
        notifications.error('Errore durante il caricamento del gestionale. Ricarica la pagina.', 10000);
    }
    
    // Gestione errori globali per richieste AJAX
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Errore non gestito:', event.reason);
        notifications.error('Si è verificato un errore imprevisto.', 7000);
    });
});