from django.contrib.auth.decorators import login_required
from django.db import models,transaction
from django.core.validators import MaxLengthValidator, MinLengthValidator, EmailValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from datetime import datetime

from .utils import get_politicas, get_next_prestamo_id


# Create your models here.
#1---------------------------------------------------------------------------------------*
class Tipos_Identificacion(models.Model):
    """
    Modelo para almacenar los tipos de identificación (ej. CC, TI, CE, PA, NIT).
    """
    tipo_id = models.CharField(
        max_length=3,
        primary_key=True,
        help_text="Código del tipo de identificación (máximo 3 caracteres)."
    )

    descripcion_id = models.CharField(
        max_length=20,
        help_text="Descripción del tipo de identificación (máximo 20 caracteres)."
    )

    class Meta:
        verbose_name = "Tipo de Identificación"
        verbose_name_plural = "Tipos de Identificación"
        ordering = ['tipo_id']

    def __str__(self):
        return f"{self.tipo_id} - {self.descripcion_id}"

    def save(self, *args, **kwargs):
        # Convertir descripcion_id a mayúsculas antes de guardar
        if self.descripcion_id:
            self.descripcion_id = self.descripcion_id.strip().upper()
        super().save(*args, **kwargs)
    
    
#2---------------------------------------------------------------------------------------* 
class Asesores(models.Model):
    """
    Modelo para almacenar información de los asesores.
    """
    ESTADO_CHOICES = [
        ('HABILITADO', 'HABILITADO'),
        ('DESHABILITADO', 'DESHABILITADO'),
    ]

    asesor_id = models.CharField(
        max_length=15,
        primary_key=True,
        help_text="Número de identificación del asesor (máximo 15 caracteres alfanuméricos)."
    )

    asesor_nombre = models.CharField(
        max_length=30,
        help_text="Nombre completo del asesor (máximo 30 caracteres)."
    )

    asesor_estado = models.CharField(
        max_length=13,
        choices=ESTADO_CHOICES,
        default='HABILITADO',
        help_text="Estado del asesor: HABILITADO o DESHABILITADO."
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del registro (automática, no editable)."
    )

    class Meta:
        verbose_name = "Asesor"
        verbose_name_plural = "Asesores"
        ordering = ['asesor_nombre']

    def __str__(self):
        return f"{self.asesor_nombre}"

    def save(self, *args, **kwargs):
        # Convertir el nombre a mayúsculas antes de guardar
        if self.asesor_nombre:
            self.asesor_nombre = self.asesor_nombre.strip().upper()
        super().save(*args, **kwargs)  

#3---------------------------------------------------------------------------------------*
class Aseguradoras(models.Model):
    """
    Modelo para almacenar información de las aseguradoras.
    """
    ESTADO_CHOICES = [
        ('HABILITADO', 'HABILITADO'),
        ('DESHABILITADO', 'DESHABILITADO'),
    ]

    aseguradora_id = models.CharField(
        max_length=15,
        primary_key=True,
        help_text="ID único de la aseguradora (máximo 15 caracteres alfanuméricos)."
    )

    aseguradora_nombre = models.CharField(
        max_length=30,
        help_text="Nombre de la aseguradora (máximo 30 caracteres)."
    )

    aseguradora_estado = models.CharField(
        max_length=13,
        choices=ESTADO_CHOICES,
        default='HABILITADO',
        help_text="Estado de la aseguradora: HABILITADO o DESHABILITADO."
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del registro (automática, no editable)."
    )

    class Meta:
        verbose_name = "Aseguradora"
        verbose_name_plural = "Aseguradoras"
        ordering = ['aseguradora_nombre']

    def __str__(self):
        return f"{self.aseguradora_nombre}"

    def save(self, *args, **kwargs):
        # Convertir el nombre a mayúsculas antes de guardar
        if self.aseguradora_nombre:
            self.aseguradora_nombre = self.aseguradora_nombre.strip().upper()
        super().save(*args, **kwargs)
        
#4---------------------------------------------------------------------------------------*
class Tasas(models.Model):
    """
    Modelo que almacena los tipos de tasa permitidos.
    Valores válidos para tipo_tasa: 'CON SEGURO', 'SIN SEGURO'.
    """
    TIPO_TASA_OPCIONES = [
        ('CON SEGURO', 'CON SEGURO'),
        ('SIN SEGURO', 'SIN SEGURO'),
    ]

    tipo_tasa = models.CharField(
        max_length=10,
        primary_key=True,
        choices=TIPO_TASA_OPCIONES,
        help_text="Tipo de tasa: 'CON SEGURO' o 'SIN SEGURO'."
    )

    tasa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Valor de la tasa (por ejemplo: 12.50). Dos enteros y dos decimales."
    )

    class Meta:
        verbose_name = "Tasa"
        verbose_name_plural = "Tasas"

    def __str__(self):
        return f"{self.tipo_tasa}: {self.tasa}%"
        

#5---------------------------------------------------------------------------------------*
class Departamentos(models.Model):
    """
    Modelo que representa los departamentos (estados, regiones, etc.).
    """
    departamento_id = models.PositiveSmallIntegerField(
        primary_key=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(99)
        ],
        help_text="Código numérico del departamento (2 dígitos: 0–99)."
    )

    departamento_nombre = models.CharField(
        max_length=60,
        help_text="Nombre del departamento (máximo 60 caracteres)."
    )

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['departamento_id']

    def __str__(self):
        return f"{self.departamento_id:02d} - {self.departamento_nombre}"

    def save(self, *args, **kwargs):
        # Convertir el nombre a mayúsculas antes de guardar
        if self.departamento_nombre:
            self.departamento_nombre = self.departamento_nombre.strip().upper()
        super().save(*args, **kwargs)

#6---------------------------------------------------------------------------------------*
class Municipios(models.Model):
    """
    Modelo que representa los municipios, asociados a un departamento.
    Clave lógica única: (municipio_id, departamento_id)
    """
    municipio_id = models.PositiveIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(99999)
        ],
        help_text="Código numérico del municipio (5 dígitos: 0–99999)."
    )

    departamento = models.ForeignKey(
        'Departamentos',
        on_delete=models.PROTECT,
        to_field='departamento_id',
        help_text="Departamento al que pertenece el municipio."
    )

    municipio_nombre = models.CharField(
        max_length=60,
        help_text="Nombre del municipio (máximo 60 caracteres)."
    )

    class Meta:
        unique_together = ('municipio_id', 'departamento')
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        ordering = ['departamento', 'municipio_id']

    def __str__(self):
        return f"{self.departamento.departamento_id:02d}{self.municipio_id:03d} - {self.municipio_nombre}"

    def save(self, *args, **kwargs):
        # Convertir el nombre a mayúsculas antes de guardar
        if self.municipio_nombre:
            self.municipio_nombre = self.municipio_nombre.strip().upper()
        super().save(*args, **kwargs)
        
