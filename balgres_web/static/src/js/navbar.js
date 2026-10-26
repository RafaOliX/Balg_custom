/** @odoo-module **/

document.addEventListener('click', function (e) {
    const toggleBtn = e.target.closest('#bgMenuToggle');
    const closeBtn = e.target.closest('#bgMenuClose');
    const overlay = e.target.closest('#bgNavOverlay');
    const navLink = e.target.closest('.bg-navbar__links a');

    const menu = document.getElementById('bgNavMenu');
    const bgOverlay = document.getElementById('bgNavOverlay');

    if (!menu || !bgOverlay) return;

    if (toggleBtn) {
        e.preventDefault();
        menu.classList.add('is-active');
        bgOverlay.classList.add('is-active');
    }

    if (closeBtn || overlay || navLink) {
        menu.classList.remove('is-active');
        bgOverlay.classList.remove('is-active');
    }
});