from datetime import date


def create_prestamo(desembolso):
    from  models import Prestamos
    """
    Creates a Prestamo record based on a Desembolso instance.
    Uses default values for optional fields if not provided.
    """
    prestamo = Prestamos.objects.create(
        prestamo_id=desembolso.prestamo_id,
        cliente_id=desembolso.cliente_id,
        asesor_id=desembolso.asesor_id,
        aseguradora_id=desembolso.aseguradora_id,
        vendedor_id=desembolso.vendedor_id,
        tipo_tasa=desembolso.tipo_tasa,
        tasa=desembolso.tasa,
        valor=desembolso.valor,
        valor_cuota_1=desembolso.valor_cuota_1,
        valor_cuota_mensual=desembolso.valor_cuota_mensual,
        valor_seguro_mes=desembolso.valor_seguro_mes,
        tiene_fee=desembolso.tiene_fee,
        dia_cobro=desembolso.dia_cobro,
        plazo_en_meses=desembolso.plazo_en_meses,
        fecha_desembolso=desembolso.fecha_desembolso,
        fecha_vencimiento=desembolso.fecha_vencimiento,
        suspender_causacion=desembolso.suspender_causacion or 'NO',
        fecha_suspension_causacion=desembolso.fecha_suspension_causacion or date.today(),
        revocatoria=desembolso.revocatoria or 'NO',
        fecha_revocatoria=desembolso.fecha_revocatoria or date.today(),
    )
    return prestamo