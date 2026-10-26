(function () {
    'use strict';

    function initBalgresProducts() {
        const gridLista = document.getElementById('productos-lista');
        if (!gridLista) return;

        console.log('[Balgres] JS iniciado ✅');

        let currentRequestId = 0;

        // Función que hace la llamada JSON-RPC a Odoo
        function callOdooRpc(url, params) {
            return fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: params || {},
                }),
            })
            .then(r => r.json())
            .then(data => data.result);
        }

        async function renderProductos(formato) {
            const requestId = ++currentRequestId;
            const spinner = document.getElementById('loading-spinner');

            gridLista.innerHTML = '';
            if (spinner) spinner.style.display = 'block';

            try {
                const productos = await callOdooRpc(
                    '/balgres_web/get_products',
                    { formato: formato }
                );
                if (requestId !== currentRequestId) return;

                if (spinner) spinner.style.display = 'none';

                if (!productos || !productos.length) {
                    gridLista.innerHTML =
                        '<div class="no-results">No hay productos en este formato.</div>';
                    return;
                }

                productos.forEach((p, i) => {
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.style.transitionDelay = (i * 0.03) + 's';
                    card.innerHTML = `
                        <a href="${p.url}">
                            <div class="card-img aspect-${p.formato}">
                                <img class="img-base" src="${p.imagen}" alt="${p.nombre}" loading="lazy"/>
                                <img class="img-hover" src="${p.hover}" alt="${p.nombre}" loading="lazy"/>
                            </div>
                            <div class="info-card">
                                <div class="text-product">
                                    <h3>${p.nombre}</h3>
                                    <p>${p.formato.toUpperCase()}</p>
                                </div>
                            </div>
                        </a>`;
                    gridLista.appendChild(card);
                });

                const obs = new IntersectionObserver(entries => {
                    entries.forEach(en => {
                        if (en.isIntersecting) {
                            en.target.classList.add('visible');
                            obs.unobserve(en.target);
                        }
                    });
                }, { threshold: 0.1 });
                gridLista.querySelectorAll('.card').forEach(c => obs.observe(c));

            } catch (err) {
                console.error('[Balgres] Error RPC:', err);
                if (spinner) spinner.style.display = 'none';
                gridLista.innerHTML =
                    '<div class="no-results">Error al cargar productos.</div>';
            }
        }

        // Listener de los pills
        document.querySelectorAll(
            '.toggle-container input[name="toggle"]'
        ).forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    renderProductos(e.target.dataset.formato);
                }
            });
        });

        // Cargar el primero activo
        const checked = document.querySelector(
            '.toggle-container input[name="toggle"]:checked'
        );
        if (checked) renderProductos(checked.dataset.formato);
    }

    // Ejecutar apenas el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBalgresProducts);
    } else {
        initBalgresProducts();
    }
})();