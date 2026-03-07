// bell_notifications.js - Sistema notifiche a campana

class BellNotificationManager {
    constructor() {
        this._btn = document.getElementById('bellBtn');
        this._badge = document.getElementById('bellBadge');
        this._dropdown = document.getElementById('notificationDropdown');
        this._body = document.getElementById('notificationDropdownBody');
        this._lastUpdate = document.getElementById('bellLastUpdate');

        if (!this._btn) return;

        this._btn.addEventListener('click', (e) => {
            e.stopPropagation();
            this._toggle();
        });

        document.addEventListener('click', (e) => {
            if (!this._dropdown.contains(e.target) && e.target !== this._btn) {
                this._close();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this._close();
        });

        this.refresh();
        setInterval(() => this.refresh(), 5 * 60 * 1000);
    }

    async refresh() {
        try {
            const [unpaidRes, stsRes] = await Promise.all([
                fetch('/api/invoices/unpaid'),
                fetch('/api/sts/invoices/unsent'),
            ]);
            const unpaid = unpaidRes.ok ? await unpaidRes.json() : [];
            const stsPending = stsRes.ok ? await stsRes.json() : [];
            this._render(
                Array.isArray(unpaid) ? unpaid : [],
                Array.isArray(stsPending) ? stsPending : []
            );
            if (this._lastUpdate) {
                const now = new Date();
                this._lastUpdate.textContent = now.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });
            }
        } catch (err) {
            console.warn('Bell notifications refresh error:', err);
        }
    }

    _render(unpaid, stsPending) {
        const total = unpaid.length + stsPending.length;

        // Badge
        if (total > 0) {
            this._badge.textContent = total > 99 ? '99+' : total;
            this._badge.style.display = 'flex';
        } else {
            this._badge.style.display = 'none';
        }

        if (total === 0) {
            this._body.innerHTML = `
                <div class="notif-empty">
                    <i class="fas fa-check-circle"></i>
                    Tutto in ordine!
                </div>`;
            return;
        }

        let html = '';

        if (unpaid.length > 0) {
            html += `<div class="notif-section-title"><i class="fas fa-clock me-1"></i>Non pagate (${unpaid.length})</div>`;
            unpaid.forEach(f => {
                const date = f.data_fattura ? new Date(f.data_fattura).toLocaleDateString('it-IT') : '';
                const totale = parseFloat(f.totale || 0).toLocaleString('it-IT', { style: 'currency', currency: 'EUR' });
                html += `
                    <div class="notif-item" data-invoice-id="${f.id}" data-type="unpaid">
                        <div class="notif-icon unpaid"><i class="fas fa-file-invoice"></i></div>
                        <div class="notif-text">
                            <strong>${f.numero_fattura} — ${f.cliente || ''}</strong>
                            <span>${date} · ${totale}</span>
                        </div>
                    </div>`;
            });
        }

        if (stsPending.length > 0) {
            html += `<div class="notif-section-title"><i class="fas fa-paper-plane me-1"></i>Da inviare a STS (${stsPending.length})</div>`;
            stsPending.forEach(f => {
                const date = f.data_pagamento ? new Date(f.data_pagamento).toLocaleDateString('it-IT') : '';
                const totale = parseFloat(f.totale || 0).toLocaleString('it-IT', { style: 'currency', currency: 'EUR' });
                html += `
                    <div class="notif-item" data-invoice-id="${f.id}" data-type="sts">
                        <div class="notif-icon sts"><i class="fas fa-paper-plane"></i></div>
                        <div class="notif-text">
                            <strong>${f.numero_fattura} — ${f.cliente || ''}</strong>
                            <span>${date} · ${totale}</span>
                        </div>
                    </div>`;
            });
        }

        this._body.innerHTML = html;

        // Click su item: naviga e highlight
        this._body.querySelectorAll('.notif-item').forEach(item => {
            item.addEventListener('click', () => {
                this._close();
                const invoiceId = item.dataset.invoiceId;
                if (window.showSection) {
                    window.showSection('invoices');
                }
                setTimeout(() => this._highlightRow(invoiceId), 300);
            });
        });
    }

    _highlightRow(invoiceId) {
        const rows = document.querySelectorAll(`tr[data-invoice-id="${invoiceId}"], [data-id="${invoiceId}"]`);
        if (rows.length === 0) return;
        rows.forEach(row => {
            row.classList.remove('row-highlight');
            void row.offsetWidth; // reflow
            row.classList.add('row-highlight');
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
        setTimeout(() => {
            rows.forEach(row => row.classList.remove('row-highlight'));
        }, 2600);
    }

    _toggle() {
        if (this._dropdown.classList.contains('open')) {
            this._close();
        } else {
            this._dropdown.classList.add('open');
        }
    }

    _close() {
        this._dropdown.classList.remove('open');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.bellNotifications = new BellNotificationManager();
});
