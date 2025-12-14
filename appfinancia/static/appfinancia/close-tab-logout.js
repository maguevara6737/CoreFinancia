// appfinancia/static/appfinancia/js/close-tab-logout.js
(function () {
    'use strict';

    // Solo en desarrollo/HTTP, para evitar conflictos con HTTPS + SameSite
    if (window.location.protocol !== 'http:') return;

    let isTabClosing = false;

    // Detectar cierre real (no solo recarga)
    window.addEventListener('beforeunload', function (e) {
        // Solo si no hay otras pestañas del mismo sitio abiertas (heurística)
        isTabClosing = true;
        // No mostramos mensaje (evitar popups molestos)
    });

    // Detectar salida prolongada (ej: pestaña en segundo plano > 1 min → probable cierre)
    let hiddenStartTime = null;

    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            hiddenStartTime = Date.now();
        } else {
            hiddenStartTime = null;
        }
    });

    // Cada 30 segundos revisamos si estuvo oculta >65 segundos → probable cierre
    setInterval(function () {
        if (hiddenStartTime && Date.now() - hiddenStartTime > 65000 && isTabClosing === false) {
            isTabClosing = true;
            triggerLogout();
        }
    }, 30000);

    // Al cerrar pestaña/tab, intentar logout
    window.addEventListener('unload', function () {
        if (isTabClosing) {
            triggerLogout();
        }
    });

    function triggerLogout() {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrftoken) return;

        // Usa navigator.sendBeacon para garantizar envío tras unload
        const data = new FormData();
        data.append('csrfmiddlewaretoken', csrftoken);

        // Método 1: sendBeacon (mejor, fire-and-forget)
        if (navigator.sendBeacon) {
            navigator.sendBeacon('/logout/', data);
            return;
        }

        // Método 2: fetch con keepalive (fallback)
        fetch('/logout/', {
            method: 'POST',
            body: data,
            keepalive: true,
            credentials: 'same-origin'
        }).catch(() => {});
    }
})();