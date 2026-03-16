// Sidebar Overlay management
function toggleSidebar(id) {
    const el = document.getElementById(id);
    const overlay = document.getElementById('sidebarOverlay');
    if (el) {
        el.classList.toggle('active');
        if (overlay) {
            if (el.classList.contains('active')) {
                overlay.classList.add('open');
            } else {
                overlay.classList.remove('open');
            }
        }
    }
}

function closeSidebar(id) {
    const el = document.getElementById(id);
    const overlay = document.getElementById('sidebarOverlay');
    if (el) el.classList.remove('active');
    if (overlay) overlay.classList.remove('open');
}

// Close when clicking outside the sidebar on the overlay
document.addEventListener('click', (e) => {
    if (e.target.id === 'sidebarOverlay') {
        closeSidebar('modSidebar');
    }
});

// Handle Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeSidebar('modSidebar');
    }
});
