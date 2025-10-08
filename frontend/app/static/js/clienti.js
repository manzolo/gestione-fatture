// ====== CLIENTI CRUD CON NOTIFICHE UNIFICATE =======
import { notifications } from './notifications.js';

// Funzione per salvare la tab attiva
function saveActiveTab() {
    const activeTab = document.querySelector('.nav-link.active');
    if (activeTab) {
        localStorage.setItem('activeTab', activeTab.id);
    }
}

export function initializeClients() {
    let clientToDelete = null;

    // Funzione per la validazione formale del Codice Fiscale italiano
    function isValidCodiceFiscale(cf) {
        // Rimuove spazi bianchi e converte in maiuscolo
        cf = cf.trim().toUpperCase();
    
        // 1. Verifica la lunghezza (deve essere 16 caratteri)
        if (cf.length !== 16) {
            return false;
        }
    
        // 2. Verifica il pattern del formato
        const regex = /^[A-Z]{6}[0-9]{2}[A-Z]{1}[0-9]{2}[A-Z]{1}[0-9]{3}[A-Z]{1}$/;
        if (!regex.test(cf)) {
            return false;
        }
    
        // 3. Calcolo del carattere di controllo (algoritmo di calcolo)
        const oddMap = {
            '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13, '6': 15, '7': 17, '8': 19, '9': 21,
            'A': 1, 'B': 0, 'C': 5, 'D': 7, 'E': 9, 'F': 13, 'G': 15, 'H': 17, 'I': 19, 'J': 21,
            'K': 2, 'L': 4, 'M': 18, 'N': 20, 'O': 11, 'P': 3, 'Q': 6, 'R': 8, 'S': 12, 'T': 14,
            'U': 16, 'V': 10, 'W': 22, 'X': 25, 'Y': 24, 'Z': 23
        };
    
        let s = 0;
        for (let i = 0; i < 15; i++) {
            let c = cf.charAt(i);
            if (i % 2 === 0) { // Caratteri in posizione dispari (0, 2, 4...)
                s += oddMap[c];
            } else { // Caratteri in posizione pari (1, 3, 5...)
                if (!isNaN(c)) {
                    s += parseInt(c, 10);
                } else {
                    s += (c.charCodeAt(0) - 'A'.charCodeAt(0));
                }
            }
        }
    
        const controlChar = String.fromCharCode('A'.charCodeAt(0) + (s % 26));
    
        // Confronta il carattere di controllo calcolato con l'ultimo carattere del CF
        return controlChar === cf.charAt(15);
    }

    // Funzione helper per gestire gli errori delle risposte HTTP
    async function handleApiResponse(response, operation) {
        if (response.ok) {
            return response;
        }

        let errorMessage = `Errore durante ${operation}`;
        
        try {
            const errorData = await response.json();
            
            // Gestisci diversi tipi di risposta di errore dal server
            if (errorData.message) {
                errorMessage = errorData.message;
            } else if (errorData.error) {
                errorMessage = errorData.error;
            } else if (errorData.details) {
                errorMessage = errorData.details;
            } else if (typeof errorData === 'string') {
                errorMessage = errorData;
            }
        } catch (parseError) {
            // Se non riusciamo a parsare la risposta JSON, usa il messaggio di stato HTTP
            if (response.status === 400) {
                errorMessage = 'Dati non validi. Controlla i campi inseriti.';
            } else if (response.status === 409) {
                errorMessage = 'Cliente già esistente nel sistema.';
            } else if (response.status === 422) {
                errorMessage = 'Dati non validi. Verifica tutti i campi richiesti.';
            } else if (response.status === 500) {
                errorMessage = 'Errore interno del server. Riprova più tardi.';
            } else {
                errorMessage = `${errorMessage} (Codice: ${response.status})`;
            }
        }

        throw new Error(errorMessage);
    }

    // Aggiunta nuovo cliente
    const addClientModal = document.getElementById('addClientModal');
    const addClientForm = document.getElementById('addClientForm');

    if (addClientModal && addClientForm) {
        addClientModal.addEventListener('show.bs.modal', function () {
            addClientForm.reset();
        });

        // Imposta il focus sul primo campo quando il modale è completamente aperto
        addClientModal.addEventListener('shown.bs.modal', function () {
            const firstInput = addClientForm.querySelector('input[type="text"], input[type="email"], textarea, select');
            if (firstInput) {
                firstInput.focus();
            }
        });
    }

    if (addClientForm) {
        addClientForm.addEventListener('submit', async function (event) {
            // Previene l'invio automatico del form
            event.preventDefault();

            // Validazione Codice Fiscale
            const codiceFiscaleInput = document.getElementById('codice_fiscale');
            if (!isValidCodiceFiscale(codiceFiscaleInput.value)) {
                notifications.warning('Il Codice Fiscale inserito non è valido. Controlla il formato e riprova.');
                codiceFiscaleInput.focus();
                return;
            }
            
            // Validazione campi obbligatori
            const nome = document.getElementById('nome')?.value?.trim();
            const cognome = document.getElementById('cognome')?.value?.trim();
            
            if (!nome) {
                notifications.error('Il campo Nome è obbligatorio.');
                document.getElementById('nome')?.focus();
                return;
            }
            
            if (!cognome) {
                notifications.error('Il campo Cognome è obbligatorio.');
                document.getElementById('cognome')?.focus();
                return;
            }
            
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch('/api/clients', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                await handleApiResponse(response, 'l\'aggiunta del cliente');
                
                notifications.success(`Cliente ${data.nome} ${data.cognome} aggiunto con successo!`);
                saveActiveTab(); // Salva la tab prima del reload
                setTimeout(() => window.location.reload(), 1500);
                
            } catch (error) {
                console.error('Errore aggiunta cliente:', error);
                notifications.error(error.message);
            }
        });
    }

    // Salvataggio modifiche cliente
    const editClientForm = document.getElementById('editClientForm');
    if (editClientForm) {
        editClientForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            
            // Validazione Codice Fiscale
            const codiceFiscaleInput = document.getElementById('edit-codice_fiscale');
            if (!isValidCodiceFiscale(codiceFiscaleInput.value)) {
                notifications.warning('Il Codice Fiscale inserito non è valido. Controlla il formato e riprova.');
                codiceFiscaleInput.focus();
                return;
            }

            // Validazione campi obbligatori
            const nome = document.getElementById('edit-nome')?.value?.trim();
            const cognome = document.getElementById('edit-cognome')?.value?.trim();
            
            if (!nome) {
                notifications.error('Il campo Nome è obbligatorio.');
                document.getElementById('edit-nome')?.focus();
                return;
            }
            
            if (!cognome) {
                notifications.error('Il campo Cognome è obbligatorio.');
                document.getElementById('edit-cognome')?.focus();
                return;
            }

            const clientId = document.getElementById('edit-client-id').value;
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch(`/api/clients/${clientId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                await handleApiResponse(response, 'l\'aggiornamento del cliente');
                
                notifications.success(`Cliente ${data.nome} ${data.cognome} aggiornato con successo!`);
                saveActiveTab(); // Salva la tab prima del reload
                setTimeout(() => window.location.reload(), 1500);
                
            } catch (error) {
                console.error('Errore aggiornamento cliente:', error);
                notifications.error(error.message);
            }
        });
    }

    // Conferma eliminazione cliente
    window.confirmDeleteClient = function (clientId) {
        // Recupera il nome del cliente per la conferma
        const clientCard = document.querySelector(`[onclick*="${clientId}"]`).closest('.client-item');
        const clientName = clientCard ? clientCard.querySelector('.card-title').textContent : 'questo cliente';
        
        notifications.confirm(
            `Sei sicuro di voler eliminare ${clientName}? Questa azione non può essere annullata.`,
            async () => {
                // Conferma eliminazione
                try {
                    const response = await fetch(`/api/clients/${clientId}`, {
                        method: 'DELETE'
                    });

                    await handleApiResponse(response, 'l\'eliminazione del cliente');
                    
                    notifications.success(`Cliente ${clientName} eliminato con successo!`);
                    saveActiveTab(); // Salva la tab prima del reload
                    setTimeout(() => window.location.reload(), 1500);
                    
                } catch (error) {
                    console.error('Errore eliminazione cliente:', error);
                    notifications.error(error.message);
                }
            },
            () => {
                // Annullamento
                notifications.info('Eliminazione annullata.', 2000);
            },
            'Elimina',
            'Annulla'
        );
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

            clientItems.forEach((item) => {
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

            // Mostra messaggio se nessun risultato
            if (searchTerm !== '' && visibleCount === 0) {
                notifications.info('Nessun cliente trovato per la ricerca corrente.', 3000);
            }
        });
    }

    // Apertura modale modifica cliente
    window.openEditClientModal = async function (clientId) {
        notifications.info('Caricamento dati cliente...', 2000);
        
        try {
            const response = await fetch(`/api/clients/${clientId}`);
            await handleApiResponse(response, 'il recupero dei dati del cliente');
            
            const data = await response.json();
            
            document.getElementById('edit-client-id').value = data.id;
            document.getElementById('edit-nome').value = data.nome;
            document.getElementById('edit-cognome').value = data.cognome;
            document.getElementById('edit-codice_fiscale').value = data.codice_fiscale;
            document.getElementById('edit-indirizzo').value = data.indirizzo || '';
            document.getElementById('edit-citta').value = data.citta || '';
            document.getElementById('edit-cap').value = data.cap || '';

            const editModal = new bootstrap.Modal(document.getElementById('editClientModal'));
            editModal.show();

            // Focus sul primo campo quando il modale di modifica è aperto
            document.getElementById('editClientModal').addEventListener('shown.bs.modal', function() {
                document.getElementById('edit-nome').focus();
            }, { once: true });
            
        } catch (error) {
            console.error('Errore caricamento cliente:', error);
            notifications.error(error.message);
        }
    }
}