#7---------------------------------------------------------------------------------------*
class Vendedores(models.Model):
    """
    Modelo para gestionar vendedores.
    """
    ESTADO_CHOICES = [
        ('HABILITADO', 'HABILITADO'),
        ('DESHABILITADO', 'DESHABILITADO'),
    ]

    cod_venta_id = models.CharField(
        max_length=15,
        primary_key=True,
        help_text="Código único del vendedor (máximo 15 caracteres alfanuméricos)."
    )

    cod_venta_nombre = models.CharField(
        max_length=30,
        help_text="Nombre del vendedor (máximo 30 caracteres)."
    )

    estado = models.CharField(
        max_length=13,
        choices=ESTADO_CHOICES,
        default='HABILITADO',
        help_text="Estado del vendedor: HABILITADO o DESHABILITADO."
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del registro (automática, no editable)."
    )

    class Meta:
        verbose_name = "Vendedor"
        verbose_name_plural = "Vendedores"
        ordering = ['cod_venta_nombre']

    def __str__(self):
        return f"{self.cod_venta_nombre} ({self.cod_venta_id})"

    def save(self, *args, **kwargs):
        # Convertir el nombre a mayúsculas antes de guardar
        if self.cod_venta_nombre:
            self.cod_venta_nombre = self.cod_venta_nombre.strip().upper()
        super().save(*args, **kwargs)
        


#8---------------------------------------------------------------------------------------*
# models.py
#from django.db import models
#from django.core.exceptions import ValidationError

class Numeradores(models.Model):
    """
    Tabla única global de contadores secuenciales.
    Solo debe existir una fila. Los valores pueden editarse, pero NUNCA disminuir.
    """
    numerador_operacion  = models.PositiveIntegerField(default=1, help_text="Contador para operacion contables.")
    numerador_transaccion = models.PositiveIntegerField(default=1, help_text="Contador para transacciones.")
    numerador_prestamo = models.PositiveIntegerField(default=1, help_text="Contador para préstamos.")
    numerador_conciliacion = models.PositiveIntegerField(default=1, help_text="Contador para conciliaciones.")
    numerador_pagos = models.PositiveIntegerField(default=1, help_text="Contador para pagos.")
    numerador_aux_1 = models.PositiveIntegerField(default=1, help_text="Contador auxiliar 1.")
    numerador_aux_2 = models.PositiveIntegerField(default=1, help_text="Contador auxiliar 2.")
    numerador_aux_3 = models.PositiveIntegerField(default=1, help_text="Contador auxiliar 3.")
    numerador_aux_4 = models.PositiveIntegerField(default=1, help_text="Contador auxiliar 4.")
    numerador_aux_5 = models.PositiveIntegerField(default=1, help_text="Contador auxiliar 5.")

    class Meta:
        verbose_name = "Numerador"
        verbose_name_plural = "Numeradores"

    def __str__(self):
        return "Contadores Secuenciales del Sistema"

    def clean(self):
        super().clean()

        # Solo una fila permitida
        if Numeradores.objects.exclude(pk=self.pk).exists():
            raise ValidationError("❌ Solo se permite una fila de numeradores.")

        # Si es edición, validar que ningún campo disminuya
        if self.pk:
            original = Numeradores.objects.get(pk=self.pk)
            fields = [
                'numerador_operacion', 'numerador_transaccion', 'numerador_prestamo',
                'numerador_conciliacion', 'numerador_pagos',
                'numerador_aux_1', 'numerador_aux_2', 'numerador_aux_3',
                'numerador_aux_4', 'numerador_aux_5'
            ]
            for field in fields:
                new_val = getattr(self, field)
                old_val = getattr(original, field)
                if new_val < old_val:
                    raise ValidationError({
                        field: f"❌ No se permite disminuir este valor (actual: {old_val}, nuevo: {new_val})."
                    })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
