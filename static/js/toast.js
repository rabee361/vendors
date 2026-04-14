/**
 * Toast Notification System
 */
const toastContainer = document.getElementById('toast-container') || (() => {
    const container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
    return container;
})();

function showToast(title, message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: 'fa-check-circle',
        info: 'fa-info-circle',
        error: 'fa-exclamation-triangle'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas ${iconMap[type] || iconMap.info}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-msg">${message}</div>
        </div>
        <div class="toast-close">
            <i class="fas fa-times"></i>
        </div>
        <div class="toast-progress" style="animation: progress ${duration}ms linear forwards"></div>
    `;
    console.log(title);
    console.log(message);
    
    toastContainer.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto remove
    const timer = setTimeout(() => {
        removeToast(toast);
    }, duration);
    
    // Manual close
    toast.querySelector('.toast-close').addEventListener('click', () => {
        clearTimeout(timer);
        removeToast(toast);
    });
}

function removeToast(toast) {
    toast.classList.remove('show');
    toast.style.transform = 'translateX(120%)';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 500);
}

// Hook into HTMX to show toasts based on response headers or events
document.addEventListener('htmx:afterOnLoad', function(evt) {
    // We can use custom headers like X-Toast-Message
    const message = evt.detail.xhr.getResponseHeader('X-Toast-Message');
    const title = evt.detail.xhr.getResponseHeader('X-Toast-Title') || 'إشعار';
    const type = evt.detail.xhr.getResponseHeader('X-Toast-Type') || 'success';
    
    if (message) {
        showToast(decodeURIComponent(title), decodeURIComponent(message), type);
    }
});

// For demonstration/convenience, let's also hook into global adding actions if needed
// or just call showToast directly from templates via hx-on
window.showToast = showToast;
