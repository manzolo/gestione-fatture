// ====== FATTURE CRUD CON NOTIFICHE UNIFICATE =======
import { notifications } from './notifications.js';

// Funzione per salvare la tab attiva
function saveActiveTab() {
    const activeTab = document.querySelector('.nav-link.active');
    if (activeTab) {
        localStorage.setItem('activeTab', activeTab.id);
    }
}

export function initializeInvoices() {
    // Sincronizza la data della fattura con la data del pagamento
    const dataFatturaInput = document.getElementById('data_fattura');
    const dataPagamentoInput = document.getElementById('data_pagamento');

    if (dataFatturaInput && dataPagamentoInput) {
        dataFatturaInput.addEventListener('change', function() {
            dataPagamentoInput.value = this.value;
            notifications.info('Data pagamento sincronizzata con la data fattura.', 2000);
        });
    }

    // Resetta il form della nuova fattura quando la modale viene aperta
    const addInvoiceModal = document.getElementById('addInvoiceModal');
    const addInvoiceForm = document.getElementById('addInvoiceForm');

    if (addInvoiceModal && addInvoiceForm) {
        addInvoiceModal.addEventListener('show.bs.modal', function () {
            addInvoiceForm.reset();
            
            // Per Select2, devi resettarlo manualmente
            $('#cliente_id').val(null).trigger('change');
            notifications.info('Form pronto per nuova fattura.', 2000);
        });

        // Imposta il focus sulla select del cliente quando il modale è completamente aperto
        addInvoiceModal.addEventListener('shown.bs.modal', function () {
            setTimeout(() => {
                $('#cliente_id').select2('open');
            }, 200);
        });
    }

    // Aggiunta nuova fattura
    if (addInvoiceForm) {
        // Disabilita la validazione HTML5 nativa per questo form
        addInvoiceForm.setAttribute('novalidate', 'novalidate');
        
        addInvoiceForm.addEventListener('submit', function (event) {
            event.preventDefault();

            const formData = new FormData(event.target);
            const data = {};
            for (const [key, value] of formData.entries()) {
                data[key] = value;
            }

            const inviataSnsCheckbox = document.getElementById('inviata_sns');
            if (inviataSnsCheckbox) {
                data['inviata_sns'] = inviataSnsCheckbox.checked;
            }

            // Validazione client-side migliorata
            if (!data.cliente_id) {
                notifications.warning('Seleziona un cliente per procedere.');
                setTimeout(() => {
                    $('#cliente_id').select2('open');
                }, 200);
                return;
            }

            if (!data.data_fattura) {
                notifications.warning('La data della fattura è obbligatoria.');
                document.getElementById('data_fattura').focus();
                return;
            }

            if (!data.numero_sedute || data.numero_sedute <= 0) {
                notifications.warning('Il numero di sedute deve essere maggiore di zero.');
                document.getElementById('numero_sedute').focus();
                return;
            }

            notifications.info('Creazione fattura in corso...', 2000);

            fetch('/api/invoices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
                .then(response => {
                    if (!response.ok) throw new Error('Errore durante l\'aggiunta della fattura.');
                    return response.json();
                })
                .then(result => {
                    console.log('Risposta del server:', result);
                    
                    const numeroFattura = result.numero_fattura || result.invoice_number || result.number || result.id || 'nuova';
                    
                    let successMessage = 'Fattura creata con successo!';
                    if (numeroFattura && numeroFattura !== 'nuova') {
                        successMessage = `Fattura #${numeroFattura} creata con successo!`;
                    }
                    
                    notifications.success(successMessage);
                    
                    // Chiudi la modale prima di ricaricare
                    const modal = bootstrap.Modal.getInstance(addInvoiceModal);
                    if (modal) {
                        modal.hide();
                    }
                    
                    saveActiveTab(); // Salva la tab prima del reload
                    setTimeout(() => window.location.reload(), 1500);
                })
                .catch(error => {
                    console.error('Errore:', error);
                    notifications.error('Si è verificato un errore durante l\'aggiunta della fattura.');
                });
        });
    }

    // Apertura modale modifica fattura
    window.openEditInvoiceModal = function(invoiceId) {
        notifications.info('Caricamento dati fattura...', 2000);
        
        fetch(`/api/invoices/${invoiceId}`)
            .then(response => {
                if (!response.ok) throw new Error('Errore recupero fattura');
                return response.json();
            })
            .then(data => {
                document.getElementById('edit-invoice-id').value = data.id;
                
                const editClienteSelect = document.getElementById('edit-cliente_id');
                if (editClienteSelect) {
                    editClienteSelect.value = data.cliente_id;
                    $('#edit-cliente_id').trigger('change');
                }
                
                document.getElementById('edit-data_fattura').value = data.data_fattura;
                document.getElementById('edit-numero_sedute').value = data.numero_sedute;
                document.getElementById('edit-metodo_pagamento').value = data.metodo_pagamento;
                document.getElementById('edit-data_pagamento').value = data.data_pagamento || '';
                
                const editInviataSns = document.getElementById('edit-inviata-sns');
                if (editInviataSns) {
                    editInviataSns.checked = data.inviata_sns;
                }

                const editModal = new bootstrap.Modal(document.getElementById('editInvoiceModal'));
                editModal.show();

                // Focus sul numero sedute nel modale di modifica
                document.getElementById('editInvoiceModal').addEventListener('shown.bs.modal', function() {
                    setTimeout(() => {
                        const numeroSeduteField = document.getElementById('edit-numero_sedute');
                        if (numeroSeduteField) {
                            numeroSeduteField.focus();
                            numeroSeduteField.select();
                        }
                    }, 200);
                }, { once: true });
                
                notifications.success('Dati fattura caricati per la modifica.', 2000);
            })
            .catch(error => {
                console.error('Errore:', error);
                notifications.error('Errore nel recupero dei dati della fattura.');
            });
    }

    // Salvataggio modifiche fattura
    const editInvoiceForm = document.getElementById('editInvoiceForm');
    if (editInvoiceForm) {
        // Disabilita la validazione HTML5 nativa per questo form
        editInvoiceForm.setAttribute('novalidate', 'novalidate');
        
        editInvoiceForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const invoiceId = document.getElementById('edit-invoice-id').value;
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());

            const editInviataSns = document.getElementById('edit-inviata-sns');
            if (editInviataSns) {
                data['inviata_sns'] = editInviataSns.checked;
            }

            // Validazione client-side migliorata per la modifica
            if (!data.cliente_id) {
                notifications.warning('Seleziona un cliente per procedere.');
                setTimeout(() => {
                    $('#edit-cliente_id').select2('open');
                }, 200);
                return;
            }

            if (!data.data_fattura) {
                notifications.warning('La data della fattura è obbligatoria.');
                document.getElementById('edit-data_fattura').focus();
                return;
            }

            if (!data.numero_sedute || data.numero_sedute <= 0) {
                notifications.warning('Il numero di sedute deve essere maggiore di zero.');
                document.getElementById('edit-numero_sedute').focus();
                return;
            }

            notifications.info('Aggiornamento fattura in corso...', 2000);

            fetch(`/api/invoices/${invoiceId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
                .then(response => {
                    if (!response.ok) throw new Error('Errore durante l\'aggiornamento della fattura.');
                    return response.json();
                })
                .then(result => {
                    console.log('Risposta aggiornamento:', result);
                    
                    const numeroFattura = result.numero_fattura || result.invoice_number || result.number || invoiceId;
                    
                    let successMessage = 'Fattura aggiornata con successo!';
                    if (numeroFattura) {
                        successMessage = `Fattura #${numeroFattura} aggiornata con successo!`;
                    }
                    
                    notifications.success(successMessage);
                    
                    // Chiudi la modale prima di ricaricare
                    const editModal = bootstrap.Modal.getInstance(document.getElementById('editInvoiceModal'));
                    if (editModal) {
                        editModal.hide();
                    }
                    
                    saveActiveTab(); // Salva la tab prima del reload
                    setTimeout(() => window.location.reload(), 1500);
                })
                .catch(error => {
                    console.error('Errore:', error);
                    notifications.error('Si è verificato un errore durante l\'aggiornamento della fattura.');
                });
        });
    }

    // Funzione per filtrare le fatture
    const invoiceSearch = document.getElementById('invoiceSearch');
    if (invoiceSearch) {
        invoiceSearch.addEventListener('input', function (event) {
            const searchTerm = event.target.value.toLowerCase();
            const rows = document.querySelectorAll('#invoicesAccordion tbody tr');
            let visibleCount = 0;

            rows.forEach(row => {
                const textContent = row.textContent.toLowerCase();
                if (textContent.includes(searchTerm)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            // Mostra notifica se nessun risultato solo se c'è un termine di ricerca
            if (searchTerm !== '' && visibleCount === 0) {
                notifications.info('Nessuna fattura trovata per la ricerca corrente.', 3000);
            }
        });
    }

    // Inizializzazione Select2
    if ($('#cliente_id').length) {
        // Rimuovi l'attributo required dalla select originale per evitare validazione HTML5
        $('#cliente_id').removeAttr('required');
        
        $('#cliente_id').select2({
            dropdownParent: $('#addInvoiceModal'),
            placeholder: "Seleziona un cliente",
            allowClear: true,
            width: '100%'
        }).on('select2:select', function (e) {
            const clientName = e.params.data.text;
            notifications.info(`Cliente "${clientName}" selezionato.`, 2000);
        }).on('select2:open', function () {
            setTimeout(() => {
                const searchField = $('.select2-container--open .select2-search__field').last();
                if (searchField.length > 0) {
                    searchField.get(0).focus();
                }
            }, 150);
        });
    }
    
    if ($('#edit-cliente_id').length) {
        // Rimuovi l'attributo required dalla select originale per evitare validazione HTML5
        $('#edit-cliente_id').removeAttr('required');
        
        $('#edit-cliente_id').select2({
            dropdownParent: $('#editInvoiceModal'),
            placeholder: "Seleziona un cliente",
            allowClear: true,
            width: '100%'
        }).on('select2:select', function (e) {
            const clientName = e.params.data.text;
            notifications.info(`Cliente cambiato in "${clientName}".`, 2000);
        }).on('select2:open', function () {
            setTimeout(() => {
                const searchField = $('.select2-container--open .select2-search__field').last();
                if (searchField.length > 0) {
                    searchField.get(0).focus();
                }
            }, 150);
        });
    }

    // Gestione download fattura
    document.addEventListener('click', function(e) {
        if (e.target.closest('.btn-success[title="Scarica fattura"]')) {
            notifications.info('Download fattura avviato...', 3000);
        }
    });
}