#9---------------------------------------------------------------------------------------*
class Clientes(models.Model):
    """
    Modelo para gestionar clientes.
    Clave primaria: cliente_id
    """
    ESTADO_CHOICES = [
        ('HABILITADO', 'HABILITADO'),
        ('DESHABILITADO', 'DESHABILITADO'),
    ]

    cliente_id = models.BigIntegerField(
        primary_key=True,
        help_text="Número de identificación único del cliente (hasta 15 dígitos)."
    )

    tipo_id = models.ForeignKey(
        'Tipos_Identificacion',
        on_delete=models.PROTECT,
        to_field='tipo_id',
        help_text="Tipo de identificación (ej. CC, TI, CE, PA)."
    )

    nombre = models.CharField(
        max_length=40,
        help_text="Nombre del cliente (máximo 40 caracteres)."
    )

    apellido = models.CharField(
        max_length=40,
        help_text="Apellido del cliente (máximo 40 caracteres)."
    )

    fecha_nacimiento = models.DateField(
        help_text="Fecha de nacimiento (formato: AAAA-MM-DD). Debe estar entre 1900-01-01 y hoy."
    )

    telefono = models.BigIntegerField(
        help_text="Número de teléfono (10 dígitos, sin espacios ni guiones)."
    )

    direccion = models.CharField(
        max_length=80,
        help_text="Dirección del cliente (máximo 80 caracteres)."
    )

    departamento = models.ForeignKey(
        'Departamentos',
        on_delete=models.PROTECT,
        to_field='departamento_id',
        help_text="Departamento del cliente."
    )

    municipio = models.ForeignKey(
        'Municipios',
        on_delete=models.PROTECT,
        help_text="Municipio del cliente. Debe pertenecer al departamento seleccionado."
    )

    email = models.EmailField(
        max_length=50,
        validators=[EmailValidator()],
        help_text="Correo electrónico del cliente (máximo 50 caracteres)."
    )

    estado = models.CharField(
        max_length=13,
        choices=ESTADO_CHOICES,
        default='HABILITADO',
        help_text="Estado del cliente: HABILITADO o DESHABILITADO."
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del registro (automática, no editable)."
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.cliente_id})" 

  
  
    def clean(self):
        super().clean()

        # Validar fecha_nacimiento
        if self.fecha_nacimiento:
            hoy = date.today()
            fecha_minima = date(1900, 1, 1)
            if self.fecha_nacimiento > hoy:
                raise ValidationError({'fecha_nacimiento': 'La fecha de nacimiento no puede ser futura.'})
            if self.fecha_nacimiento < fecha_minima:
                raise ValidationError({'fecha_nacimiento': 'La fecha debe ser posterior al 01/01/1900.'})
        

       # Validar fecha_nacimiento con las politicas de crédito
        if self.fecha_nacimiento:
            hoy = date.today()
            edad = hoy.year - self.fecha_nacimiento.year
            if (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
                edad -= 1

            try:
                politicas = get_politicas()
                if not (politicas.edad_min <= edad <= politicas.edad_max):
                    raise ValidationError({
                        'fecha_nacimiento': f"La edad del cliente ({edad} años) debe estar entre.  "
                        f"{politicas.edad_min} y {politicas.edad_max} años."
                    })
            except RuntimeError as e:
                raise ValidationError({'fecha_nacimiento': str(e)})


        # Validar coherencia geográfica
        if self.municipio and self.departamento:
            if self.municipio.departamento != self.departamento:
                raise ValidationError({'municipio': 'El municipio no pertenece al departamento seleccionado.'})

        # Validar teléfono: 10 dígitos exactos
        if self.telefono:
            telefono_str = str(self.telefono)
            if len(telefono_str) != 10:
                raise ValidationError({'telefono': 'El teléfono debe tener exactamente 10 dígitos.'})

        # Validar cliente_id: entre 1 y 15 dígitos
        if self.cliente_id and (self.cliente_id < 1 or self.cliente_id > 999999999999999):
            raise ValidationError({'cliente_id': 'El ID del cliente debe tener entre 1 y 15 dígitos.'})

    def save(self, *args, **kwargs):
        # Convertir nombre, apellido y dirección a mayúsculas antes de guardar
        if self.nombre:
            self.nombre = self.nombre.strip().upper()
        if self.apellido:
            self.apellido = self.apellido.strip().upper()
        if self.direccion:
            self.direccion = self.direccion.strip().upper()
        super().save(*args, **kwargs)

#10---------------------------------------------------------------------------------------*
#desembolsos

#from django.db import models
#from django.core.exceptions import ValidationError
#from django.utils import timezone
#from datetime import date
#from dateutil.relativedelta import relativedelta
#from .utils import get_next_prestamo_id, get_politicas


class Desembolsos(models.Model):
    ESTADO_CHOICES = [
        ('ELABORACION', 'Elaboración'),
        ('A_DESEMBOLSAR', 'A desembolsar'),
        ('DESEMBOLSADO', 'Desembolsado'),
        ('ANULADO', 'Anulado'),
    ]

    TIENE_FEE_CHOICES = [
        ('SI', 'Sí'),
        ('NO', 'No'),
    ]
    #Cargar la fecha de procesos del sistema CoreFinanza
    #hoy = FechasSistemaHelper.get_fecha_proceso_actual()
    
    # === CAMPOS CLAVE ===
    prestamo_id = models.BigIntegerField(
        primary_key=True,
        editable=False,
        help_text="ID único del préstamo, generado automáticamente."
    )

    cliente_id = models.ForeignKey('Clientes', on_delete=models.PROTECT, to_field='cliente_id')
    asesor_id = models.ForeignKey('Asesores', on_delete=models.PROTECT, to_field='asesor_id')
    aseguradora_id = models.ForeignKey('Aseguradoras', on_delete=models.PROTECT, to_field='aseguradora_id')
    vendedor_id = models.ForeignKey('Vendedores', on_delete=models.PROTECT, to_field='cod_venta_id')
    tipo_tasa = models.ForeignKey(
        'Tasas',
        on_delete=models.PROTECT,
        to_field='tipo_tasa',
        null=True,
        blank=True,
        help_text="Tipo de tasa (ej. 'CON SEGURO')."
    )

    # === VALORES FINANCIEROS ===
    tasa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    valor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_cuota_1 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    numero_transaccion_cuota_1 = models.CharField(max_length=10, blank=True, verbose_name="#Trans.Cuota 1")
    valor_cuota_mensual = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_seguro_mes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tiene_fee = models.CharField(max_length=2, choices=TIENE_FEE_CHOICES, default='NO')
    dia_cobro = models.PositiveSmallIntegerField(default=1, help_text="Día de cobro (1-30)")
    plazo_en_meses = models.PositiveSmallIntegerField(default=12)
    fecha_desembolso = models.DateField(default=timezone.now)
    #fecha_desembolso = models.DateField(default=hoy)
    fecha_vencimiento = models.DateField(editable=False, null=True, blank=True)
    estado = models.CharField(max_length=14, choices=ESTADO_CHOICES, default='ELABORACION')
    fecha_creacion = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        verbose_name = "Desembolso"
        verbose_name_plural = "Desembolsos"
        ordering = ['-fecha_desembolso']

    def __str__(self):
        return f"{self.prestamo_id} -  {self.cliente_id}"

    # ═════════════════════════════════════════════════════════════
    # 1. VALIDACIÓN DE TRANSICIÓN DE ESTADO (SOLO: ELABORACION → A_DESEMBOLSAR)
    # ═════════════════════════════════════════════════════════════

    def _validar_transicion_permitida(self, estado_anterior, estado_nuevo):
        """
        Única transición permitida desde el formulario:
          ELABORACION → A_DESEMBOLSAR
        Cualquier otra transición debe hacerse mediante acción explícita.
        """
        if estado_anterior == 'ELABORACION' and estado_nuevo == 'A_DESEMBOLSAR':
            return  # ✅ Permitido
        raise ValidationError(
            "Solo se permite la transición: 'ELABORACION' → 'A_DESEMBOLSAR'. "
            "Para pasar a 'DESEMBOLSADO' o 'ANULADO', use una acción explícita."
        )

    def _validar_estado_a_desembolsar(self):
        """Validaciones exhaustivas al intentar pasar a 'A_DESEMBOLSAR'."""
        try:
            politicas = get_politicas()
        except Exception as e:
            raise ValidationError(f"Error al cargar políticas: {e}")

        errores = {}

        # 1. Tipo de tasa obligatorio
        if not self.tipo_tasa:
            errores['tipo_tasa'] = "El tipo de tasa es obligatorio para pasar a 'A desembolsar'."
                # Validar tasa          
        
        # 2. Tasa válida
        if self.tasa <= 0:
            errores['tasa'] = "La tasa debe ser mayor a 0%."
        elif not (politicas.tasa_min <= self.tasa <= politicas.tasa_max):
            errores['tasa'] = f"La tasa debe estar entre {politicas.tasa_min}% y {politicas.tasa_max}%."

        # 3. Valor del préstamo válido
        if self.valor <= 0:
            errores['valor'] = "El valor del préstamo debe ser mayor a cero."
        elif not (politicas.valor_cred_min <= self.valor <= politicas.valor_cred_max):
            errores['valor'] = f"El valor debe estar entre ${politicas.valor_cred_min:,.0f} y ${politicas.valor_cred_max:,.0f}."

        # 4. Cuota inicial en rango permitido
        if self.valor > 0 and self.valor_cuota_1 > 0:
            min_cuota = self.valor * (politicas.porcentaje_min_cuota_ini / 100)
            max_cuota = self.valor * (politicas.porcentaje_max_cuota_ini / 100)
            if not (min_cuota <= self.valor_cuota_1 <= max_cuota):
                errores['valor_cuota_1'] = f"Cuota inicial debe estar entre ${min_cuota:,.0f} y ${max_cuota:,.0f}."

        # 5. Plazo en rango permitido
        if not (politicas.plazo_min <= self.plazo_en_meses <= politicas.plazo_max):
            errores['plazo_en_meses'] = f"Plazo debe estar entre {politicas.plazo_min} y {politicas.plazo_max} meses."

        # 6. Día de cobro válido
        if not (1 <= self.dia_cobro <= 30):
            errores['dia_cobro'] = "Día de cobro debe estar entre 1 y 30."

        # 7. Fecha de desembolso no futura
        from .utils import FechasSistemaHelper
        #hoy = date.today()
        hoy = FechasSistemaHelper.get_fecha_proceso_actual()
        if self.fecha_desembolso > hoy:
            errores['fecha_desembolso'] = "La fecha de desembolso no puede ser futura."

        # 8. Fecha de desembolso no demasiado antigua
        dias_atras = getattr(politicas, 'dias_max_desembolso_atras', 10)
        min_fecha = hoy - relativedelta(days=dias_atras)
        if self.fecha_desembolso < min_fecha:
            errores['fecha_desembolso'] = f"La fecha no puede ser anterior a {min_fecha} ({dias_atras} días atrás)."

        if errores:
            self.estado = 'ELABORACION'
            raise ValidationError(errores)

    def clean(self):
        super().clean()

        # Validar transición de estado solo en edición
        if not self._state.adding:
            try:
                estado_anterior = Desembolsos.objects.values_list('estado', flat=True).get(pk=self.pk)
            except Desembolsos.DoesNotExist:
                estado_anterior = 'ELABORACION'

            if self.estado != estado_anterior:
                self._validar_transicion_permitida(estado_anterior, self.estado)

        # Ejecutar validaciones de 'A_DESEMBOLSAR' si aplica
        if self.estado == 'A_DESEMBOLSAR':
            self._validar_estado_a_desembolsar()
            

    def save(self, *args, **kwargs):
        # Generar ID si es nuevo
        if not self.prestamo_id:
            self.prestamo_id = get_next_prestamo_id()

        # Calcular fecha de vencimiento
        if self.fecha_desembolso and self.plazo_en_meses > 0:
            self.fecha_vencimiento = self.fecha_desembolso + relativedelta(months=self.plazo_en_meses)

        # Validar antes de guardar
        self.full_clean()

        super().save(*args, **kwargs)
        
#Fin desembolsos


#11---------------------------------------------------------------------------------------*
class Conceptos_Transacciones(models.Model):   #2025-11-15 NOTA: incluir concepto de cuota
    """
    Clase que almacena los códigos y conceptos de transacciones utilizados en el sistema.
    Internamente y externamente se refiere como la tabla maestra de códigos de transacciones.
    """
    ESTADO_CHOICES = [
        ('HABILITADO', 'HABILITADO'),
        ('DESHABILITADO', 'DESHABILITADO'),
    ]

    concepto_id = models.CharField(
        max_length=10,
        primary_key=True,
        help_text="Identificador único del concepto (máximo 10 caracteres)."
    )

    codigo_transaccion = models.CharField(
        max_length=10,
        unique=True,
        help_text="Código de transacción único (máximo 10 caracteres, no duplicable)."
    )

    descripcion = models.CharField(
        max_length=60,
        help_text="Descripción del concepto de transacción (máximo 60 caracteres)."
    )

    estado = models.CharField(
        max_length=13,
        choices=ESTADO_CHOICES,
        default='HABILITADO',
        help_text="Estado del concepto: HABILITADO o DESHABILITADO."
    )

    class Meta:
        verbose_name = "Concepto de Transacción"
        verbose_name_plural = "Conceptos de Transacciones"
        ordering = ['concepto_id']

    def __str__(self):
        return f"{self.codigo_transaccion} - {self.descripcion}"

    def save(self, *args, **kwargs):
        # Convertir todos los campos de texto a mayúsculas
        if self.concepto_id:
            self.concepto_id = self.concepto_id.strip().upper()
        if self.codigo_transaccion:
            self.codigo_transaccion = self.codigo_transaccion.strip().upper()
        if self.descripcion:
            self.descripcion = self.descripcion.strip().upper()
        super().save(*args, **kwargs)



#12--------------------------------------------------------------------------------------*

# models.py
#from django.db import models

class Comentarios(models.Model):
    """
    Modelo que almacena comentarios estandarizados.
    La combinación (operacion_id, evento_id) debe ser única.
    No se permite eliminar registros (solo deshabilitar).
    """
    ESTADO_CHOICES = [
        ('HABILITADO', 'HABILITADO'),
        ('DESHABILITADO', 'DESHABILITADO'),
    ]

    comentario_id = models.AutoField(
        primary_key=True,
        help_text="ID único autonumerado del comentario."
    )

    operacion_id = models.CharField(
        max_length=20,
        help_text="Código de operación (máximo 20 caracteres)."
    )

    evento_id = models.CharField(
        max_length=20,
        help_text="Código de evento (máximo 20 caracteres)."
    )

    comentario = models.CharField(
        max_length=60,
        help_text="Texto del comentario (máximo 60 caracteres)."
    )

    estado = models.CharField(
        max_length=13,
        choices=ESTADO_CHOICES,
        default='HABILITADO',
        help_text="Estado del comentario."
    )

    class Meta:
        #unique_together = ('operacion_id', 'evento_id')
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"

    def __str__(self):
        return f"{self.operacion_id} / {self.evento_id} - {self.comentario}"

    def save(self, *args, **kwargs):
        # Convertir a mayúsculas antes de guardar
        if self.operacion_id:
            self.operacion_id = self.operacion_id.strip().upper()
        if self.evento_id:
            self.evento_id = self.evento_id.strip().upper()
        if self.comentario:
            self.comentario = self.comentario.strip().upper()
        super().save(*args, **kwargs)

#13--------------------------------------------------------------------------------------*
# appfinancia/models.py

class Comentarios_Prestamos(models.Model):
    """
    Registro histórico y no modificable de comentarios asociados a un préstamo.
    """
    numero_comentario = models.AutoField(
        primary_key=True,
        help_text="Número secuencial único del comentario (generado automáticamente)."
    )

    fecha_comentario = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora del comentario (automática al crear)."
    )

    prestamo = models.ForeignKey(
        'Desembolsos',
        on_delete=models.CASCADE,
        to_field='prestamo_id',
        db_column='prestamo_id',
        help_text="Préstamo asociado (admite múltiples comentarios)."
    )


    comentario_catalogo = models.ForeignKey(
        'Comentarios',
        on_delete=models.PROTECT,
        help_text="Comentario estandarizado del catálogo."
    )
    
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        editable=False,
        null=True,  # ← Permitir temporalmente null
        blank=True,
        help_text="Usuario que registró el comentario." 
    )
    
    def save(self, *args, **kwargs):
        # Si es nuevo y no tiene usuario → asignar el usuario actual
        if not self.pk and not self.creado_por:
            # Solo funciona si hay un request (admin, vistas, etc.)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Intenta obtener del kwargs (usado por admin inline)
            user = kwargs.pop('user', None)
            if user and isinstance(user, User):
                self.creado_por = user
            elif hasattr(self, '_current_user'):  # fallback
                self.creado_por = self._current_user

        # Bloquear modificación después de creado
        if self.pk:
            original = Comentarios_Prestamos.objects.get(pk=self.pk)
            if original.creado_por != self.creado_por:
                raise ValueError("No se puede modificar el usuario creador.")
        
        super().save(*args, **kwargs)
 
        
