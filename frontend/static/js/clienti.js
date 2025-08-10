// ====== CLIENTI CRUD =======
export function initializeClients() {
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
    window.confirmDeleteClient = function(clientId) {
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
    window.openEditClientModal = function(clientId) {
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