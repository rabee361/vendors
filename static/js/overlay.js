// Overlay management
function toggleOverlay(id) {
    const el = document.getElementById(id);
    if (el) {
    el.classList.toggle('open');
    // If it's the cart, we might want to refresh it via HTMX if it's empty or out of date
    // But for now just simple toggle
    }
}

function closeOverlay(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('open');
}

// Close when clicking outside the modal
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('overlay')) {
    e.target.classList.remove('open');
    }
});

// Handle Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
    document.querySelectorAll('.overlay.open').forEach(el => el.classList.remove('open'));
    }
});

// Initialize HTMX after Swap
document.addEventListener('htmx:afterSwap', function (evt) {
    const target = evt.detail.target;
    // If the target is one of our overlays, re-apply the .open class since outerHTML swap removes it
    if (target && (target.id === 'cart' || target.id === 'favorites')) {
    target.classList.add('open');
    }
});
document.body.addEventListener('htmx:configRequest', (event) => {
    event.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
});