#14--------------------------------------------------------------------------------------*
# appfinancia/models.py
#from django.db import models
#from django.core.exceptions import ValidationError
#from decimal import Decimal
class Politicas(models.Model):
    edad_min = models.PositiveSmallIntegerField(
        default=18,
        help_text="Edad mínima permitida (ej. 18)"
    )
    edad_max = models.PositiveSmallIntegerField(
        default=75,
        help_text="Edad máxima permitida (ej. 75)"
    )

    valor_cred_min = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=Decimal('1000000.00'),
        help_text="Valor mínimo del crédito (ej. 1.000.000,00)"
    )
    valor_cred_max = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=Decimal('50000000.00'),
        help_text="Valor máximo del crédito (ej. 50.000.000,00)"
    )

    porcentaje_min_cuota_ini = models.DecimalField(
        max_digits=4, decimal_places=2,
        default=Decimal('20.00'),
        help_text="Porcentaje mínimo de cuota inicial (%)"
    )
    porcentaje_max_cuota_ini = models.DecimalField(
        max_digits=4, decimal_places=2,
        default=Decimal('50.00'),
        help_text="Porcentaje máximo de cuota inicial (%)"
    )

    tasa_min = models.DecimalField(
        max_digits=4, decimal_places=2,
        default=Decimal('1.50'),
        help_text="Tasa de interés mínima mensual (%)"
    )
    tasa_max = models.DecimalField(
        max_digits=4, decimal_places=2,
        default=Decimal('3.50'),
        help_text="Tasa de interés máxima mensual (%)"
    )

    plazo_min = models.PositiveSmallIntegerField(
        default=12,
        help_text="Plazo mínimo en meses"
    )
    plazo_max = models.PositiveSmallIntegerField(
        default=60,
        help_text="Plazo máximo en meses"
    )

    dias_max_desembolso_atras = models.PositiveSmallIntegerField(
        default=0,
        help_text="Dias máximo desembolsos con fecha anterior"
    )


    class Meta:
        verbose_name = "Política Global"
        verbose_name_plural = "Políticas Globales"

    def __str__(self):
        return "Políticas Globales del Sistema"

    # VALIDACIONES PERSONALIZADAS
    def clean(self):
        if self.edad_max < self.edad_min:
            raise ValidationError("La edad máxima debe ser mayor o igual a la edad mínima.")

        if self.valor_cred_max < self.valor_cred_min:
            raise ValidationError("El valor máximo del crédito debe ser mayor o igual al mínimo.")

        if self.porcentaje_max_cuota_ini < self.porcentaje_min_cuota_ini:
            raise ValidationError("El porcentaje máximo de cuota inicial debe ser mayor o igual al mínimo.")

        if self.tasa_max < self.tasa_min:
            raise ValidationError("La tasa máxima debe ser mayor o igual a la tasa mínima.")

        if self.plazo_max < self.plazo_min:
            raise ValidationError("El plazo máximo debe ser mayor o igual al mínimo.")

    # Solo permite 1 registro
    def save(self, *args, **kwargs):
        self.pk = 1  # Forza siempre el ID = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Para usar en cualquier parte: Politicas.load()"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
