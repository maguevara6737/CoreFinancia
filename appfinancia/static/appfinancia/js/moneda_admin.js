(function () {

    function limpiarNumero(valor) {
        if (!valor) return '';
        return valor.replace(/,/g, '');
    }

    function formatearNumero(valor) {
        if (!valor) return '';
        let numero = limpiarNumero(valor);

        if (isNaN(numero)) return valor;

        let partes = parseFloat(numero).toFixed(2).split('.');
        partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return partes.join('.');
    }

    document.addEventListener('DOMContentLoaded', function () {

        // 👉 SELECTOR: ajusta según tus campos monetarios
        const campos = document.querySelectorAll(
            'input[name="valor_prestamo"], input[name="valor_cuota_inicial"], input[name="tasa"]'
        );

        campos.forEach(function (input) {

            // Formatear al cargar
            input.value = formatearNumero(input.value);

            // Formatear mientras escribe
            input.addEventListener('input', function () {
                let cursor = input.selectionStart;
                input.value = formatearNumero(input.value);
                input.setSelectionRange(cursor, cursor);
            });

            // Limpiar antes de enviar
            input.form.addEventListener('submit', function () {
                input.value = limpiarNumero(input.value);
            });
        });
    });

})();
