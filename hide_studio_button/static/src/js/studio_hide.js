odoo.define('hide_studio_button.studio_hide', function (require) {
    "use strict";

    var session = require('web.session');

    session.user_has_group('hide_studio_button.group_hide_studio').then(function(hasGroup) {
        if (!hasGroup) {
            return; // No hacer nada si no pertenece al grupo
        }

        // 1. Inyectar CSS con !important en el head
        var style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = `
            .o_web_studio_navbar_item {
                display: none !important;
            }
        `;
        document.head.appendChild(style);

        // 2. Función para ocultar directamente (por si el CSS falla)
        function hideButtonDirectly() {
            var btn = document.querySelector('.o_web_studio_navbar_item');
            if (btn) {
                btn.style.setProperty('display', 'none', 'important');
            }
        }

        // 3. Ejecutar inmediatamente y luego cada vez que cambie el DOM
        hideButtonDirectly();

        var observer = new MutationObserver(function(mutations) {
            // Si el CSS no lo ocultó, forzar ocultamiento directo
            hideButtonDirectly();
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // 4. Fallback: intervalo cada 1 segundo por si el observer falla
        setInterval(hideButtonDirectly, 1000);
    });
});