#15--------------------------------------------------------------------------------------*

#=============================== BACKEND ================================================================= 2025-11-15
#2025-11-15  Elimino clase abstracta common_fields, elimino Plan_pagos. Normalizo Prestamos, incluyo metodo consulta cuotas y
#            se incluye el plan pagos en la historia prestamos.
#16--------------------------------------------------------------------------------------------------------
    
class Prestamos(models.Model):
    prestamo_id = models.OneToOneField(          
        'Desembolsos',
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='prestamo_id'
    )
    cliente_id = models.ForeignKey('Clientes', on_delete=models.CASCADE, to_field='cliente_id')
    asesor_id = models.ForeignKey('Asesores', on_delete=models.PROTECT, to_field='asesor_id')
    aseguradora_id = models.ForeignKey('Aseguradoras', on_delete=models.PROTECT, to_field='aseguradora_id', null=True, blank=True)
    vendedor_id = models.ForeignKey('Vendedores', on_delete=models.PROTECT, to_field='cod_venta_id', null=True, blank=True)
    tipo_tasa = models.ForeignKey('Tasas', on_delete=models.PROTECT, to_field='tipo_tasa', null=True, blank=True)
    tasa = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    valor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_cuota_1 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_cuota_mensual = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_seguro_mes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tiene_fee = models.CharField(max_length=2, default='NO')
    dia_cobro = models.PositiveSmallIntegerField(default=1)
    plazo_en_meses = models.PositiveSmallIntegerField(default=0)
    fecha_desembolso = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    SUSPENSION_INTRS_CHOICES = [
        ('SI', 'SI'),
        ('NO', 'NO'),
    ]
    REVOCATORIA_CHOICES = [
        ('SI', 'SI'),
        ('NO', 'NO'),
    ]
    suspender_causacion = models.CharField(
        max_length=2,
        choices=SUSPENSION_INTRS_CHOICES,
        help_text="Tiene suspendida la causacion intrs ('SI' o 'NO')."
    )
    fecha_suspension_causacion = models.DateField(null=True, blank=True)
    revocatoria = models.CharField(
        max_length=2,
        choices=REVOCATORIA_CHOICES,
        help_text="Tiene Revocatoria ('SI' o 'NO')."
    )
    fecha_revocatoria = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Prestamo"
        verbose_name_plural = "Prestamos"

    def __str__(self):
        return f"{self.prestamo_id.prestamo_id}"

    # -------------------------------
    # MÉTODOS EXISTENTES (sin cambios)
    def get_payment_schedule(self):
        from .models import Historia_Prestamos, Conceptos_Transacciones
        try:
            concepto_cuota = Conceptos_Transacciones.objects.get(concepto_id="CUOTA")
        except Conceptos_Transacciones.DoesNotExist:
            return []
        cuotas_qs = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=concepto_cuota
        ).order_by('numero_operacion')
        today = timezone.now().date()
        schedule = []
        for cuota in cuotas_qs:
            total_cuota = cuota.abono_capital + cuota.intrs_ctes + cuota.seguro
            if cuota.fecha_vencimiento < today:
                estado = 'MOROSO' if cuota.abono_capital > 0 else 'PROYECTADO'
            elif cuota.fecha_vencimiento == today:
                estado = 'VENCE_HOY'
            else:
                estado = 'PROYECTADO'
            schedule.append({
                'numero_cuota': cuota.numero_operacion,
                'capital': cuota.abono_capital,
                'intereses': cuota.intrs_ctes,
                'seguro': cuota.seguro,
                'total_cuota': total_cuota,
                'fecha_vencimiento': cuota.fecha_vencimiento,
                'estado': estado,
                'fecha_proceso': cuota.fecha_proceso,
            })
        return schedule

    def get_total_cuotas(self):
        return len(self.get_payment_schedule())

    def get_paid_cuotas(self):
        from .models import Historia_Prestamos, Conceptos_Transacciones
        try:
            concepto_cuota = Conceptos_Transacciones.objects.get(concepto_id="CUOTA")
        except Conceptos_Transacciones.DoesNotExist:
            return 0
        today = timezone.now().date()
        return Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=concepto_cuota,
            abono_capital__gt=0,
            fecha_vencimiento__lte=today
        ).count()

    def get_outstanding_balance(self):
        schedule = self.get_payment_schedule()
        return sum(
            cuota['total_cuota'] for cuota in schedule
            if cuota['estado'] in ['PROYECTADO', 'VENCE_HOY', 'MOROSO']
        )




