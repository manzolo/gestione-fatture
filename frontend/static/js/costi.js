// Funzione per caricare i costi dal backend e popolare la tabella
async function loadCosts() {
    //console.log("Caricamento dei costi...");
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
    const confirmModalElement = document.getElementById('confirmDeleteExpenseModal');
    if (!confirmModalElement) {
        console.error('Modal di conferma non trovato');
        return;
    }

    // Ottieni o crea l'istanza del modal
    let confirmModal = bootstrap.Modal.getInstance(confirmModalElement);
    if (!confirmModal) {
        confirmModal = new bootstrap.Modal(confirmModalElement);
    }

    // Mostra il modal
    confirmModal.show();
    
    const confirmBtn = document.getElementById('confirmDeleteExpenseBtn');
    if (confirmBtn) {
        // Rimuovi listener precedenti
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        
        // Aggiungi nuovo listener
        newConfirmBtn.addEventListener('click', () => {
            handleDeleteCost(costoId);
            confirmModal.hide();
        });
    }
}

// Variabile globale per l'istanza del modal di modifica
let editCostModalInstance = null;

// Funzione per aprire il modal di modifica e popolare i campi
async function openEditCostModal(costoId) {
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
        alert("Impossibile recuperare i dati del costo per la modifica.");
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
        
        //console.log("Costo eliminato con successo!");
        loadCosts();
    } catch (error) {
        console.error("Errore durante l'eliminazione del costo:", error);
        alert("Si è verificato un errore durante l'eliminazione del costo.");
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

            try {
                const response = await fetch('/api/costs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData),
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const result = await response.json();
                //console.log("Costo aggiunto:", result);

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
                alert("Si è verificato un errore durante l'aggiunta del costo. Controlla la console per i dettagli.");
            }
        });
    }

    // Gestione ricerca/filtro costi
    const expenseSearch = document.getElementById('expenseSearch');
    if (expenseSearch) {
        expenseSearch.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#expensesTableBody tr');

            rows.forEach(row => {
                const rowText = row.textContent.toLowerCase();
                if (rowText.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
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

            try {
                const response = await fetch(`/api/costs/${costoId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData),
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const result = await response.json();
                //console.log("Costo aggiornato:", result);
                
                // Chiudi il modal
                if (editCostModalInstance) {
                    editCostModalInstance.hide();
                }
                
                loadCosts();
            } catch (error) {
                console.error("Errore nell'aggiornamento del costo:", error);
                alert("Si è verificato un errore durante l'aggiornamento. Controlla la console per i dettagli.");
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
        });
    }
});