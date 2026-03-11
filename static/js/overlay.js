// Overlay management
function toggleOverlay(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.toggle('open');
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

// Preserve Overlay State across HTMX Swaps
document.addEventListener('htmx:beforeSwap', function(evt) {
    const target = evt.detail.target;
    if (target && (target.id === 'cart' || target.id === 'favorites')) {
        evt.detail.wasOpen = target.classList.contains('open');
    }
});

document.addEventListener('htmx:afterSwap', function (evt) {
    const target = evt.detail.target;
    if (evt.detail.wasOpen && target) {
        target.classList.add('open');
    }
});