#17--------------------------------------------------------------------------------------------------------
#2025-11-15 actualizo Historia con campos de cuotas
from django.db import models
from django.utils.html import format_html
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime
from decimal import Decimal # Añadido para manejo seguro

# --- Asumiendo que los otros modelos están definidos previamente ---
# class Clientes(models.Model): ...
# class Desembolsos(models.Model): ...
# class Conceptos_Transacciones(models.Model): ...
# class Asesores(models.Model): ...
# class Aseguradoras(models.Model): ...
# class Vendedores(models.Model): ...
# class Tasas(models.Model): ...
# class Prestamos(models.Model): ... (el modelo que tiene la FK a Desembolsos)

class Historia_Prestamos(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Cuota Pendiente'),
        ('PAGADA', 'Pagada'),
        ('CANCELADO', 'Cancelado'),
        ('MOROSO', 'Moroso'),
        ('TRANSACCION', 'Transaccion'),  #2025-11-25  Miguel
    ]

    # Ajustamos el nombre del campo para que sea más claro, si es posible
    # prestamo = models.ForeignKey('Prestamos', on_delete=models.CASCADE) # Opción más clara
    prestamo_id = models.ForeignKey('Prestamos', on_delete=models.CASCADE) # Como está actualmente
    fecha_efectiva = models.DateField(null=True, blank=True)
    fecha_proceso = models.DateField()
    ordinal_interno = models.IntegerField() 
    numero_operacion = models.PositiveIntegerField(default=1, help_text="secuencial de operacion")
    concepto_id = models.ForeignKey('Conceptos_Transacciones', on_delete=models.CASCADE)
    fecha_vencimiento = models.DateField()
    tasa = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    monto_transaccion = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    abono_capital = models.DecimalField(max_digits=15, decimal_places=2, default=0)                                                                     
    intrs_ctes = models.DecimalField(max_digits=15, decimal_places=2, default=0)                                                                     
    seguro = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fee = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    usuario = models.CharField(max_length=15)
    # --- Campos nuevos ---
    numero_cuota = models.IntegerField(null=True, blank=True, help_text="Número de cuota a la que pertenece")
    estado = models.CharField(max_length=14, choices=ESTADO_CHOICES, default='PENDIENTE')

    def detalle_breve(self):
        # Accedemos al cliente a través de la cadena de relaciones:
        # Historia_Prestamos -> Prestamos -> Desembolsos -> Clientes
        try:
            cliente = self.prestamo_id.prestamo_id.cliente_id # Accedemos al objeto Cliente
        except AttributeError:
            # Si alguna relación es nula, lo manejamos
            cliente = None

        # Accedemos al código de la transacción a través de concepto_id
        try:
            codigo_transaccion = self.concepto_id.codigo_transaccion # Usamos 'codigo_transaccion'
        except AttributeError:
            codigo_transaccion = "N/A"

        # Accedemos al ID del préstamo real (desembolso)
        try:
            id_prestamo_real = self.prestamo_id.prestamo_id.prestamo_id # Accedemos al PK del objeto Desembolso
        except AttributeError:
            id_prestamo_real = "N/A"

        # Manejo seguro del monto_transaccion
        monto = self.monto_transaccion
        if monto is None or not isinstance(monto, (int, float, Decimal)):
            monto_formateado = "$0.00"
        else:
            # Aseguramos que sea un número antes de formatear
            monto_num = float(monto)
            monto_formateado = f"${monto_num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") # Formato para es-ES

        # Manejo de campos que podrían ser nulos
        nombre_cliente = getattr(cliente, 'nombre', 'N/A')
        apellido_cliente = getattr(cliente, 'apellido', 'N/A')
        id_cliente = getattr(cliente, 'cliente_id', 'N/A')
        num_cuota = self.numero_cuota if self.numero_cuota is not None else 'N/A'

        return format_html(
            "<div style='font-family:monospace; white-space:pre;'>"
            "{} {} {} - {} - {} - {} - {} - {}"
            "</div>",
            nombre_cliente,
            apellido_cliente,
            id_cliente,
            id_prestamo_real,
            num_cuota,
            codigo_transaccion,
            self.fecha_vencimiento.strftime('%Y/%m/%d'),
            monto_formateado # Usamos el valor ya formateado como string
        ) # Cierre del método detalle_breve

    class Meta:
        unique_together = ('prestamo_id', 'fecha_efectiva', 'fecha_proceso', 'numero_operacion')
        verbose_name = "Historia Prestamo"
        verbose_name_plural = "Historia Prestamos"

    def __str__(self):
        return f"{self.prestamo_id}  {self.numero_cuota}  {self.concepto_id} " 

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)



 
#18--------------------------------------------------------------------------------------------------------
#2025-11-15 Elimino modelo Planpagos se integra con Historia_prestamos

#19--------------------------------------------------------------------------------------------------------
class Bitacora(models.Model):
    secuencial = models.AutoField(primary_key=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)  # Fecha y hora del sistema cuando se crea
    fecha_proceso = models.DateField()  # Campo tipo fecha
    user_name = models.CharField(max_length=30)  # Máximo 30 caracteres
    evento_realizado = models.CharField()  # Máximo 30 caracteres
    proceso = models.CharField()  # Máximo 10 caracteres
    resultado = models.TextField()  # ✅ Cambiado a TextField

    class Meta:
        verbose_name = 'Bitácora'
        verbose_name_plural = 'Bitácoras'

    def __str__(self):
        return f'Bitácora #{self.secuencial} - {self.user_name}'

