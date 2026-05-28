// ====== COSTI CRUD CON NOTIFICHE UNIFICATE =======
import { notifications } from './notifications.js';

// Funzione per salvare la sezione attiva
function saveActiveTab() {
    const activePanel = document.querySelector('.section-panel.active');
    if (activePanel) {
        localStorage.setItem('activeSection', activePanel.id.replace('section-', ''));
    }
}

// Funzione per caricare i costi dal backend e popolare la tabella
async function loadCosts() {
    // Non serve più loadCosts dinamicamente perché i costi sono già nel template
    // Questa funzione può essere rimossa o utilizzata per ricaricare dopo modifiche
}

// Variabile globale per l'istanza del modal di modifica
let editCostModalInstance = null;
let editRecurringCostModalInstance = null;

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

async function openEditRecurringCostModal(ricorrenzaId) {
    notifications.info('Caricamento dati costo ricorrente...', 2000);

    try {
        const response = await fetch(`/api/recurring-costs/${ricorrenzaId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const ricorrenza = await response.json();

        document.getElementById('edit-recurring-cost-id').value = ricorrenza.id;
        document.getElementById('edit-recurring-descrizione-costo').value = ricorrenza.descrizione;
        document.getElementById('edit-recurring-totale-costo').value = ricorrenza.totale;
        document.getElementById('edit-recurring-frequenza-costo').value = ricorrenza.frequenza;
        document.getElementById('edit-recurring-giorno-scadenza-costo').value = ricorrenza.giorno_scadenza;
        document.getElementById('edit-recurring-data-inizio-costo').value = ricorrenza.data_inizio;
        document.getElementById('edit-recurring-data-fine-costo').value = ricorrenza.data_fine || '';
        document.getElementById('edit-recurring-pagato-default-costo').checked = ricorrenza.pagato_default;
        document.getElementById('edit-recurring-attivo-costo').checked = ricorrenza.attivo;

        const editRecurringCostModalElement = document.getElementById('editRecurringExpenseModal');
        if (!editRecurringCostModalElement) {
            console.error('Modal di modifica costo ricorrente non trovato');
            return;
        }

        editRecurringCostModalInstance = bootstrap.Modal.getInstance(editRecurringCostModalElement);
        if (!editRecurringCostModalInstance) {
            editRecurringCostModalInstance = new bootstrap.Modal(editRecurringCostModalElement);
        }

        editRecurringCostModalInstance.show();
    } catch (error) {
        console.error("Errore nel recupero dei dati del costo ricorrente:", error);
        notifications.error('Impossibile recuperare i dati del costo ricorrente per la modifica.');
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

function showDeleteRecurringConfirmation(ricorrenzaId) {
    const button = document.querySelector(`[data-id="${ricorrenzaId}"].delete-recurring-cost-btn`);
    const row = button.closest('tr');
    const descrizione = row ? row.cells[0].textContent : 'questo costo ricorrente';

    notifications.confirm(
        `Disattivare il costo ricorrente "${descrizione}"? I costi già generati resteranno in elenco.`,
        () => {
            handleDeleteRecurringCost(ricorrenzaId);
        },
        () => {
            notifications.info('Disattivazione annullata.', 2000);
        },
        'Disattiva',
        'Annulla'
    );
}

// Handler separato per il pulsante di modifica
function handleEditButtonClick(e) {
    const costoId = e.currentTarget.dataset.id;
    openEditCostModal(costoId);
}

function handleEditRecurringButtonClick(e) {
    const ricorrenzaId = e.currentTarget.dataset.id;
    openEditRecurringCostModal(ricorrenzaId);
}

// Handler separato per il pulsante di eliminazione
function handleDeleteButtonClick(e) {
    const costoId = e.currentTarget.dataset.id;
    showDeleteConfirmation(costoId);
}

function handleDeleteRecurringButtonClick(e) {
    const ricorrenzaId = e.currentTarget.dataset.id;
    showDeleteRecurringConfirmation(ricorrenzaId);
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

async function handleDeleteRecurringCost(ricorrenzaId) {
    try {
        const response = await fetch(`/api/recurring-costs/${ricorrenzaId}`, {
            method: 'DELETE',
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        notifications.success('Costo ricorrente disattivato con successo!');
        setTimeout(() => window.location.reload(), 1500);
    } catch (error) {
        console.error("Errore durante la disattivazione del costo ricorrente:", error);
        notifications.error('Si è verificato un errore durante la disattivazione del costo ricorrente.');
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

    document.querySelectorAll('.delete-recurring-cost-btn').forEach(button => {
        button.addEventListener('click', handleDeleteRecurringButtonClick);
    });

    document.querySelectorAll('.edit-recurring-cost-btn').forEach(button => {
        button.addEventListener('click', handleEditRecurringButtonClick);
    });

    const recurringCheckbox = document.getElementById('ricorrente_costo');
    const recurringFields = document.getElementById('recurringCostFields');
    const dataPagamentoField = document.getElementById('data_pagamento_costo');
    const dataInizioRicorrenzaField = document.getElementById('data_inizio_ricorrenza_costo');
    const giornoScadenzaField = document.getElementById('giorno_scadenza_costo');
    const pagatoCheckbox = document.getElementById('pagato_costo');
    const pagatoDefaultCheckbox = document.getElementById('pagato_default_costo');

    if (recurringCheckbox && recurringFields) {
        recurringCheckbox.addEventListener('change', () => {
            recurringFields.classList.toggle('d-none', !recurringCheckbox.checked);
            if (recurringCheckbox.checked) {
                const sourceDate = dataPagamentoField?.value || new Date().toISOString().split('T')[0];
                if (dataInizioRicorrenzaField && !dataInizioRicorrenzaField.value) {
                    dataInizioRicorrenzaField.value = sourceDate;
                }
                if (giornoScadenzaField && dataPagamentoField?.value) {
                    giornoScadenzaField.value = new Date(`${dataPagamentoField.value}T00:00:00`).getDate();
                }
                if (pagatoDefaultCheckbox && pagatoCheckbox) {
                    pagatoDefaultCheckbox.checked = pagatoCheckbox.checked;
                }
            }
        });
    }

    if (pagatoCheckbox && pagatoDefaultCheckbox) {
        pagatoCheckbox.addEventListener('change', () => {
            if (recurringCheckbox?.checked) {
                pagatoDefaultCheckbox.checked = pagatoCheckbox.checked;
            }
        });
    }

    // Gestione form di aggiunta costo
    const addExpenseForm = document.getElementById('addExpenseForm');
    if (addExpenseForm) {
        addExpenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const form = e.target;
            const isRecurring = form.querySelector('#ricorrente_costo')?.checked || false;
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

            if (isRecurring) {
                const recurringData = {
                    descrizione: formData.descrizione,
                    totale: formData.totale,
                    frequenza: form.querySelector('#frequenza_costo').value,
                    giorno_scadenza: parseInt(form.querySelector('#giorno_scadenza_costo').value),
                    data_inizio: form.querySelector('#data_inizio_ricorrenza_costo').value || formData.data_pagamento,
                    data_fine: form.querySelector('#data_fine_ricorrenza_costo').value || null,
                    pagato_default: form.querySelector('#pagato_default_costo').checked,
                    attivo: true,
                };

                if (!recurringData.data_inizio) {
                    notifications.warning('La data di inizio ricorrenza è obbligatoria.');
                    return;
                }

                if (
                    isNaN(recurringData.giorno_scadenza) ||
                    recurringData.giorno_scadenza < 1 ||
                    recurringData.giorno_scadenza > 31
                ) {
                    notifications.warning('Il giorno di scadenza deve essere tra 1 e 31.');
                    return;
                }

                try {
                    const response = await fetch('/api/recurring-costs', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(recurringData),
                    });

                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}));
                        throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
                    }

                    notifications.success(`Costo ricorrente "${recurringData.descrizione}" aggiunto con successo!`);

                    const addExpenseModalElement = document.getElementById('addExpenseModal');
                    if (addExpenseModalElement) {
                        addExpenseModalInstance = bootstrap.Modal.getInstance(addExpenseModalElement);
                        if (addExpenseModalInstance) {
                            addExpenseModalInstance.hide();
                        }
                    }

                    setTimeout(() => window.location.reload(), 1500);
                } catch (error) {
                    console.error("Errore nell'aggiunta del costo ricorrente:", error);
                    notifications.error(error.message || 'Si è verificato un errore durante l\'aggiunta del costo ricorrente.');
                }
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

    const editRecurringExpenseForm = document.getElementById('editRecurringExpenseForm');
    if (editRecurringExpenseForm) {
        editRecurringExpenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const form = e.target;
            const ricorrenzaId = form.querySelector('#edit-recurring-cost-id').value;
            const formData = {
                descrizione: form.querySelector('#edit-recurring-descrizione-costo').value,
                totale: parseFloat(form.querySelector('#edit-recurring-totale-costo').value),
                frequenza: form.querySelector('#edit-recurring-frequenza-costo').value,
                giorno_scadenza: parseInt(form.querySelector('#edit-recurring-giorno-scadenza-costo').value),
                data_inizio: form.querySelector('#edit-recurring-data-inizio-costo').value,
                data_fine: form.querySelector('#edit-recurring-data-fine-costo').value || null,
                pagato_default: form.querySelector('#edit-recurring-pagato-default-costo').checked,
                attivo: form.querySelector('#edit-recurring-attivo-costo').checked,
            };

            if (!formData.descrizione.trim()) {
                notifications.warning('La descrizione è obbligatoria.');
                return;
            }

            if (isNaN(formData.totale) || formData.totale <= 0) {
                notifications.warning('Il totale deve essere un numero positivo.');
                return;
            }

            if (
                isNaN(formData.giorno_scadenza) ||
                formData.giorno_scadenza < 1 ||
                formData.giorno_scadenza > 31
            ) {
                notifications.warning('Il giorno di scadenza deve essere tra 1 e 31.');
                return;
            }

            if (!formData.data_inizio) {
                notifications.warning('La data di inizio ricorrenza è obbligatoria.');
                return;
            }

            if (formData.data_fine && formData.data_fine < formData.data_inizio) {
                notifications.warning('La data di fine non può precedere la data di inizio.');
                return;
            }

            try {
                const response = await fetch(`/api/recurring-costs/${ricorrenzaId}`, {
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

                notifications.success(`Costo ricorrente "${formData.descrizione}" aggiornato con successo!`);

                if (editRecurringCostModalInstance) {
                    editRecurringCostModalInstance.hide();
                }

                setTimeout(() => window.location.reload(), 1500);
            } catch (error) {
                console.error("Errore nell'aggiornamento del costo ricorrente:", error);
                notifications.error(error.message || 'Si è verificato un errore durante l\'aggiornamento del costo ricorrente.');
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
            if (pagatoCheckbox) {
                pagatoCheckbox.checked = false;
            }

            if (recurringCheckbox && recurringFields) {
                recurringCheckbox.checked = false;
                recurringFields.classList.add('d-none');
            }

            const frequenzaField = document.getElementById('frequenza_costo');
            if (frequenzaField) {
                frequenzaField.value = 'mensile';
            }

            if (giornoScadenzaField && dataField?.value) {
                giornoScadenzaField.value = new Date(`${dataField.value}T00:00:00`).getDate();
            }

            if (dataInizioRicorrenzaField && dataField?.value) {
                dataInizioRicorrenzaField.value = dataField.value;
            }

            const dataFineRicorrenzaField = document.getElementById('data_fine_ricorrenza_costo');
            if (dataFineRicorrenzaField) {
                dataFineRicorrenzaField.value = '';
            }

            if (pagatoDefaultCheckbox) {
                pagatoDefaultCheckbox.checked = false;
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
