// ======================================================
// 🪙 FORMATO GLOBAL DE MONEDAS - DJANGO ADMIN
// Separador miles: ","
// Separador decimal: "."
// Formatea en tiempo real y limpia antes de guardar
// ======================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("🪙 moneda_admin_global.js cargado correctamente");

    /**
     * Formatea número con separador de miles
     * Ej: 1234567.89 → 1,234,567.89
     */
    function formatNumber(value) {
        if (!value) return "";

        // Quitar separadores existentes
        value = value.replace(/,/g, "");

        // Permitir solo números y punto
        value = value.replace(/[^0-9.]/g, "");

        let parts = value.split(".");

        // Formatear parte entera
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");

        // Limitar decimales a 2
        if (parts.length > 1) {
            parts[1] = parts[1].substring(0, 2);
        }

        return parts.join(".");
    }

    /**
     * Limpia separadores antes de enviar al backend
     * Ej: 1,234,567.89 → 1234567.89
     */
    function unformatNumber(value) {
        if (!value) return "";
        return value.replace(/,/g, "");
    }

    /**
     * Detectar inputs numéricos de moneda
     */
    function isCurrencyField(input) {
        const name = input.name || "";
        return (
            name.includes("valor") ||
            name.includes("monto") ||
            name.includes("importe") ||
            name.includes("tasa")
        );
    }

    /**
     * Aplicar formato a los campos
     */
    document.querySelectorAll("input[type='text']").forEach(function (input) {

        if (!isCurrencyField(input)) return;

        // Formatear al escribir
        input.addEventListener("input", function () {
            let cursor = input.selectionStart;
            let originalLength = input.value.length;

            input.value = formatNumber(input.value);

            let newLength = input.value.length;
            cursor += newLength - originalLength;

            input.setSelectionRange(cursor, cursor);
        });

        // Formatear si ya trae valor (editar registro)
        input.value = formatNumber(input.value);

        // Limpiar antes de guardar
        let form = input.closest("form");
        if (form) {
            form.addEventListener("submit", function () {
                input.value = unformatNumber(input.value);
            });
        }
    });

});