#20 -----------------------------------------------------------
# Create your models here.                movimiento
class Movimientos(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    cliente_id =  models.ForeignKey('Clientes',
        on_delete=models.CASCADE,
        help_text="Selecciona un cliente, Puedes añadir una nueva categoría haciendo clic en el signo '+'." )         
    asesor_id = models.ForeignKey('Asesores', on_delete=models.DO_NOTHING)

    fecha_creacion = models.DateField(
        auto_now_add=True,
        help_text="Fecha y hora movimiento"
    )
    
    valor_movimiento = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        help_text="Valor mvto"
    )
    fecha_valor_mvto = models.DateField(
        help_text="Fecha valor"
    )
    

#21=========================================================================================        
# === CONTROL DE ARCHIVOS DE PAGOS === 2025/11/24       
#=========================================================================================
# appfinancia/models.py
#from django.db import models
#from django.conf import settings
#from django.utils import timezone
#from decimal import Decimal


class Pagos_Archivos(models.Model):
    FORMATO_CHOICES = [
        ('1-FORMATO PSE', '1 - Formato PSE'),
        ('2-FORMATO ESTANDAR', '2 - Formato Estándar'),
        ('3-FORMATO EXTRACTO BANCOLOMBIA', '3 - Extracto Bancolombia'),
    ]
    ESTADO_ARCHIVO_CHOICES = [
        ('RECIBIDO', 'Recibido'),
        ('PROCESADO', 'Procesado'),
        ('ANULADO', 'Anulado'),
    ]

    nombre_archivo_id = models.CharField(max_length=100, unique=True, editable=False)
    formato = models.CharField(max_length=30, choices=FORMATO_CHOICES)
    fecha_carga_archivo = models.DateTimeField(default=timezone.now, editable=False)
    banco_origen = models.CharField(max_length=100, blank=True, null=True)
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    registros_cargados = models.PositiveSmallIntegerField(default=0, editable=False)
    registros_rechazados = models.PositiveSmallIntegerField(default=0, editable=False)
    estado_proceso_archivo = models.CharField(
        max_length=10,
        choices=ESTADO_ARCHIVO_CHOICES,
        default='RECIBIDO'
    )
    observaciones = models.CharField(max_length=200, blank=True)
    #creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, editable=False)
    creado_por = models.ForeignKey(
                 settings.AUTH_USER_MODEL,
                 on_delete=models.PROTECT,
                 editable=False,
                 null=True,  # ← Permitir temporalmente null
                 blank=True,
                 help_text="Usuario que registró el comentario." )

    class Meta:
        verbose_name = "Archivo de Pagos"
        verbose_name_plural = "Archivos de Pagos"
        ordering = ['-fecha_carga_archivo']

    def __str__(self):
        return f"{self.nombre_archivo_id} ({self.get_formato_display()})"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.creado_por = kwargs.pop('user', None)
        super().save(*args, **kwargs)

#22---------------------------------------------------------------------------------------
class Pagos(models.Model):
    TIPO_CUENTA_CHOICES = [
        ('AHORROS', 'Ahorros'),
        ('CORRIENTE', 'Corriente'),
    ]
    ESTADO_PAGO_CHOICES = [
        ('Recibido', 'Recibido'),
        ('pendiente', 'Pendiente'),
        ('rechazado', 'Rechazado'),
        ('conciliado', 'Conciliado'),
        ('aplicado', 'Aplicado'),
        ('reversado', 'Reversado'),
        ('acreedores', 'Acreedores'),
    ]
    ESTADO_CONCILIACION_CHOICES = [
        ('cliente o prestamo no existe', 'Cliente o préstamo no existe'),
        ('prestamo_cancelado', 'Préstamo cancelado'),
    ]

    # Clave primaria autonumérica
    pago_id = models.BigAutoField(primary_key=True)

    # Relación con archivo
    nombre_archivo_id = models.ForeignKey(
        Pagos_Archivos,
        on_delete=models.PROTECT,
        to_field='nombre_archivo_id',
        help_text="Archivo de origen"
    )
    fecha_carga_archivo = models.DateTimeField(default=timezone.now, editable=False)

    # Datos bancarios
    banco_origen = models.CharField(max_length=100, blank=True)
    cuenta_bancaria = models.CharField(max_length=100, blank=True)
    tipo_cuenta_bancaria = models.CharField(max_length=9, choices=TIPO_CUENTA_CHOICES, blank=True)
    canal_red_pago = models.CharField(max_length=100, blank=True)
    ref_bancaria = models.CharField(max_length=100, blank=True)
    ref_red = models.CharField(max_length=100, blank=True)
    ref_cliente_1 = models.CharField(max_length=100, blank=True)
    ref_cliente_2 = models.CharField(max_length=100, blank=True)
    ref_cliente_3 = models.CharField(max_length=100, blank=True)

    # Reportado por el banco
    estado_transaccion_reportado = models.CharField(max_length=20, blank=True)
    cliente_id_reportado = models.CharField(max_length=20, blank=True)
    prestamo_id_reportado = models.CharField(max_length=20, blank=True)
    poliza_id_reportado = models.CharField(max_length=20, blank=True)

    # Conciliado
    cliente_id_real = models.BigIntegerField(null=True, blank=True)
    prestamo_id_real = models.BigIntegerField(null=True, blank=True)
    poliza_id_real = models.CharField(max_length=20, blank=True)

    # Fechas y horas
    fecha_pago = models.DateField()
    hora_pago = models.TimeField()
    fecha_aplicacion_pago = models.DateTimeField(null=True, blank=True)
    fecha_conciliacion = models.DateTimeField(null=True, blank=True)

    # Estados
    estado_pago = models.CharField(max_length=12, choices=ESTADO_PAGO_CHOICES, default='Recibido')
    estado_conciliacion = models.CharField(max_length=30, choices=ESTADO_CONCILIACION_CHOICES, blank=True)

    # Valores
    valor_pago = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_aplicado_capital = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_aplicado_intereses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_aplicado_seguros = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_aplicado_gastos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_aplicado_acreedores = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_aplicado_otros = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Auditoría
    observaciones = models.CharField(max_length=200, blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, editable=False)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

    def __str__(self):
        return f"Pago {self.pago_id} - {self.valor_pago}"


#23---------------------------------------------------------------------------------------
#=====CONTROL DE FECHAS DEL SISTEMA
#-----------------------------------------------------------------------------------------
        
# appfinancia/models.py
#from django.db import models
#from django.conf import settings
#from django.core.exceptions import ValidationError
#from django.utils import timezone
#from datetime import date, timedelta

