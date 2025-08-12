// ====== COSTI CRUD CON NOTIFICHE UNIFICATE =======
import { notifications } from './notifications.js';

// Funzione per caricare i costi dal backend e popolare la tabella
async function loadCosts() {
    const tableBody = document.getElementById('expensesTableBody');
    tableBody.innerHTML = '<tr><td colspan="6" class="text-center">Caricamento in corso...</td></tr>';

    try {
        const response = await fetch('/api/costs');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const costs = await response.json();
        
        tableBody.innerHTML = ''; // Pulisci la tabella
        if (costs.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">Nessun costo registrato.</td></tr>';
            return;
        }

        costs.forEach(costo => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${costo.descrizione}</td>
                <td>${costo.anno_riferimento}</td>
                <td>${costo.data_pagamento}</td>
                <td>€${costo.totale.toFixed(2)}</td>
                <td>${costo.pagato ? '<span class="badge bg-success">Pagato</span>' : '<span class="badge bg-danger">Non Pagato</span>'}</td>
                <td>
                    <button class="btn btn-warning btn-sm edit-cost-btn" data-id="${costo.id}" title="Modifica"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-danger btn-sm delete-cost-btn" data-id="${costo.id}" title="Elimina"><i class="fas fa-trash-alt"></i></button>
                </td>
            `;
            tableBody.appendChild(row);
        });

        // Rimuovi event listener esistenti per evitare duplicati
        document.querySelectorAll('.edit-cost-btn').forEach(button => {
            button.removeEventListener('click', handleEditButtonClick);
            button.addEventListener('click', handleEditButtonClick);
        });
        
        document.querySelectorAll('.delete-cost-btn').forEach(button => {
            button.removeEventListener('click', handleDeleteButtonClick);
            button.addEventListener('click', handleDeleteButtonClick);
        });

    } catch (error) {
        console.error("Errore nel caricamento dei costi:", error);
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Errore nel caricamento dei costi. Riprova più tardi.</td></tr>`;
        notifications.error('Errore nel caricamento dei costi. Riprova più tardi.');
    }
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
        loadCosts();
    } catch (error) {
        console.error("Errore durante l'eliminazione del costo:", error);
        notifications.error('Si è verificato un errore durante l\'eliminazione del costo.');
    }
}

// Variabile globale per l'istanza del modal di aggiunta
let addExpenseModalInstance = null;

// Inizializzazione principale
document.addEventListener('DOMContentLoaded', () => {
    loadCosts();

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
                
                form.reset(); // Resetta il form
                loadCosts(); // Ricarica la lista
            } catch (error) {
                console.error("Errore nell'aggiunta del costo:", error);
                notifications.error(error.message || 'Si è verificato un errore durante l\'aggiunta del costo.');
            }
        });
    }

    // Gestione ricerca/filtro costi
    const expenseSearch = document.getElementById('expenseSearch');
    if (expenseSearch) {
        expenseSearch.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#expensesTableBody tr');

            let visibleCount = 0;
            rows.forEach(row => {
                const rowText = row.textContent.toLowerCase();
                if (rowText.includes(searchTerm) || searchTerm === '') {
                    row.style.display = '';
                    if (!row.textContent.includes('Nessun costo') && !row.textContent.includes('Caricamento')) {
                        visibleCount++;
                    }
                } else {
                    row.style.display = 'none';
                }
            });

            // Mostra messaggio se nessun risultato
            if (searchTerm !== '' && visibleCount === 0) {
                const noResultsRow = document.querySelector('#expensesTableBody .no-results');
                if (!noResultsRow && rows.length > 0) {
                    const row = document.createElement('tr');
                    row.className = 'no-results';
                    row.innerHTML = '<td colspan="6" class="text-center text-muted">Nessun risultato trovato per la ricerca.</td>';
                    document.getElementById('expensesTableBody').appendChild(row);
                }
                notifications.info('Nessun costo trovato per la ricerca corrente.', 3000);
            } else {
                const noResultsRow = document.querySelector('#expensesTableBody .no-results');
                if (noResultsRow) {
                    noResultsRow.remove();
                }
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
                
                loadCosts();
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