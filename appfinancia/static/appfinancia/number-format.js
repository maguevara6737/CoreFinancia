// appfinancia/static/appfinancia/js/number-format.js
document.addEventListener('DOMContentLoaded', function () {
    // === CONFIGURACIÓN: ajusta estos selectores si cambian los nombres de los campos ===
    const moneyFields = [
        'valor',
        'valor_cuota_1',
        'valor_seguro_mes',
        'tasa'  // si quieres formato con 2 decimales (ej: 2.50)
    ];

    // Busca todos los inputs tipo "number" o "text" con esos nombres
    const inputs = Array.from(document.querySelectorAll(
        moneyFields.map(name => `input[name="${name}"]`).join(', ')
    ));

    // Inicializa los campos con formato visual (solo lectura visual, no cambia el valor real)
    inputs.forEach(input => {
        const rawValue = input.value.trim();
        if (rawValue && !isNaN(rawValue)) {
            const num = parseFloat(rawValue);
            if (!isNaN(num)) {
                input.dataset.raw = rawValue; // guarda valor original en data-raw
                input.value = num.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        }
    });

    // === Al enfocar: mostrar valor crudo para edición ===
    inputs.forEach(input => {
        input.addEventListener('focus', function () {
            if (this.dataset.raw !== undefined) {
                this.value = this.dataset.raw;
            }
        });
    });

    // === Al salir: volver a formatear visualmente ===
    inputs.forEach(input => {
        input.addEventListener('blur', function () {
            const val = parseFloat(this.value);
            if (!isNaN(val)) {
                this.dataset.raw = val.toString();
                this.value = val.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            } else {
                // Si no es número, limpiar
                delete this.dataset.raw;
                this.value = '';
            }
        });
    });

    // === Antes de enviar el formulario: restaurar valor crudo (¡IMPORANTE!) ===
    const forms = document.querySelectorAll('form[method="post"]');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            // Restaurar valores crudos en todos los campos monetarios
            inputs.forEach(input => {
                if (input.dataset.raw !== undefined) {
                    input.value = input.dataset.raw;
                }
            });
        });
    });

    // === Soporte para inline forms dinámicos (añadidos por "Add another") ===
    // Django emite evento 'formset:added' desde django/contrib/admin/static/admin/js/inlines.js
    document.addEventListener('formset:added', function (event) {
        const form = event.detail.form;
        const newInputs = Array.from(form.querySelectorAll(
            moneyFields.map(name => `input[name$="${name}"]`).join(', ')
        ));
        newInputs.forEach(input => {
            // Inicializar nuevo input
            const raw = input.value.trim();
            if (raw && !isNaN(raw)) {
                const num = parseFloat(raw);
                if (!isNaN(num)) {
                    input.dataset.raw = raw;
                    input.value = num.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                }
            }

            // Añadir event listeners
            input.addEventListener('focus', function () {
                if (this.dataset.raw !== undefined) {
                    this.value = this.dataset.raw;
                }
            });

            input.addEventListener('blur', function () {
                const val = parseFloat(this.value);
                if (!isNaN(val)) {
                    this.dataset.raw = val.toString();
                    this.value = val.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                } else {
                    delete this.dataset.raw;
                    this.value = '';
                }
            });
        });
    });
});