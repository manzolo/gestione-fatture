// ====== CLIENTI CRUD =======
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

    // Aggiunta nuovo cliente
    const addClientModal = document.getElementById('addClientModal');
    const addClientForm = document.getElementById('addClientForm');

    if (addClientModal && addClientForm) {
        addClientModal.addEventListener('show.bs.modal', function () {
            addClientForm.reset();
        });
    }

    if (addClientForm) {
        addClientForm.addEventListener('submit', function (event) {
            // Previene l'invio automatico del form
            event.preventDefault();

            const codiceFiscaleInput = document.getElementById('codice_fiscale');
            if (!isValidCodiceFiscale(codiceFiscaleInput.value)) {
                // Sostituito alert() con un messaggio di errore più chiaro.
                alert('Attenzione: Il Codice Fiscale inserito non è valido.');
                return; // Blocca l'esecuzione
            }
            
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

    // Salvataggio modifiche cliente
    const editClientForm = document.getElementById('editClientForm');
    if (editClientForm) {
        editClientForm.addEventListener('submit', function (event) {
            event.preventDefault();
            
            const codiceFiscaleInput = document.getElementById('edit-codice_fiscale');
            if (!isValidCodiceFiscale(codiceFiscaleInput.value)) {
                // Sostituito alert() con un messaggio di errore più chiaro.
                alert('Attenzione: Il Codice Fiscale inserito non è valido.');
                return; // Blocca l'esecuzione
            }

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
    window.confirmDeleteClient = function (clientId) {
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
        });
    }

    // Apertura modale modifica cliente
    window.openEditClientModal = function (clientId) {
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

}
