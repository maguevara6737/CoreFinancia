// appfinancia/static/appfinancia/js/session-expiry.js
(function () {
    'use strict';

    // Solo en desarrollo/HTTP, para evitar conflictos con HTTPS + SameSite
    if (window.location.protocol !== 'http:') return;

    // Bandera para evitar múltiples llamadas
    let sessionExpired = false;

    // Opción 1: detectar cierre de pestaña/ventana
    window.addEventListener('beforeunload', function (e) {
        if (!sessionExpired) {
            // No podemos hacer fetch aquí (bloqueado por navegador),
            // pero podemos limpiar sessionStorage y marcar flag
            sessionStorage.clear();
            sessionExpired = true;
        }
    });

    // Opción 2 (mejor): usar visibilitychange + temporizador
    // Se activa cuando el usuario cierra pestaña o cambia de pestaña por >1 min
    let hiddenStartTime = null;

    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            // Usuario salió de la pestaña
            hiddenStartTime = Date.now();
        } else {
            // Volvió: cancelar temporizador
            hiddenStartTime = null;
        }
    });

    // Cada 10 segundos revisamos si estuvo oculto >65 segundos (más de 1 minuto)
    setInterval(function () {
        if (hiddenStartTime && Date.now() - hiddenStartTime > 65000 && !sessionExpired) {
            // Posible cierre de pestaña → cerrar sesión
            fetch('/logout/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                    'Accept': 'application/json'
                },
                keepalive: true  // permite enviar tras unload
            }).finally(() => {
                sessionExpired = true;
                // Opcional: redirigir si aún está en la pestaña
                if (!document.hidden) {
                    window.location.href = '/login/';
                }
            });
        }
    }, 10000);

})();