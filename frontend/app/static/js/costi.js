// ====== COSTI CRUD CON NOTIFICHE UNIFICATE =======
import { notifications } from './notifications.js';

// Funzione per caricare i costi dal backend e popolare la tabella
async function loadCosts() {
    // Non serve più loadCosts dinamicamente perché i costi sono già nel template
    // Questa funzione può essere rimossa o utilizzata per ricaricare dopo modifiche
}

// Variabile globale per l'istanza del modal di modifica
let editCostModalInstance = null;

// Funzione per aprire il modal di modifica e popolare i campi
async function openEditCostModal(costoId) {
    notifications.info('Caricamento dati costo...', 2000);
    
    try {
        const response = await fetch(`/api/costs/${costoId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const costo = await response.json();
        
        // Popola il form
        document.getElementById('edit-cost-id').value = costo.id;
        document.getElementById('edit-descrizione-costo').value = costo.descrizione;
        document.getElementById('edit-anno-costo').value = costo.anno_riferimento;
        document.getElementById('edit-data-pagamento-costo').value = costo.data_pagamento;
        document.getElementById('edit-totale-costo').value = costo.totale;
        document.getElementById('edit-pagato-costo').checked = costo.pagato;

        // Gestisci il modal
        const editCostModalElement = document.getElementById('editExpenseModal');
        if (!editCostModalElement) {
            console.error('Modal di modifica non trovato');
            return;
        }

        // Ottieni o crea l'istanza del modal
        editCostModalInstance = bootstrap.Modal.getInstance(editCostModalElement);
        if (!editCostModalInstance) {
            editCostModalInstance = new bootstrap.Modal(editCostModalElement);
        }

        editCostModalInstance.show();
    } catch (error) {
        console.error("Errore nel recupero dei dati del costo:", error);
        notifications.error('Impossibile recuperare i dati del costo per la modifica.');
    }
}

// Funzione per mostrare il modal di conferma eliminazione
function showDeleteConfirmation(costoId) {
    // Trova la descrizione del costo per la conferma
    const button = document.querySelector(`[data-id="${costoId}"].delete-cost-btn`);
    const row = button.closest('tr');
    const descrizione = row ? row.cells[0].textContent : 'questo costo';
    
    notifications.confirm(
        `Sei sicuro di voler eliminare il costo "${descrizione}"? Questa azione non può essere annullata.`,
        () => {
            handleDeleteCost(costoId);
        },
        () => {
            notifications.info('Eliminazione annullata.', 2000);
        },
        'Elimina',
        'Annulla'
    );
}

// Handler separato per il pulsante di modifica
function handleEditButtonClick(e) {
    const costoId = e.currentTarget.dataset.id;
    openEditCostModal(costoId);
}

// Handler separato per il pulsante di eliminazione
function handleDeleteButtonClick(e) {
    const costoId = e.currentTarget.dataset.id;
    showDeleteConfirmation(costoId);
}

// Funzione per gestire l'eliminazione di un costo
async function handleDeleteCost(costoId) {
    try {
        const response = await fetch(`/api/costs/${costoId}`, {
            method: 'DELETE',
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        notifications.success('Costo eliminato con successo!');
        setTimeout(() => window.location.reload(), 1500);
    } catch (error) {
        console.error("Errore durante l'eliminazione del costo:", error);
        notifications.error('Si è verificato un errore durante l\'eliminazione del costo.');
    }
}

// Variabile globale per l'istanza del modal di aggiunta
let addExpenseModalInstance = null;

// Inizializzazione principale
document.addEventListener('DOMContentLoaded', () => {
    // Aggiungi event listener per i pulsanti di modifica ed eliminazione
    document.querySelectorAll('.edit-cost-btn').forEach(button => {
        button.addEventListener('click', handleEditButtonClick);
    });
    
    document.querySelectorAll('.delete-cost-btn').forEach(button => {
        button.addEventListener('click', handleDeleteButtonClick);
    });

    // Gestione form di aggiunta costo
    const addExpenseForm = document.getElementById('addExpenseForm');
    if (addExpenseForm) {
        addExpenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const form = e.target;
            const formData = {
                descrizione: form.querySelector('#descrizione_costo').value,
                anno_riferimento: parseInt(form.querySelector('#anno_costo').value),
                data_pagamento: form.querySelector('#data_pagamento_costo').value,
                totale: parseFloat(form.querySelector('#totale_costo').value),
                pagato: form.querySelector('#pagato_costo').checked,
            };

            // Validazione client-side
            if (!formData.descrizione.trim()) {
                notifications.warning('La descrizione è obbligatoria.');
                return;
            }

            if (!formData.data_pagamento) {
                notifications.warning('La data di pagamento è obbligatoria.');
                return;
            }

            if (isNaN(formData.totale) || formData.totale <= 0) {
                notifications.warning('Il totale deve essere un numero positivo.');
                return;
            }

            try {
                const response = await fetch('/api/costs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData),
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
                }

                const result = await response.json();
                notifications.success(`Costo "${formData.descrizione}" aggiunto con successo!`);

                // Chiudi il modal
                const addExpenseModalElement = document.getElementById('addExpenseModal');
                if (addExpenseModalElement) {
                    addExpenseModalInstance = bootstrap.Modal.getInstance(addExpenseModalElement);
                    if (addExpenseModalInstance) {
                        addExpenseModalInstance.hide();
                    }
                }
                
                setTimeout(() => window.location.reload(), 1500);
            } catch (error) {
                console.error("Errore nell'aggiunta del costo:", error);
                notifications.error(error.message || 'Si è verificato un errore durante l\'aggiunta del costo.');
            }
        });
    }

    // Gestione ricerca/filtro costi con accordion
    const expenseSearch = document.getElementById('expenseSearch');
    if (expenseSearch) {
        expenseSearch.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const accordionItems = document.querySelectorAll('#costsAccordion .accordion-item');
            let totalVisibleCount = 0;

            accordionItems.forEach(accordionItem => {
                const rows = accordionItem.querySelectorAll('tbody tr');
                let visibleRowsInAccordion = 0;

                rows.forEach(row => {
                    const rowText = row.textContent.toLowerCase();
                    if (rowText.includes(searchTerm) || searchTerm === '') {
                        row.style.display = '';
                        visibleRowsInAccordion++;
                        totalVisibleCount++;
                    } else {
                        row.style.display = 'none';
                    }
                });

                // Nascondi l'accordion se non ha righe visibili
                if (visibleRowsInAccordion === 0) {
                    accordionItem.style.display = 'none';
                } else {
                    accordionItem.style.display = '';
                    // Espandi l'accordion se ha risultati
                    if (searchTerm !== '') {
                        const collapseElement = accordionItem.querySelector('.accordion-collapse');
                        if (collapseElement && !collapseElement.classList.contains('show')) {
                            const bsCollapse = new bootstrap.Collapse(collapseElement, { toggle: true });
                        }
                    }
                }
            });

            // Mostra messaggio se nessun risultato
            if (searchTerm !== '' && totalVisibleCount === 0) {
                notifications.info('Nessun costo trovato per la ricerca corrente.', 3000);
            }
        });
    }

    // Gestione form di modifica costo
    const editExpenseForm = document.getElementById('editExpenseForm');
    if (editExpenseForm) {
        editExpenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const form = e.target;
            const costoId = form.querySelector('#edit-cost-id').value;
            const formData = {
                descrizione: form.querySelector('#edit-descrizione-costo').value,
                anno_riferimento: parseInt(form.querySelector('#edit-anno-costo').value),
                data_pagamento: form.querySelector('#edit-data-pagamento-costo').value,
                totale: parseFloat(form.querySelector('#edit-totale-costo').value),
                pagato: form.querySelector('#edit-pagato-costo').checked,
            };

            // Validazione client-side
            if (!formData.descrizione.trim()) {
                notifications.warning('La descrizione è obbligatoria.');
                return;
            }

            if (!formData.data_pagamento) {
                notifications.warning('La data di pagamento è obbligatoria.');
                return;
            }

            if (isNaN(formData.totale) || formData.totale <= 0) {
                notifications.warning('Il totale deve essere un numero positivo.');
                return;
            }

            try {
                const response = await fetch(`/api/costs/${costoId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData),
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
                }

                const result = await response.json();
                notifications.success(`Costo "${formData.descrizione}" aggiornato con successo!`);
                
                // Chiudi il modal
                if (editCostModalInstance) {
                    editCostModalInstance.hide();
                }
                
                setTimeout(() => window.location.reload(), 1500);
            } catch (error) {
                console.error("Errore nell'aggiornamento del costo:", error);
                notifications.error(error.message || 'Si è verificato un errore durante l\'aggiornamento.');
            }
        });
    }

    // Gestione modal di aggiunta - inizializza quando necessario
    const addExpenseModalElement = document.getElementById('addExpenseModal');
    if (addExpenseModalElement) {
        addExpenseModalElement.addEventListener('show.bs.modal', () => {
            if (!addExpenseModalInstance) {
                addExpenseModalInstance = bootstrap.Modal.getInstance(addExpenseModalElement) || new bootstrap.Modal(addExpenseModalElement);
            }
            
            // Reset completo del form
            const form = document.getElementById('addExpenseForm');
            if (form) {
                form.reset();
            }
            
            // Imposta l'anno corrente
            const annoField = document.getElementById('anno_costo');
            if (annoField) {
                const currentYear = new Date().getFullYear();
                annoField.value = currentYear;
            }
            
            // Imposta la data di oggi
            const dataField = document.getElementById('data_pagamento_costo');
            if (dataField) {
                const today = new Date().toISOString().split('T')[0];
                dataField.value = today;
            }
            
            // Assicurati che il checkbox "pagato" sia deselezionato
            const pagatoCheckbox = document.getElementById('pagato_costo');
            if (pagatoCheckbox) {
                pagatoCheckbox.checked = false;
            }
        });
    }

    // Gestione modal di modifica - pulisci notifiche quando si chiude
    const editExpenseModalElement = document.getElementById('editExpenseModal');
    if (editExpenseModalElement) {
        editExpenseModalElement.addEventListener('hidden.bs.modal', () => {
            // Modal chiuso - le notifiche si auto-rimuovono già
        });
    }
});