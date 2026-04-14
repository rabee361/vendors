const toggler = document.getElementById('theme-toggler');
const html = document.documentElement;
const themeIcon = toggler.querySelector('i');

// Icons
const SUN_ICON = 'fas fa-sun';
const MOON_ICON = 'fas fa-moon';

/**
 * Update the toggle icon based on the current theme
 * @param {string} theme 
 */
function updateIcon(theme) {
    if (theme === 'light') {
        themeIcon.className = SUN_ICON;
    } else {
        themeIcon.className = MOON_ICON;
    }
}

/**
 * Apply theme to document
 * @param {string} theme 
 */
function applyTheme(theme) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateIcon(theme);
}

// Initial Sync from LocalStorage
const savedTheme = localStorage.getItem('theme') || 'dark';
applyTheme(savedTheme);

// Click Event Listener
toggler.addEventListener('click', () => {
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
});
