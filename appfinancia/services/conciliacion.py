# appfinancia/services/conciliacion.py
from decimal import Decimal
from django.db import transaction
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

MAX_CANDIDATES_DP = 40  # límite práctico para DP; si hay más, usamos fallback greedy

def _to_cents(dec):
    """Convierte Decimal a int (centavos) para evitar problemas de float."""
    if dec is None:
        return 0
    return int((Decimal(dec) * 100).quantize(Decimal('1')))

def _find_subset_indices_amounts(amounts_cents, target_cents):
    """
    Encontrar combinación de índices cuya suma de amounts_cents == target_cents.
    amounts_cents: lista de ints.
    Retorna lista de índices o None.
    Algoritmo: DP incremental (map sum->lista índices). Determinista y suficientemente rápido
    para < ~40 elementos. Si falla, devuelve None.
    """
    sums = {0: []}
    for idx, amt in enumerate(amounts_cents):
        # iterar sobre snapshot de keys para no mutar durante iteración
        current_sums = list(sums.keys())
        for s in current_sums:
            new = s + amt
            if new in sums:
                continue
            # crear nueva combinación
            sums[new] = sums[s] + [idx]
            if new == target_cents:
                return sums[new]
    return None

def _greedy_try(amounts_cents, target_cents):
    """
    Intento greedily usando mayores primero. No garantiza solución aunque exista,
    pero es rápido como fallback para muchos candidatos.
    Retorna lista de indices o None.
    """
    # sort indices by amount descending
    indexed = sorted(enumerate(amounts_cents), key=lambda x: -x[1])
    selected = []
    total = 0
    for idx, amt in indexed:
        if total + amt <= target_cents:
            selected.append(idx)
            total += amt
            if total == target_cents:
                return selected
    return None

def conciliacion_por_movimiento(movimiento, candidatos_qs):
    """
    Trata de conciliar un movimiento bancario (movimiento: instancia InBox_PagosDetalle)
    con candidatos (QuerySet con instancias InBox_PagosDetalle).
    Retorna tuple (ok: bool, mensaje: str, detalles: dict)
    Si ok==True, se hicieron las actualizaciones:
      - cada pago hijo: lote_pse = movimiento.pago_id, estado_pago = 'SI'
      - movimiento: estado_pago = 'SI'
    Todo dentro de transaction.atomic()
    """
    from ..models import InBox_PagosDetalle  # import local para evitar ciclos

    target = movimiento.valor_pago
    if target is None:
        return False, "Movimiento sin valor definido.", {}

    target_cents = _to_cents(target)

    candidatos = list(candidatos_qs)  # materializar
    # filtrar candidatos con valor > 0
    candidatos = [c for c in candidatos if c.valor_pago and Decimal(c.valor_pago) > 0]

    if not candidatos:
        return False, "No hay candidatos válidos para conciliar.", {}

    amounts_cents = [_to_cents(c.valor_pago) for c in candidatos]

    indices = None
    if len(candidatos) <= MAX_CANDIDATES_DP:
        indices = _find_subset_indices_amounts(amounts_cents, target_cents)

    if indices is None:
        # fallback greedy si DP no encontró o hay demasiados candidatos
        indices = _greedy_try(amounts_cents, target_cents)

    if indices is None:
        return False, "No se encontró combinación de pagos que sume el movimiento.", {
            "candidatos_count": len(candidatos)
        }

    # Ahora aplicar cambios en DB dentro de transacción
    try:
        with transaction.atomic():
            hijos = []
            for idx in indices:
                candidato = candidatos[idx]
                # actualizar campos: lote_pse y estado_pago
                candidato.lote_pse = movimiento.pago_id
                #candidato.estado_pago = "SI"
                candidato.estado_conciliacion = "SI"
                candidato.save(update_fields=["lote_pse", "estado_pago"])
                hijos.append(candidato)

            # marcar movimiento como conciliado
            #movimiento.estado_pago = "SI"
            movimiento.estado_conciliacion = "SI"
            #movimiento.save(update_fields=["estado_pago"])
            movimiento.save(update_fields=["estado_conciliacion"])

        detalles = {
            "movimiento_id": movimiento.pago_id,
            "hijos_creados": len(hijos),
            "hijos_ids": [h.pago_id for h in hijos],
        }
        return True, f"Conciliado: {len(hijos)} pagos asignados al movimiento {movimiento.pago_id}.", detalles

    except Exception as e:
        logger.exception("Error durante conciliación transaccional")
        return False, f"Error guardando conciliación: {e}", {}
