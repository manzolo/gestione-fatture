// main.js - Navigazione sidebar + inizializzazione moduli

import { initializeClients } from './clienti.js';
import { initializeInvoices } from './fatture.js';
import { initializeDashboard } from './dashboard.js';
import { notifications } from './notifications.js';

window.notifications = notifications;

const SECTION_TITLES = {
    invoices:  'Fatture',
    clients:   'Clienti',
    expenses:  'Costi',
    dashboard: 'Dashboard',
};

let dashboardInitialized = false;

// ---- Navigazione ----

function showSection(sectionId) {
    document.querySelectorAll('.section-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.sidebar-nav-item').forEach(i => i.classList.remove('active'));

    const panel = document.getElementById(`section-${sectionId}`);
    if (panel) panel.classList.add('active');

    const navItem = document.querySelector(`.sidebar-nav-item[data-section="${sectionId}"]`);
    if (navItem) navItem.classList.add('active');

    const title = document.getElementById('pageTitle');
    if (title) title.textContent = SECTION_TITLES[sectionId] || sectionId;

    localStorage.setItem('activeSection', sectionId);

    if (sectionId === 'dashboard' && !dashboardInitialized) {
        dashboardInitialized = true;
        initializeDashboard();
    }
}
window.showSection = showSection;

function restoreSection() {
    const saved = localStorage.getItem('activeSection') || 'invoices';
    showSection(saved);
}

function saveActiveTab() {
    const activePanel = document.querySelector('.section-panel.active');
    if (activePanel) {
        localStorage.setItem('activeSection', activePanel.id.replace('section-', ''));
    }
}
window.saveActiveTab = saveActiveTab;

// ---- DOMContentLoaded ----

document.addEventListener('DOMContentLoaded', function () {
    restoreSection();

    // Sidebar nav clicks
    document.querySelectorAll('.sidebar-nav-item[data-section]').forEach(item => {
        item.addEventListener('click', function () {
            showSection(this.dataset.section);
            // Chiudi sidebar su mobile dopo click
            document.getElementById('sidebar').classList.remove('open');
            document.getElementById('sidebarOverlay').classList.remove('open');
        });
    });

    // Hamburger (mobile)
    const hamburger = document.getElementById('hamburgerBtn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (hamburger && sidebar && overlay) {
        hamburger.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('open');
        });
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('open');
        });
    }

    // Bottone vai a clienti
    const gotoClientsBtn = document.getElementById('gotoClientsBtn');
    if (gotoClientsBtn) {
        gotoClientsBtn.addEventListener('click', () => showSection('clients'));
    }

    // Inizializzazione moduli
    try {
        initializeClients();
        initializeInvoices();
    } catch (error) {
        console.error('Errore durante l\'inizializzazione:', error);
        notifications.error('Errore durante il caricamento del gestionale. Ricarica la pagina.', 10000);
    }

    // Gestione errori globali AJAX
    window.addEventListener('unhandledrejection', function (event) {
        console.error('Errore non gestito:', event.reason);
        notifications.error('Si è verificato un errore imprevisto.', 7000);
    });
});
