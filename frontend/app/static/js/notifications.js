// ====== SISTEMA UNIFORME DI NOTIFICHE ======

export class NotificationManager {
    constructor() {
        this.createNotificationContainer();
    }

    // Crea il container per le notifiche se non esiste
    createNotificationContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    // Mostra una notifica
    show(message, type = 'success', duration = 5000) {
        const container = this.createNotificationContainer();
        
        // Crea l'elemento notifica
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification-item`;
        notification.style.cssText = `
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            animation: slideInRight 0.3s ease-out;
        `;
        
        notification.innerHTML = `
            ${this.getIcon(type)} ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Aggiungi al container
        container.appendChild(notification);
        
        // Auto-rimuovi dopo il tempo specificato
        if (duration > 0) {
            setTimeout(() => {
                this.remove(notification);
            }, duration);
        }
        
        // Gestisci il click del pulsante chiudi
        const closeBtn = notification.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.remove(notification);
            });
        }
        
        return notification;
    }

    // Rimuove una notifica con animazione
    remove(notification) {
        if (notification && notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                if (notification && notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }

    // Ottieni l'icona basata sul tipo
    getIcon(type) {
        const icons = {
            'success': '<i class="fas fa-check-circle me-2"></i>',
            'danger': '<i class="fas fa-exclamation-triangle me-2"></i>',
            'warning': '<i class="fas fa-exclamation-circle me-2"></i>',
            'info': '<i class="fas fa-info-circle me-2"></i>'
        };
        return icons[type] || icons['info'];
    }

    // Metodi di convenienza
    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        return this.show(message, 'danger', duration);
    }

    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }

    // Pulisce tutte le notifiche
    clearAll() {
        const container = document.getElementById('notification-container');
        if (container) {
            const notifications = container.querySelectorAll('.notification-item');
            notifications.forEach(notification => this.remove(notification));
        }
    }

    // Mostra notifica di conferma con callback
    confirm(message, onConfirm, onCancel = null, confirmText = 'Conferma', cancelText = 'Annulla') {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Conferma</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary cancel-btn" data-bs-dismiss="modal">${cancelText}</button>
                        <button type="button" class="btn btn-primary confirm-btn">${confirmText}</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        
        // Gestisci i pulsanti
        const confirmBtn = modal.querySelector('.confirm-btn');
        const cancelBtn = modal.querySelector('.cancel-btn');
        
        confirmBtn.addEventListener('click', () => {
            bootstrapModal.hide();
            if (onConfirm) onConfirm();
        });
        
        if (onCancel) {
            cancelBtn.addEventListener('click', () => {
                onCancel();
            });
        }
        
        // Pulisci il DOM quando il modal si chiude
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
        
        bootstrapModal.show();
        return bootstrapModal;
    }
}

// Crea un'istanza globale del manager delle notifiche
export const notifications = new NotificationManager();

// Aggiungi gli stili CSS per le animazioni
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .notification-container {
        pointer-events: none;
    }
    
    .notification-item {
        pointer-events: all;
    }
`;
document.head.appendChild(style);