class Fechas_Sistema(models.Model):
    ESTADO_SISTEMA_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('CERRADO', 'Cerrado'),
    ]

    MODO_FECHA_CHOICES = [
        ('MANUAL', 'Manual'),
        ('AUTOMATICO', 'Automático'),
    ]

    # Campos principales
    fecha_proceso_actual = models.DateField(
        help_text="Fecha en la que se está procesando actualmente (día hábil)."
    )
    fecha_proceso_anterior = models.DateField(
        help_text="Fecha del último proceso realizado."
    )
    fecha_proximo_proceso = models.DateField(
        help_text="Fecha esperada del próximo proceso."
    )
    estado_sistema = models.CharField(
        max_length=8,
        choices=ESTADO_SISTEMA_CHOICES,
        default='ABIERTO',
        help_text="Controla si el sistema permite operaciones o solo consultas."
    )
    modo_fecha_sistema = models.CharField(
        max_length=10,
        choices=MODO_FECHA_CHOICES,
        default='AUTOMATICO',
        help_text="Automático: se sincroniza con la fecha del sistema. Manual: editable."
    )
    fecha_ultima_modificacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última actualización (sistema)."
    )
    cambiado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        editable=False,
        help_text="Usuario que realizó la última modificación."
    )

    class Meta:
        verbose_name = "Fecha de Sistema"
        verbose_name_plural = "Fechas de Sistema"

    def __str__(self):
        return f"Fechas del Sistema — {self.fecha_proceso_actual} (modo: {self.modo_fecha_sistema})"
    
   
        

    def clean(self):
        #Para configuración automática
        if self.modo_fecha_sistema == 'AUTOMATICO':
           hoy = timezone.now().date()
           self.fecha_proceso_anterior = hoy - timedelta(days=1)
           self.fecha_proceso_actual = hoy
           self.fecha_proximo_proceso = hoy + timedelta(days=1)

        # Validar coherencia de fechas
        if self.fecha_proceso_anterior >= self.fecha_proceso_actual:
            raise ValidationError({
                'fecha_proceso_actual': "La fecha actual debe ser posterior a la anterior."
            })
        if self.fecha_proceso_actual >= self.fecha_proximo_proceso:
            raise ValidationError({
                'fecha_proximo_proceso': "La fecha próxima debe ser posterior a la actual."
            })

    def save(self, *args, **kwargs):
        # Forzar ID = 1 para singleton
        self.pk = 1

        # Si es modo AUTOMÁTICO y es la primera vez del día → actualizar
        if self.modo_fecha_sistema == 'AUTOMATICO':
            hoy = timezone.now().date()
            # Solo actualiza si aún no se ha actualizado hoy
            if not Fechas_Sistema.objects.filter(pk=1).exists():
                # Primer registro
                self.fecha_proceso_anterior = hoy - timedelta(days=1)
                self.fecha_proceso_actual = hoy
                self.fecha_proximo_proceso = hoy + timedelta(days=1)
            else:
                # Verificar si ya se actualizó hoy
                last = Fechas_Sistema.objects.get(pk=1)
                if last.fecha_proceso_actual != hoy:
                    # ¡Nuevo día! Actualizar fechas
                    #self.fecha_proceso_anterior = last.fecha_proceso_actual
                    self.fecha_proceso_anterior = hoy - timedelta(days=1)
                    self.fecha_proceso_actual = hoy
                    self.fecha_proximo_proceso = hoy + timedelta(days=1)

        # Asignar usuario actual (solo en edición)
        from django.contrib.auth import get_user
        request = kwargs.pop('request', None)
        if request:
            self.cambiado_por = request.user
        elif hasattr(self, '_request'):
            self.cambiado_por = self._request.user
        # Si no hay request (ej: shell), usa el último o un usuario por defecto

        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Obtiene o crea el único registro (singleton)"""
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'fecha_proceso_anterior': timezone.now().date() - timedelta(days=1),
                'fecha_proceso_actual': timezone.now().date(),
                'fecha_proximo_proceso': timezone.now().date() + timedelta(days=1),
                'modo_fecha_sistema': 'AUTOMATICO',
                'estado_sistema': 'ABIERTO',
                'cambiado_por_id': 1,  # fallback seguro
            }
        )
        return obj

    def delete(self, *args, **kwargs):
        raise ValidationError("No se permite eliminar el registro de fechas del sistema.")

  
      
#-----------versión ChatGPT   2025/12/05

class BancolombiaExtracto(models.Model):

    ESTADOS_ARCHIVO = [
        ('RECIBIDO', 'Recibido'),
        ('A_CONCILIAR', 'A Conciliar'),
        ('ANULADO', 'Anulado'),
    ]

    nombre_archivo_id = models.CharField(max_length=200, primary_key=True)
    empresa = models.CharField(max_length=60, null=True, blank=True)
    nit = models.CharField(max_length=16, null=True, blank=True)
    numero_cuenta = models.CharField(max_length=12, null=True, blank=True)
    tipo_cuenta = models.CharField(max_length=30, null=True, blank=True)

    fecha_hora_actual = models.CharField(max_length=30, null=True, blank=True)
    fecha_hora_consulta = models.CharField(max_length=30, null=True, blank=True)

    saldo_efectivo_actual = models.CharField(max_length=30, null=True, blank=True)
    saldo_en_canje_actual = models.CharField(max_length=30, null=True, blank=True)
    saldo_total_actual = models.CharField(max_length=30, null=True, blank=True)

    fecha_carga_archivo = models.DateTimeField(default=timezone.now, null=True, blank=True)

    estado_del_archivo = models.CharField(
        max_length=15,
        choices=ESTADOS_ARCHIVO,
        null=True, blank=True
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True
    )

    registro_extracto = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.nombre_archivo_id
     
        
# (hijos)
class BancolombiaMovimientos(models.Model):

    ESTADOS_MOV = [
        ('RECIBIDO', 'Recibido'),
        ('ANULADO', 'Anulado'),
        ('A_CONCILIAR', 'A Conciliar'),
        ('CONCILIADO', 'Conciliado')
    ]

    CLASE_MOV = [
        ('PAGO_DIRECTO_CLIENTE', 'Pago Directo Cliente'),
        ('ABONO_PSE', 'Abono PSE'),
        ('OTROS', 'Otros'),
    ]

    nombre_archivo_id = models.ForeignKey(
        BancolombiaExtracto,
        on_delete=models.CASCADE,
        to_field='nombre_archivo_id'
    )

    movimiento_id = models.BigAutoField(primary_key=True)

    fecha_movimiento = models.DateField(null=True, blank=True)
    descripcion = models.CharField(max_length=70, null=True, blank=True)
    sucursal_canal = models.CharField(max_length=20, null=True, blank=True)
    referencia_1 = models.CharField(max_length=20, null=True, blank=True)
    referencia_2 = models.CharField(max_length=20, null=True, blank=True)
    documento = models.CharField(max_length=20, null=True, blank=True)

    valor = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    estado_movimiento = models.CharField(
        max_length=15,
        choices=ESTADOS_MOV,
        default='RECIBIDO'
    )

    clase_movimiento = models.CharField(
        max_length=30,
        choices=CLASE_MOV,
        null=True,
        blank=True
    )

    cliente_id_real = models.ForeignKey('Clientes', on_delete=models.SET_NULL, null=True, blank=True)
    prestamo_id_real = models.ForeignKey('Prestamos', on_delete=models.SET_NULL, null=True, blank=True)

    registro_extracto = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return f"Mov {self.movimiento_id}"

