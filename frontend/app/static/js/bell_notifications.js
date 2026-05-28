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
            const [unpaidRes, stsRes, unpaidCostsRes] = await Promise.all([
                fetch('/api/invoices/unpaid'),
                fetch('/api/sts/invoices/unsent'),
                fetch('/api/costs/unpaid'),
            ]);
            const unpaid = unpaidRes.ok ? await unpaidRes.json() : [];
            const stsPending = stsRes.ok ? await stsRes.json() : [];
            const unpaidCosts = unpaidCostsRes.ok ? await unpaidCostsRes.json() : [];
            this._render(
                Array.isArray(unpaid) ? unpaid : [],
                Array.isArray(stsPending) ? stsPending : [],
                Array.isArray(unpaidCosts) ? unpaidCosts : []
            );
            if (this._lastUpdate) {
                const now = new Date();
                this._lastUpdate.textContent = now.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });
            }
        } catch (err) {
            console.warn('Bell notifications refresh error:', err);
        }
    }

    _render(unpaid, stsPending, unpaidCosts) {
        const total = unpaid.length + stsPending.length + unpaidCosts.length;

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
                const invoiceId = this._escapeHtml(f.id);
                const numeroFattura = this._escapeHtml(f.numero_fattura);
                const cliente = this._escapeHtml(f.cliente || '');
                html += `
                    <div class="notif-item" data-invoice-id="${invoiceId}" data-type="unpaid">
                        <div class="notif-icon unpaid"><i class="fas fa-file-invoice"></i></div>
                        <div class="notif-text">
                            <strong>${numeroFattura} — ${cliente}</strong>
                            <span>${this._escapeHtml(date)} · ${this._escapeHtml(totale)}</span>
                        </div>
                    </div>`;
            });
        }

        if (stsPending.length > 0) {
            html += `<div class="notif-section-title"><i class="fas fa-paper-plane me-1"></i>Da inviare a STS (${stsPending.length})</div>`;
            stsPending.forEach(f => {
                const date = f.data_pagamento ? new Date(f.data_pagamento).toLocaleDateString('it-IT') : '';
                const totale = parseFloat(f.totale || 0).toLocaleString('it-IT', { style: 'currency', currency: 'EUR' });
                const invoiceId = this._escapeHtml(f.id);
                const numeroFattura = this._escapeHtml(f.numero_fattura);
                const cliente = this._escapeHtml(f.cliente || '');
                html += `
                    <div class="notif-item" data-invoice-id="${invoiceId}" data-type="sts">
                        <div class="notif-icon sts"><i class="fas fa-paper-plane"></i></div>
                        <div class="notif-text">
                            <strong>${numeroFattura} — ${cliente}</strong>
                            <span>${this._escapeHtml(date)} · ${this._escapeHtml(totale)}</span>
                        </div>
                    </div>`;
            });
        }

        if (unpaidCosts.length > 0) {
            html += `<div class="notif-section-title"><i class="fas fa-receipt me-1"></i>Costi non pagati (${unpaidCosts.length})</div>`;
            unpaidCosts.forEach(c => {
                const date = c.data_pagamento ? new Date(c.data_pagamento).toLocaleDateString('it-IT') : '';
                const totale = parseFloat(c.totale || 0).toLocaleString('it-IT', { style: 'currency', currency: 'EUR' });
                const costId = this._escapeHtml(c.id);
                const descrizione = this._escapeHtml(c.descrizione || 'Costo');
                html += `
                    <div class="notif-item" data-cost-id="${costId}" data-type="cost">
                        <div class="notif-icon cost"><i class="fas fa-receipt"></i></div>
                        <div class="notif-text">
                            <strong>${descrizione}</strong>
                            <span>${this._escapeHtml(date)} · ${this._escapeHtml(totale)}</span>
                        </div>
                    </div>`;
            });
        }

        this._body.innerHTML = html;

        // Click su item: naviga e highlight
        this._body.querySelectorAll('.notif-item').forEach(item => {
            item.addEventListener('click', () => {
                this._close();
                if (item.dataset.type === 'cost') {
                    const costId = item.dataset.costId;
                    if (window.showSection) {
                        window.showSection('expenses');
                    }
                    setTimeout(() => this._highlightCostRow(costId), 300);
                } else {
                    const invoiceId = item.dataset.invoiceId;
                    if (window.showSection) {
                        window.showSection('invoices');
                    }
                    setTimeout(() => this._highlightInvoiceRow(invoiceId), 300);
                }
            });
        });
    }

    _highlightInvoiceRow(invoiceId) {
        const safeId = this._cssEscape(invoiceId);
        const rows = document.querySelectorAll(`tr[data-invoice-id="${safeId}"], [data-id="${safeId}"]`);
        this._highlightRows(rows);
    }

    _highlightCostRow(costId) {
        const safeId = this._cssEscape(costId);
        const rows = document.querySelectorAll(`tr[data-cost-id="${safeId}"]`);
        this._highlightRows(rows);
    }

    _highlightRows(rows) {
        if (rows.length === 0) return;
        const targets = Array.from(new Set(Array.from(rows, row => row.closest('tr') || row)));
        targets.forEach(target => {
            const delay = this._expandContainingAccordion(target) ? 400 : 0;
            setTimeout(() => {
                target.classList.remove('row-highlight');
                void target.offsetWidth; // reflow
                target.classList.add('row-highlight');
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, delay);
        });
        setTimeout(() => {
            targets.forEach(target => {
                target.classList.remove('row-highlight');
            });
        }, 3000);
    }

    _expandContainingAccordion(target) {
        const collapse = target.closest('.accordion-collapse');
        if (!collapse || collapse.classList.contains('show') || typeof bootstrap === 'undefined') {
            return false;
        }
        bootstrap.Collapse.getOrCreateInstance(collapse, { toggle: false }).show();
        return true;
    }

    _escapeHtml(value) {
        const replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
        };
        return String(value ?? '').replace(/[&<>"']/g, char => replacements[char]);
    }

    _cssEscape(value) {
        if (window.CSS && typeof window.CSS.escape === 'function') {
            return window.CSS.escape(String(value));
        }
        return String(value).replace(/["\\]/g, '\\$&');
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
