/**
 * Cálculo de Cuota Fija (Sistema Francés) en tiempo real
 */
/**
 * CoreFinancia - Sistema de Amortización Francés
 * Cálculo en tiempo real para Financia Seguros
 * /appfinancia/js/financiacion_amortizacion_frances.js
 */
 
document.addEventListener('DOMContentLoaded', function() {
    // 1. Identificación de campos (IDs estándar de Django Admin)
    const prestamoInput = document.getElementById('id_valor_prestamo');
    const tasaInput = document.getElementById('id_tasa');
    const cuotasInput = document.getElementById('id_numero_cuotas');

    // 2. Contenedor donde se mostrará el resultado (Debajo de valor_prestamo)
    const container = document.querySelector('.field-valor_prestamo');

    if (prestamoInput && tasaInput && cuotasInput && container) {
        
        // 3. Crear el elemento visual (Widget de cuota)
        let displayDiv = document.getElementById('cuota-francesa-display');
        if (!displayDiv) {
            displayDiv = document.createElement('div');
            displayDiv.id = 'cuota-francesa-display';
            
            // ESTÉTICA AJUSTADA PARA ALINEACIÓN NATIVA
            displayDiv.style.marginTop = "8px";
            displayDiv.style.padding = "6px 12px";
            displayDiv.style.backgroundColor = "#f8f9fa";
            displayDiv.style.border = "1px solid #dee2e6";
            displayDiv.style.borderLeft = "4px solid #28a745";
            displayDiv.style.borderRadius = "4px";
            displayDiv.style.boxShadow = "2px 2px 5px rgba(0,0,0,0.05)";
            displayDiv.style.fontFamily = '"Roboto", "Lucida Grande", Verdana, Arial, sans-serif';
            
            // EL TRUCO DE ALINEACIÓN:
            // Django Admin suele usar un ancho fijo para las etiquetas.
            displayDiv.style.marginLeft = "170px"; // Ajuste estándar para alinearse con el input
            displayDiv.style.display = "none";     // Se oculta inicialmente
            displayDiv.style.width = "fit-content"; // Para que no se estire a todo lo ancho
            
            container.appendChild(displayDiv);
        }

        // 4. Función principal de cálculo
        function calcular() {
            // Limpieza de caracteres no numéricos (excepto el punto decimal)
            const P = parseFloat(prestamoInput.value.replace(/[^0-9.]/g, '')) || 0;
            const i = (parseFloat(tasaInput.value) / 100) || 0;
            const n = parseInt(cuotasInput.value) || 0;

            // Solo calculamos si los tres valores son mayores a cero
            if (P > 0 && i > 0 && n > 0) {
                // Fórmula Sistema Francés: R = (P * i) / (1 - (1 + i)^-n)
                const cuota = (P * i) / (1 - Math.pow(1 + i, -n));
                
                // Formateador de moneda colombiana
                const formateador = new Intl.NumberFormat('es-CO', {
                    style: 'currency',
                    currency: 'COP',
                    maximumFractionDigits: 0
                });

                const cuotaFormateada = formateador.format(cuota);

                // Inyectar el contenido en el div
                displayDiv.innerHTML = `
                    <span style="color: #666; font-size: 0.85em;">Estimación Cuota Base (Francés):</span>
                    <strong style="color: #155724; font-size: 1.1em; margin-left: 8px;">${cuotaFormateada}</strong>
                `;
                
                displayDiv.style.display = "inline-block"; // Mostrar cuando haya cálculo
            } else {
                displayDiv.style.display = "none"; // Ocultar si los datos están incompletos
            }
        }

        // 5. Asignar los "escuchadores" de eventos para cambios en tiempo real
        [prestamoInput, tasaInput, cuotasInput].forEach(input => {
            input.addEventListener('input', calcular);
            // También escuchamos 'change' por si el navegador autocompleta
            input.addEventListener('change', calcular);
        });

        // 6. Ejecución inmediata al cargar (por si el formulario ya tiene datos)
        calcular();
    } else {
        console.warn("CoreFinancia: No se encontraron todos los campos necesarios en el formulario.");
    }
});