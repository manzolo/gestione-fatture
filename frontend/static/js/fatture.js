// ====== FATTURE CRUD =======
export function initializeInvoices() {
    // Sincronizza la data della fattura con la data del pagamento
    const dataFatturaInput = document.getElementById('data_fattura');
    const dataPagamentoInput = document.getElementById('data_pagamento');

    if (dataFatturaInput && dataPagamentoInput) {
        dataFatturaInput.addEventListener('change', function() {
            dataPagamentoInput.value = this.value;
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
        });
    }

    // Aggiunta nuova fattura
    if (addInvoiceForm) {
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

            fetch('/api/invoices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
                .then(response => {
                    if (!response.ok) throw new Error('Errore durante l\'aggiunta della fattura.');
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Errore:', error);
                    alert('Si è verificato un errore durante l\'aggiunta della fattura.');
                });
        });
    }

    // Apertura modale modifica fattura
    window.openEditInvoiceModal = function(invoiceId) {
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
            })
            .catch(error => {
                console.error('Errore:', error);
                alert('Errore nel recupero dei dati della fattura.');
            });
    }

    // Salvataggio modifiche fattura
    const editInvoiceForm = document.getElementById('editInvoiceForm');
    if (editInvoiceForm) {
        editInvoiceForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const invoiceId = document.getElementById('edit-invoice-id').value;
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());

            const editInviataSns = document.getElementById('edit-inviata-sns');
            if (editInviataSns) {
                data['inviata_sns'] = editInviataSns.checked;
            }

            fetch(`/api/invoices/${invoiceId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
                .then(response => {
                    if (!response.ok) throw new Error('Errore durante l\'aggiornamento della fattura.');
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Errore:', error);
                    alert('Si è verificato un errore durante l\'aggiornamento della fattura.');
                });
        });
    }

    // Funzione per filtrare le fatture
    const invoiceSearch = document.getElementById('invoiceSearch');
    if (invoiceSearch) {
        invoiceSearch.addEventListener('input', function (event) {
            const searchTerm = event.target.value.toLowerCase();
            const rows = document.querySelectorAll('#invoicesAccordion tbody tr');

            rows.forEach(row => {
                const textContent = row.textContent.toLowerCase();
                if (textContent.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Inizializzazione Select2
    if ($('#cliente_id').length) {
        $('#cliente_id').select2({
            dropdownParent: $('#addInvoiceModal'),
            placeholder: "Seleziona un cliente",
            allowClear: true,
            width: '100%'
        });
    }
    
    if ($('#edit-cliente_id').length) {
        $('#edit-cliente_id').select2({
            dropdownParent: $('#editInvoiceModal'),
            placeholder: "Seleziona un cliente",
            allowClear: true,
            width: '100%'
        });
    }
}