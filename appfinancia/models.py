# ======================================================
# 1. Librerías estándar de Python
# ======================================================
from datetime import date, datetime, timedelta
from decimal import Decimal

# ======================================================
# 2. Librerías de terceros
# ======================================================
from dateutil.relativedelta import relativedelta
from smart_selects.db_fields import ChainedForeignKey
from django.utils.formats import number_format

# ======================================================
# 3. Django: Núcleo y Base de Datos
from django.conf import settings
from django.db import models, transaction
from django.core.serializers.json import DjangoJSONEncoder
# ======================================================

# ======================================================
# 4. Django: Autenticación y Usuarios
# ======================================================
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# ======================================================
# 5. Django: Validadores y Excepciones
# ======================================================
from django.core.exceptions import ValidationError
from django.core.validators import (
    EmailValidator, 
    MaxLengthValidator, 
    MaxValueValidator, 
    MinLengthValidator, 
    MinValueValidator
)

# ======================================================
# 6. Django: Utilidades (Fechas y HTML)
# ======================================================

from django.utils import timezone
from django.utils.html import format_html

from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP

    
# Nota: Si necesitas 'get_politicas' de .utils, recuerda el riesgo de
# referencia circular. Es mejor importarlo dentro del método que lo use.


# === Consultas y  reportes en el menu lateral ===
class ConsultasReportes(models.Model):
    """
    Modelo ficticio para agrupar vistas de consultas y reportes en el admin.
    No se almacena en la base de datos.
    """
    class Meta:
        managed = False  # ¡Importante! No crea tabla en DB
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas y Reportes"
        permissions = [
            ("puede_consultar_causacion", "Puede acceder a la consulta de causación"),
            # En el futuro, añade más permisos aquí:
            # ("puede_exportar_reporte", "Puede exportar reporte detallado"),
        ]
# === AGREGAR DESPUÉS DE ConsultasReportes ===
class ConsultasReportesProxy(ConsultasReportes):
    class Meta:
        proxy = True
        verbose_name = "Consulta de Causación"
        verbose_name_plural = "Consultas y Reportes"
    
#-----------------------------------------------------------------------------------------
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
        return f"{self.tipo_id}"

    def save(self, *args, **kwargs):
        # Convertir descripcion_id a mayúsculas antes de guardar
        if self.descripcion_id:
            self.descripcion_id = self.descripcion_id.strip().upper()
        super().save(*args, **kwargs)
    
#----------------------------------------------------------------------------------------- 
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

#-----------------------------------------------------------------------------------------
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
        

#-------------------------------------------------------------------------------------*

class Tasas(models.Model):
    TIPO_TASA_OPCIONES = [
        ('CON SEGURO', 'CON SEGURO'),
        ('SIN SEGURO', 'SIN SEGURO'),
        ('ESPECIAL', 'ESPECIAL'),
    ]

    tipo_tasa = models.CharField(
        max_length=15,
        choices=TIPO_TASA_OPCIONES,
        help_text="Tipo de tasa: 'CON SEGURO' o 'SIN SEGURO'."
    )
    
    fecha_aplica = models.DateField(
        help_text="Fecha a partir de la cual rige esta tasa."
    )

    tasa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Valor de la tasa mensual."
    )

    class Meta:
        verbose_name = "Tasa"
        verbose_name_plural = "Tasas"
        # Esto reemplaza la llave primaria compuesta
        unique_together = ('tipo_tasa', 'fecha_aplica')
        ordering = ['-fecha_aplica']

    def __str__(self):
        return f"{self.tipo_tasa} - {self.fecha_aplica}: {self.tasa}%"
      
#-----------------------------------------------------------------------------------------

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

#-----------------------------------------------------------------------------------------
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
        
#-----------------------------------------------------------------------------------------
class Vendedores(models.Model):
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
        
#-----------------------------------------------------------------------------------------

class Numeradores(models.Model):
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
        

#-----------------------------------------------------------------------------------------

class Clientes(models.Model):
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
        help_text="Tipo de identificación (ej. CC, TI, CE, PA, NIT)."
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
        max_length=120,
        help_text="Dirección del cliente (máximo 120 caracteres)."  #2025-12-10 amplio a 120
    )

    departamento = models.ForeignKey(
        'Departamentos',
        on_delete=models.PROTECT,
        to_field='departamento_id',
        help_text="Departamento del cliente."
    )
   
    municipio = ChainedForeignKey(
        'appfinancia.Municipios', # El modelo al que apunta
        chained_field="departamento", # El nombre del campo LOCAL en este modelo (Clientes)
        chained_model_field="departamento", # El nombre del campo en el modelo DESTINO (Municipio)
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.CASCADE, # También necesita el on_delete como cualquier FK
        help_text="Municipio del cliente. Debe pertenecer al departamento seleccionado."
    )
    
    email = models.EmailField(
        max_length=120,
        validators=[EmailValidator()],
        help_text="Correo electrónico del cliente (máximo 120 caracteres)." #  #2025-12-10 amplio a 120
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

    observaciones = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.cliente_id}" 
  
    def clean(self):
        super().clean()
        from .utils import get_politicas
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

#-----------------------------------------------------------------------------------------
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
    OPCIONES_SI_NO = [
            ('SI', 'SI'),
            ('NO', 'NO'),
    ]


    # Definimos las opciones aquí para que coincidan con la tabla Tasas
    TIPO_TASA_CHOICES = [
        ('CON SEGURO', 'CON SEGURO'),
        ('SIN SEGURO', 'SIN SEGURO'),
        ('ESPECIAL', 'ESPECIAL'),
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

    asesor_id  = models.ForeignKey('Asesores', on_delete=models.PROTECT, to_field='asesor_id',db_column='asesor_id',blank=True)
    aseguradora_id  = models.ForeignKey('Aseguradoras', on_delete=models.PROTECT, to_field='aseguradora_id',db_column='aseguradora_id',blank=True)
    
    vendedor_id  = models.ForeignKey(
        'Vendedores', 
        on_delete=models.PROTECT,
        to_field='cod_venta_id',
        db_column='vendedor_id',
        null=True,
        blank=True, 
        help_text="Codigo de venta"
    )

    
    tipo_tasa = models.CharField(
        max_length=15, # Un poco más de margen por si acaso
        choices=TIPO_TASA_CHOICES,
        null=True,
        blank=True,
        help_text="Seleccione el tipo de tasa"   # (el valor se calculará según la fecha de desembolso en tabla Tasas).
    )

    # === VALORES FINANCIEROS ===
    tasa_mes = models.DecimalField(max_digits=4, decimal_places=2, default=0)    #tasa mensual para reportes y pantalla
    tasa = models.DecimalField(max_digits=4, decimal_places=2, default=0)    #tasa anual para calculos internos
    valor = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Valor", help_text="Valor de la Póliza")
    valor_cuota_1 = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Cuota 1", help_text="Cuota 1")
    numero_transaccion_cuota_1 = models.CharField(max_length=10, blank=True, verbose_name="Pago_Id", help_text="Cuota Inicial/Cuota 1")
    valor_cuota_mensual = models.DecimalField(max_digits=15, decimal_places=2, default=0,help_text="Cuota mensual calculada")
    valor_seguro_mes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tiene_fee = models.CharField(max_length=2, choices=TIENE_FEE_CHOICES, default='NO')
    dia_cobro = models.PositiveSmallIntegerField(default=1, help_text="Día de cobro (1-30)")
    plazo_en_meses = models.PositiveSmallIntegerField(default=10,verbose_name="cantidad cuotas", help_text="cantidad de cuotas mensuales")
    fecha_desembolso = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField(editable=False, null=True, blank=True)
    estado = models.CharField(max_length=14, choices=ESTADO_CHOICES, default='ELABORACION')
    fecha_creacion = models.DateTimeField(default=timezone.now, editable=False)

    ofrece_cuota_inicial = models.CharField(
        max_length=2,
        choices=OPCIONES_SI_NO,
        default='NO',
        help_text="Indique si el cliente ofrece pagar cuota inicial."
    )
    valor_cuota_inicial = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Valor de la cuota Inicial")    

    tiene_oneroso = models.CharField(
        max_length=2,
        choices=OPCIONES_SI_NO,
        default='NO',
        verbose_name="¿Tiene Oneroso?",
        help_text="Indique si el seguro tiene beneficiario oneroso."
    )
    
    entidad_onerosa = models.ForeignKey(
        'EntidadesFinancieras',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Entidad Onerosa",
        help_text="Seleccione la entidad financiera beneficiaria."
    )

    class Meta:
        verbose_name = "Desembolso"
        verbose_name_plural = "Desembolsos"
        ordering = ['-fecha_desembolso']
        permissions = [
            ("can_revert_desembolso", "Puede revertir un desembolso ya procesado"),
        ]
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
        from .utils import get_politicas
        try:
            politicas = get_politicas()
        except Exception as e:
            raise ValidationError(f"Error al cargar políticas: {e}")

        errores = {}

        # 1. Tipo de tasa obligatorio
        if not self.tipo_tasa:
            errores['tipo_tasa'] = "El tipo de tasa es obligatorio para pasar a 'A desembolsar'."
                # Validar tasa          
        
        # 2. Tasa válida  <-- suspendo validacion la tasa no se muestra, se calcula con tabla tasas 2026-01-07
        #if self.tasa <= 0:
        #    errores['tasa'] = "La tasa debe ser mayor a 0%."
        #elif not (politicas.tasa_min <= self.tasa <= politicas.tasa_max):
        #    errores['tasa'] = f"La tasa debe estar entre {politicas.tasa_min}% y {politicas.tasa_max}%."

        #3. Valor del préstamo válido 
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

    def obtener_tasa_vigente(self):
        """Busca la tasa en la tabla Tasas según el tipo y la fecha."""
        from .models import Tasas # Import local para evitar importación circular
        
        tasa_obj = Tasas.objects.filter(
            tipo_tasa=self.tipo_tasa,
            fecha_aplica__lte=self.fecha_desembolso  # Menor o igual a la fecha de desembolso
        ).order_by('-fecha_aplica').first() # Trae la más reciente de las encontradas

        if tasa_obj:
            return tasa_obj.tasa #-- tasa mes
        return 0

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        from decimal import Decimal
        import math

        # 1. RESET Y ACTUALIZACIÓN DE TASA
        if self.tipo_tasa and self.fecha_desembolso:
            tasa_mensual_db = self.obtener_tasa_vigente()
            if tasa_mensual_db > 0:
                self.tasa_mes = tasa_mensual_db
                self.tasa = (tasa_mensual_db * 12).quantize(Decimal('0.01'))
            else:
                self.tasa_mes = 0
                self.tasa = 0
                raise ValidationError(
                    f"No existe una tasa configurada para {self.tipo_tasa} "
                    f"en la fecha {self.fecha_desembolso}"
                )

        # --- NUEVA SECCIÓN: VALIDACIÓN DE REGLAS DE SEGURO ---
        # Convertimos a string y mayúsculas para evitar errores de digitación
        nombre_tasa = str(self.tipo_tasa).upper()
        seguro_valor = Decimal(str(self.valor_seguro_mes or 0))

        if "CON SEGURO" in nombre_tasa:
            if seguro_valor <= 0:
                raise ValidationError({
                    'valor_seguro_mes': "El campo 'valor seguro mes' debe ser mayor a cero cuando la tasa es 'CON SEGURO'."
                })
        
        elif "SIN SEGURO" in nombre_tasa:
            if seguro_valor != 0:
                raise ValidationError({
                    'valor_seguro_mes': "El campo 'valor seguro mes' debe ser cero cuando la tasa es 'SIN SEGURO'."
                })
        # Si no es ninguna de las anteriores, entra la condición (3): es opcional.
        # ----------------------------------------------------

        # 2. CÁLCULO DE CUOTA
        if self.valor > 0 and self.plazo_en_meses > 0:
            r_mensual = float(self.tasa_mes) / 100
            n = float(self.plazo_en_meses)
            p = float(self.valor)
            
            if r_mensual > 0:
                # Fórmula de amortización francesa
                factor = math.pow(1 + r_mensual, n)
                cuota_capital_interes = p * (r_mensual * factor) / (factor - 1)
            else:
                cuota_capital_interes = p / n
            
            # Sumamos el seguro y redondeamos a la unidad
            resultado = Decimal(str(cuota_capital_interes)) + seguro_valor
            self.valor_cuota_mensual = resultado.quantize(Decimal('1')) 
        else:
            self.valor_cuota_mensual = 0

        # 3. ACTUALIZACIÓN DE CUOTA INICIAL / CUOTA 1
        if self.ofrece_cuota_inicial == 'SI':
            if self.valor_cuota_inicial < self.valor_cuota_mensual:
                # Usamos :.0f en el f-string para que el mensaje de error también se vea sin decimales
                raise ValidationError({
                    'valor_cuota_inicial': f"La inicial debe ser >= {self.valor_cuota_mensual:,.0f}"
                })
            self.valor_cuota_1 = 0
        else:
            self.valor_cuota_inicial = 0
            self.valor_cuota_1 = self.valor_cuota_mensual

        # 4. VALIDACIÓN DE BENEFICIARIO ONEROSO
        if self.tiene_oneroso == 'SI' and not self.entidad_onerosa:
            raise ValidationError({
                'entidad_onerosa': "Si marcó SI tiene 'Oneroso', debe seleccionar la Entidad Financiera."
            })
 
        # Usamos un atributo temporal (no se guarda en la BD)
        if self.tiene_oneroso == 'NO' and self.entidad_onerosa:
            self.entidad_onerosa = None
            self._mostrar_warning_oneroso = True

        if self.tiene_oneroso == 'NO':
            self.entidad_onerosa = None

        # 5. VALIDACIÓN DE ESTADOS
        if not self._state.adding:
            try:
                # Acceso dinámico para evitar colisiones de importación
                Desembolsos_Model = self.__class__
                estado_anterior = Desembolsos_Model.objects.values_list('estado', flat=True).get(pk=self.pk)
                if self.estado != estado_anterior:
                    self._validar_transicion_permitida(estado_anterior, self.estado)
            except Exception:
                pass

        if self.estado == 'A_DESEMBOLSAR':
            self._validar_estado_a_desembolsar()
#_________________________________________________________________________________

    def save(self, *args, **kwargs):
        from .utils import get_next_prestamo_id, calcular_dv_modulo11
        # Generar ID si es nuevo
        if not self.prestamo_id:
            # es nuevo, genero numero y dv
            id_base = get_next_prestamo_id()
            dv = calcular_dv_modulo11(id_base) 
            self.prestamo_id = (id_base * 10) + dv

        # Calcular fecha de vencimiento
        if self.fecha_desembolso and self.plazo_en_meses > 0:
            self.fecha_vencimiento = self.fecha_desembolso + relativedelta(months=self.plazo_en_meses)

        # Validar antes de guardar
        self.full_clean()

        super().save(*args, **kwargs)
        
        #para crear prestamo automaticamente y sirva de ayuda para asignar el pago de cuota inicial  2025-12-20
        # Crear Prestamos automáticamente al marcar como 'ELABORACION'
        # Solo si aún no existe, y evitando duplicados con consulta a la BD
        if self.estado == 'ELABORACION':
            # Verificación segura en la base de datos (no depende del estado en memoria)
            if not Prestamos.objects.filter(prestamo_id=self.pk).exists():
                with transaction.atomic():
                    Prestamos.objects.create(
                        prestamo_id=self,  # OneToOne con Desembolsos
                        cliente_id=self.cliente_id,
                        asesor_id=self.asesor_id,
                        aseguradora_id=self.aseguradora_id,
                        vendedor_id=self.vendedor_id,
                        tipo_tasa=self.tipo_tasa,
                        tasa=self.tasa or 0,
                        tasa_mes=self.tasa_mes or 0,
                        valor=self.valor or 0,
                        valor_cuota_1=self.valor_cuota_1 or 0,
                        valor_cuota_mensual=self.valor_cuota_mensual or 0,
                        valor_seguro_mes=self.valor_seguro_mes or 0,
                        tiene_fee=self.tiene_fee or 'NO',
                        dia_cobro=self.dia_cobro or 1,
                        plazo_en_meses=self.plazo_en_meses or 0,
                        fecha_desembolso=self.fecha_desembolso,
                        fecha_vencimiento=self.fecha_vencimiento,
                        suspender_causacion='NO',
                        revocatoria='NO',
                        ofrece_cuota_inicial=self.ofrece_cuota_inicial or 'NO',
                        valor_cuota_inicial=self.valor_cuota_inicial or 0,
                        tiene_oneroso=self.tiene_oneroso or 'NO',
                        entidad_onerosa=self.entidad_onerosa or None,
                        # Campos con blank=True/null=True quedarán como None si no se asignan
                    )
#Fin desembolsos
        
#-----------------------------------------------------------------------------------------
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

#-----------------------------------------------------------------------------------------

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

#-----------------------------------------------------------------------------------------

class Comentarios_Prestamos(models.Model):
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
  
#-----------------------------------------------------------------------------------------

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

#=============================== BACKEND ================================================================= 2025-11-15
#2025-11-15  Elimino clase abstracta common_fields, elimino Plan_pagos. Normalizo Prestamos, incluyo metodo consulta cuotas y
#            se incluye el plan pagos en la historia prestamos.
#-----------------------------------------------------------------------------------------

class Prestamos(models.Model):

    ESTADO_PRESTAMO_CHOICES = [                   #2026-01-11 <--- para reversion
        ('ELABORACION', 'En Elaboración'), #El préstamo ha sido creado (cuando el desembolso está en borrador) pero aún no es una deuda legal
        ('ACTIVO', 'Activo'),   #El desembolso ya ocurrió, el plan de pagos está vigente y el cliente debe empezar a pagar.
        ('REVERTIDO', 'Revertido'),   #se desembolsó, pero se echó atrás el proceso.
        ('SIN CAUSACION', 'Sin Causacion'), #No causa intereses 
        ('FINALIZADO', 'Finalizado / Pagado'), #Cuando el saldo llega a cero por pagos normales.
        ('ANULADO', 'Anulado'),   #Si el crédito se cancela definitivamente antes de cualquier desembolso
    ] 
    prestamo_id = models.OneToOneField(          
        'Desembolsos',
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='prestamo_id'
    )
    cliente_id = models.ForeignKey('Clientes', on_delete=models.CASCADE, to_field='cliente_id')
    asesor_id = models.ForeignKey('Asesores', on_delete=models.PROTECT, to_field='asesor_id', db_column='asesor_id')
    aseguradora_id = models.ForeignKey('Aseguradoras', on_delete=models.PROTECT, to_field='aseguradora_id', db_column='aseguradora_id', null=True, blank=True)
    vendedor_id = models.ForeignKey('Vendedores', on_delete=models.PROTECT, to_field='cod_venta_id', db_column='vendedor_id', null=True, blank=True)
    tipo_tasa = models.CharField(max_length=15,choices=[('CON SEGURO', 'CON SEGURO'), ('SIN SEGURO', 'SIN SEGURO')], null=True, blank=True, help_text="Tipo de tasa aplicada.")
    tasa_mes = models.DecimalField(max_digits=4, decimal_places=2, default=0)    #tasa mensual para reportes y pantalla
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
    
    OPCIONES_SI_NO = [
            ('SI', 'SI'),
            ('NO', 'NO'),
    ]

    ofrece_cuota_inicial = models.CharField(
        max_length=2,
        choices=OPCIONES_SI_NO,
        default='NO',
        help_text="Indique si el cliente ofrece pagar cuota inicial."
    )
    valor_cuota_inicial = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Valor de la cuota Inicial")    

    tiene_oneroso = models.CharField(
        max_length=2,
        choices=OPCIONES_SI_NO,
        default='NO',
        verbose_name="¿Tiene Oneroso?",
        help_text="Indique si el seguro tiene beneficiario oneroso."
    )
    
    entidad_onerosa = models.ForeignKey(
        'EntidadesFinancieras',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Entidad Onerosa",
        help_text="Seleccione la entidad financiera beneficiaria."
    )
    estado = models.CharField(
        max_length=15, 
        choices=ESTADO_PRESTAMO_CHOICES, 
        default='ELABORACION'
    )

    class Meta:
        verbose_name = "Prestamo"
        verbose_name_plural = "Prestamos"

    def __str__(self):
        return f"{self.prestamo_id.prestamo_id}"


    #_________________________________________________________________________________________________
    #funcion para calcular cuotas atrasadas basada en lo programado vs pagado 2025-12-21

    def cuotas_atrasadas_info(self, fecha_corte=None):
        """
        Devuelve: (número de cuotas atrasadas, días de mora en base 30/360).
        """
        from .models import Fechas_Sistema, Conceptos_Transacciones, Detalle_Aplicacion_Pago
        from decimal import Decimal
        from collections import defaultdict

        if fecha_corte is None:
            fecha_sistema = Fechas_Sistema.objects.first()
            if not fecha_sistema:
                return (0, 0)
            fecha_corte = fecha_sistema.fecha_proceso_actual

        conceptos_plan = ["PLANCAP", "PLANINT", "PLANSEG", "PLANGTO"]
        conceptos = Conceptos_Transacciones.objects.filter(concepto_id__in=conceptos_plan)

        cuotas_vencidas_qs = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id__in=conceptos,
            fecha_vencimiento__lt=fecha_corte,
            numero_cuota__isnull=False
        ).values('numero_cuota', 'fecha_vencimiento').distinct()

        if not cuotas_vencidas_qs:
            return (0, 0)

        cuotas_vencidas = sorted(cuotas_vencidas_qs, key=lambda x: x['fecha_vencimiento'])
        numeros_cuotas = [c['numero_cuota'] for c in cuotas_vencidas]

        monto_plan = defaultdict(Decimal)
        for reg in Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id__in=conceptos,
            numero_cuota__in=numeros_cuotas
        ):
            monto_plan[reg.numero_cuota] += Decimal(str(reg.monto_transaccion))

        monto_pagado = defaultdict(Decimal)
        detalles = Detalle_Aplicacion_Pago.objects.filter(
            historia_prestamo__prestamo_id=self,
            historia_prestamo__numero_cuota__in=numeros_cuotas
        )
        for det in detalles:
            monto_pagado[det.historia_prestamo.numero_cuota] += Decimal(str(det.monto_aplicado))

        fechas_no_cubiertas = [
            c['fecha_vencimiento'] for c in cuotas_vencidas
            if monto_pagado[c['numero_cuota']] < monto_plan[c['numero_cuota']]
        ]

        if not fechas_no_cubiertas:
            return (0, 0)

        cantidad = len(fechas_no_cubiertas)
        fecha_mas_antigua = min(fechas_no_cubiertas)
        dias_atraso = (fecha_corte.year - fecha_mas_antigua.year) * 360 + \
                    (fecha_corte.month - fecha_mas_antigua.month) * 30 + \
                    (fecha_corte.day - fecha_mas_antigua.day)
        dias_atraso = max(dias_atraso, 0)

        return (cantidad, dias_atraso)
    #-.-.-.-
    def cuotas_atrasadas(self):
        return self.cuotas_atrasadas_info()[0]
  
    cuotas_atrasadas.admin_order_field = None  # No ordenable directamente

    def dias_atraso(self):
        return self.cuotas_atrasadas_info()[1]
    dias_atraso.admin_order_field = None  # Lo haremos ordenable con anotación


    #__________________________________________________________________________________________________________________

    def monto_atrasado(self, fecha_corte=None):
        """
        Devuelve: suma de capital, intereses, seguros y gastos vencidos no pagados (de las cuotas vencidas).
        """
        return (
            self.capital_vencido_no_pagado(fecha_corte) +
            self.intereses_vencidos_no_pagados(fecha_corte) +
            self.seguros_vencidos_no_pagados(fecha_corte) +
            self.gastos_vencidos_no_pagados(fecha_corte)
        )

    #__________________________________________________________________________________________________________
    def capital_vencido_no_pagado(self, fecha_corte=None):
        """
        Devuelve: capital de cuotas con fecha_vencimiento < fecha_corte que aún no han sido pagadas.
        """
        from .models import Fechas_Sistema, Conceptos_Transacciones, Detalle_Aplicacion_Pago
        from django.db.models import Sum
        from decimal import Decimal

        if fecha_corte is None:
            fecha_sistema = Fechas_Sistema.objects.first()
            if not fecha_sistema:
                return Decimal('0.00')
            fecha_corte = fecha_sistema.fecha_proceso_actual

        try:
            cap_id = Conceptos_Transacciones.objects.get(concepto_id="PLANCAP")
        except Conceptos_Transacciones.DoesNotExist:
            return Decimal('0.00')

        capital_prog = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=cap_id,
            fecha_vencimiento__lt=fecha_corte
        ).aggregate(total=Sum('monto_transaccion'))['total'] or Decimal('0.00')

        capital_pag = Detalle_Aplicacion_Pago.objects.filter(
            historia_prestamo__prestamo_id=self,
            componente='CAPITAL'
        ).aggregate(total=Sum('monto_aplicado'))['total'] or Decimal('0.00')

        return max(capital_prog - capital_pag, Decimal('0.00'))
    


    #.-.-.-.-.-.-.-.--.--.-.-.-.--.-.-.--.-.-.-.-.-
    #__________________________________________________________________________________________________________________
    '''   ---- borrar, no sirve   2025-12-26
    def monto_atrasado_por_concepto_falta_la_mora(self):
        """
        Calcula el monto total REAL y exacto pendiente de cuotas vencidas (fecha_vencimiento < fecha_corte),
        considerando pagos parciales, usando agregaciones en la base de datos para máxima eficiencia.
        Pero falta la mora...
        """
        from .models import Historia_Prestamos, Fechas_Sistema, Conceptos_Transacciones
        from django.db.models import Sum, F, Value, DecimalField
        from django.db.models.functions import Coalesce
        from decimal import Decimal

        # Obtener fecha de corte
        fecha_sistema = Fechas_Sistema.objects.first()
        if not fecha_sistema:
            return Decimal('0.00')
        fecha_corte = fecha_sistema.fecha_proceso_actual

        # Helper: calcular pendiente para un concepto
        def pendiente_para_concepto(concepto_id, campo_pagado):
            return Historia_Prestamos.objects.filter(
                prestamo_id=self,
                concepto_id__concepto_id=concepto_id,
                fecha_vencimiento__lt=fecha_corte
            ).aggregate(
                total=Sum(
                    F('monto_transaccion') - Coalesce(F(campo_pagado), Value(Decimal('0.00'))),
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            )['total'] or Decimal('0.00')

        # Calcular pendiente por componente
        capital_pend = pendiente_para_concepto("PLANCAP", "abono_capital")
        interes_pend = pendiente_para_concepto("PLANINT", "intrs_ctes")
        seguro_pend = pendiente_para_concepto("PLANSEG", "seguro")
        gastos_pend = pendiente_para_concepto("PLANGTO", "fee")

        total = capital_pend + interes_pend + seguro_pend + gastos_pend
        return total
    '''
    #--- estos metodos de arriba son  para calcular cuotas atrasadas  -----
    #__________________________________________________________________________________________________________________
    #------------------ calculo de intereses de mora --------------------
    '''   ---- borrar, no sirve   2025-12-26
    def intereses_mora_hasta_fecha_OJO_SIN_USO(self, fecha_corte=None):
        """
        Calcula SOLO los intereses de mora (días después de la fecha de vencimiento).
        """
        from .utils import obtener_intereses_causados_a_fecha
        from .models import Fechas_Sistema
        from decimal import Decimal

        if fecha_corte is None:
            fecha_corte = Fechas_Sistema.objects.first().fecha_proceso_actual

        # Intereses totales causados
        intereses_totales = obtener_intereses_causados_a_fecha(self.prestamo_id, fecha_corte)

        # Intereses programados (hasta las fechas de vencimiento)
        from .models import Historia_Prestamos, Conceptos_Transacciones
        concepto_int = Conceptos_Transacciones.objects.get(concepto_id="PLANINT")
        intereses_programados = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=concepto_int,
            fecha_vencimiento__lt=fecha_corte
        ).aggregate(total=models.Sum('monto_transaccion'))['total'] or Decimal('0.00')

        mora = intereses_totales - intereses_programados
        return max(mora, Decimal('0.00'))
    '''
    #==========  metodos de calculo corregidos para dar saldos pendientes ====  2025-12-21
    from decimal import Decimal
    from django.db.models import Sum, Q

    #__________________________________________________________________________________________________________________
    def saldo_capital_pendiente(self):
        """
        Calcula el saldo de capital pendiente REAL:
        - Total capital programado (del plan)
        - Menos capital pagado REAL (desde Detalle_Aplicacion_Pago)
        - Menos excedentes aplicados como capital (AJU_EXC)
        """
        from .models import Conceptos_Transacciones, Detalle_Aplicacion_Pago
        from django.db.models import Sum
        from decimal import Decimal

        # 1. Total capital programado (del plan)
        try:
            cap_id = Conceptos_Transacciones.objects.get(concepto_id="PLANCAP")
        except Conceptos_Transacciones.DoesNotExist:
            return Decimal('0.00')
        
        total_programado = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=cap_id
        ).aggregate(total=Sum('monto_transaccion'))['total'] or Decimal('0.00')

        # 2. Capital pagado REAL (desde detalles de pago)
        capital_pagado = Detalle_Aplicacion_Pago.objects.filter(
            historia_prestamo__prestamo_id=self,
            componente='CAPITAL'
        ).aggregate(total=Sum('monto_aplicado'))['total'] or Decimal('0.00')

        # 3. Excedentes aplicados como capital (AJU_EXC)
        try:
            aju_exc_id = Conceptos_Transacciones.objects.get(concepto_id="AJU_EXC")
            excedentes = Historia_Prestamos.objects.filter(
                prestamo_id=self,
                concepto_id=aju_exc_id
            ).aggregate(total=Sum('abono_capital'))['total'] or Decimal('0.00')
        except Conceptos_Transacciones.DoesNotExist:
            excedentes = Decimal('0.00')

        # Cálculo final
        saldo = total_programado - capital_pagado - excedentes
        return max(saldo, Decimal('0.00'))
    #__________________________________________________________________________________________________________________
    # --- intereses_vencidos_no_pagados: Lo que debe por ints de cuotas atrasadas + ints de mora por cada cuota

    def intereses_vencidos_no_pagados(self, fecha_corte=None):
        """
        Devuelve: intereses programados no pagados + intereses de mora (calculados cuota por cuota con base 30/360).
        La MORa se calcula CUOTA POR CUOTA:
        - Solo para registros PLANCAP con estado='PENDIENTE' y fecha_vencimiento < fecha_corte
        - Sobre el capital PENDIENTE REAL (usando Detalle_Aplicacion_Pago como fuente definitiva)
        - Por los días reales de atraso: (fecha_corte - fecha_vencimiento)
        - Con tasa diaria = tasa_anual / 100 / 360
        """

        if fecha_corte is None:
            fecha_sistema = Fechas_Sistema.objects.first()
            if not fecha_sistema:
                return Decimal('0.00')
            fecha_corte = fecha_sistema.fecha_proceso_actual

        # 1. Intereses programados vencidos no pagados
        intereses_programados = self.intereses_programados_vencidos_no_pagados(fecha_corte)

        # 2. Calcular mora cuota por cuota
        try:
            concepto_capital = Conceptos_Transacciones.objects.get(concepto_id="PLANCAP")
        except Conceptos_Transacciones.DoesNotExist:
            return intereses_programados

        cuotas_pendientes = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=concepto_capital,
            estado="PENDIENTE",
            fecha_vencimiento__lt=fecha_corte
        )

        tasa_diaria = self.tasa / Decimal('100') / Decimal('360')
        mora_total = Decimal('0.00')

        for cuota in cuotas_pendientes:
            capital_original = cuota.monto_transaccion
            pagos_aplicados = Detalle_Aplicacion_Pago.objects.filter(
                historia_prestamo=cuota,
                componente='CAPITAL'
            ).aggregate(total=Sum('monto_aplicado'))['total'] or Decimal('0.00')
            capital_pendiente = capital_original - pagos_aplicados
            if capital_pendiente <= 0:
                continue

            # Cálculo base 30/360
            fv = cuota.fecha_vencimiento
            dias_atraso = (fecha_corte.year - fv.year) * 360 + \
                        (fecha_corte.month - fv.month) * 30 + \
                        (fecha_corte.day - fv.day)
            dias_atraso = max(dias_atraso, 0)

            if dias_atraso > 0:
                interes_mora = (capital_pendiente * tasa_diaria * dias_atraso).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                mora_total += interes_mora

        return intereses_programados + mora_total
    #__________________________________________________________________________________________________________________
    def intereses_programados_vencidos_no_pagados(self, fecha_corte=None):
        """
        Devuelve: intereses de cuotas con fecha_vencimiento < fecha_corte que aún no han sido pagados.
          Calcula intereses vencidos NO pagados:
        - Intereses programados con fecha_vencimiento <= fecha_corte
        - Menos intereses pagados reales (componente='INTERES')
        """
        from .models import Fechas_Sistema, Conceptos_Transacciones, Detalle_Aplicacion_Pago

        if fecha_corte is None:
            fecha_sistema = Fechas_Sistema.objects.first()
            if not fecha_sistema:
                return Decimal('0.00')
            fecha_corte = fecha_sistema.fecha_proceso_actual

        try:
            int_id = Conceptos_Transacciones.objects.get(concepto_id="PLANINT")
        except Conceptos_Transacciones.DoesNotExist:
            return Decimal('0.00')

        intereses_programados = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=int_id,
            fecha_vencimiento__lt=fecha_corte
        ).aggregate(total=Sum('monto_transaccion'))['total'] or Decimal('0.00')

        intereses_pagados = Detalle_Aplicacion_Pago.objects.filter(
            historia_prestamo__prestamo_id=self,
            componente='INTERES'
        ).aggregate(total=Sum('monto_aplicado'))['total'] or Decimal('0.00')

        return max(intereses_programados - intereses_pagados, Decimal('0.00'))

    #__________________________________________________________________________________________________________________
    def seguros_vencidos_no_pagados(self, fecha_corte=None):
        """
        Devuelve: seguros de cuotas con fecha_vencimiento < fecha_corte que aún no han sido pagados.
        Calcula seguros vencidos NO pagados:
        - Seguros programados con fecha_vencimiento <= fecha_corte
        - Menos seguros pagados reales (componente='SEGURO')
        """
        from .models import Fechas_Sistema, Conceptos_Transacciones, Detalle_Aplicacion_Pago
        from django.db.models import Sum
        from decimal import Decimal

        if fecha_corte is None:
            fecha_sistema = Fechas_Sistema.objects.first()
            if not fecha_sistema:
                return Decimal('0.00')
            fecha_corte = fecha_sistema.fecha_proceso_actual

        try:
            seg_id = Conceptos_Transacciones.objects.get(concepto_id="PLANSEG")
        except Conceptos_Transacciones.DoesNotExist:
            return Decimal('0.00')

        seguros_programados = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=seg_id,
            fecha_vencimiento__lt=fecha_corte
        ).aggregate(total=Sum('monto_transaccion'))['total'] or Decimal('0.00')

        seguros_pagados = Detalle_Aplicacion_Pago.objects.filter(
            historia_prestamo__prestamo_id=self,
            componente='SEGURO'
        ).aggregate(total=Sum('monto_aplicado'))['total'] or Decimal('0.00')

        return max(seguros_programados - seguros_pagados, Decimal('0.00'))


    #__________________________________________________________________________________________________________________
    
    def gastos_vencidos_no_pagados(self, fecha_corte=None):
        """
        Devuelve: gastos (fee) de cuotas con fecha_vencimiento < fecha_corte que aún no han sido pagados.
        """
        from .models import Fechas_Sistema, Conceptos_Transacciones, Detalle_Aplicacion_Pago
        from django.db.models import Sum
        from decimal import Decimal

        if fecha_corte is None:
            fecha_sistema = Fechas_Sistema.objects.first()
            if not fecha_sistema:
                return Decimal('0.00')
            fecha_corte = fecha_sistema.fecha_proceso_actual

        try:
            gto_id = Conceptos_Transacciones.objects.get(concepto_id="PLANGTO")
        except Conceptos_Transacciones.DoesNotExist:
            return Decimal('0.00')

        gastos_programados = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=gto_id,
            fecha_vencimiento__lt=fecha_corte
        ).aggregate(total=Sum('monto_transaccion'))['total'] or Decimal('0.00')

        gastos_pagados = Detalle_Aplicacion_Pago.objects.filter(
            historia_prestamo__prestamo_id=self,
            componente='GASTOS'
        ).aggregate(total=Sum('monto_aplicado'))['total'] or Decimal('0.00')

        return max(gastos_programados - gastos_pagados, Decimal('0.00'))

    #__________________________________________________________________________________________________________________
    def total_pendiente_real(self, fecha_corte=None):
        """
        Devuelve: total adeudado a una fecha dada (capital pendiente total + intereses vencidos + seguros + gastos).
        """
        from decimal import Decimal
        capital = self.saldo_capital_pendiente() or Decimal('0.00')
        intereses = self.intereses_vencidos_no_pagados(fecha_corte) or Decimal('0.00')
        seguros = self.seguros_vencidos_no_pagados(fecha_corte) or Decimal('0.00')
        gastos = self.gastos_vencidos_no_pagados(fecha_corte) or Decimal('0.00')
        return capital + intereses + seguros + gastos
    #__________________________________________________________________________________________________________________
    def liquidar_prestamo(self, fecha_liquidacion=None):
        """
        Calcula el adeudo detallado para aplicar_pago.
        - Usa los mismos métodos que el estado de cuenta.
        """
        if fecha_liquidacion is None:
            fecha_sistema = Fechas_Sistema.load()  # o Fechas_Sistema.objects.first()
            if not fecha_sistema or not fecha_sistema.fecha_proceso_actual:
                raise ValueError("No hay fecha de sistema configurada.")
            fecha_liquidacion = fecha_sistema.fecha_proceso_actual

        # === 1. Capital pendiente ===
        capital_pendiente = self.saldo_capital_pendiente()

        # === 2. Intereses ===
        intereses_vencidos = self.intereses_vencidos_no_pagados(fecha_liquidacion)
        intereses_corrientes = self.intereses_programados_vencidos_no_pagados(fecha_liquidacion)
        intereses_mora = max(intereses_vencidos - intereses_corrientes, Decimal('0.00'))

        # === 3. Seguros y gastos ===
        seguros_vencidos = self.seguros_vencidos_no_pagados()
        gastos_vencidos = self.gastos_vencidos_no_pagados()

        # === 4. Total ===
        total_a_pagar = (
            capital_pendiente +
            intereses_vencidos +
            seguros_vencidos +
            gastos_vencidos
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            'capital_pendiente': float(capital_pendiente),
            'intereses_corrientes': float(intereses_corrientes),
            'intereses_mora': float(intereses_mora),
            'seguros_vencidos': float(seguros_vencidos),
            'gastos_vencidos': float(gastos_vencidos),
            'total_a_pagar': float(total_a_pagar),
            'fecha_liquidacion': fecha_liquidacion
        }
    #       ----- fin liquidar prestamo ----
    # _________________________________________________________________
    def calcular_dias_30_360(self, fecha_inicio, fecha_fin):
        """Calcula días con base 30/360: todos los meses = 30 días, año = 360 días."""
        if not fecha_inicio or not fecha_fin:
            return 0
        y1, m1, d1 = fecha_inicio.year, fecha_inicio.month, fecha_inicio.day
        y2, m2, d2 = fecha_fin.year, fecha_fin.month, fecha_fin.day

        # Ajuste: no puede haber día 31 en un mundo de meses de 30 días (Ajuste U.S.)
        if d1 == 31:
            d1 = 30
        if d2 == 31 and d1 == 30:  # o: if d2 == 31: d2 = 30 (variante europea)
            d2 = 30

        return (y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)
    # _________________________________________________________________
    def detalle_cuotas_vencidas_con_mora(self, fecha_aplicacion):
        """
        Devuelve lista de cuotas vencidas con:
        - capital, interes_programado, seguro, gastos, interes_mora
        - usa base 30/360 para días de mora
        - usa self.tasa (en % anual, ej. 20.4)
        """
        from decimal import Decimal, ROUND_HALF_UP
        from collections import defaultdict 

        CONCEPTOS_PLAN = ["PLANCAP", "PLANINT", "PLANSEG", "PLANGTO"]
        registros = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            estado='PENDIENTE',
            fecha_vencimiento__lte=fecha_aplicacion,
            concepto_id__concepto_id__in=CONCEPTOS_PLAN,
            numero_cuota__isnull=False
        ).order_by('numero_cuota', 'concepto_id__concepto_id')

        cuotas = defaultdict(lambda: {
            'numero_cuota': None,
            'fecha_vencimiento': None,
            'capital': Decimal('0.00'),
            'interes_programado': Decimal('0.00'),
            'seguro': Decimal('0.00'),
            'gastos': Decimal('0.00'),
            'dias_mora': 0,
            'interes_mora': Decimal('0.00'),
        })

        CONCEPTO_A_CAMPO = {
            "PLANCAP": "abono_capital",
            "PLANINT": "intrs_ctes",
            "PLANSEG": "seguro",
            "PLANGTO": "fee"
        }

        for reg in registros:
            num_cuota = reg.numero_cuota
            concepto = reg.concepto_id.concepto_id

            if cuotas[num_cuota]['numero_cuota'] is None:
                cuotas[num_cuota]['numero_cuota'] = num_cuota
                cuotas[num_cuota]['fecha_vencimiento'] = reg.fecha_vencimiento
                
                # Protección explícita contra fechas nulas
                if reg.fecha_vencimiento is None:
                    dias_mora = 0
                else:
                    dias_mora = self.calcular_dias_30_360(reg.fecha_vencimiento, fecha_aplicacion)
                
                cuotas[num_cuota]['dias_mora'] = max(dias_mora, 0)

            campo_pago = CONCEPTO_A_CAMPO.get(concepto)
            if campo_pago is None:
                continue

            saldo_actual = getattr(reg, campo_pago, Decimal('0.00'))
            monto_pendiente = reg.monto_transaccion - saldo_actual

            if concepto == 'PLANCAP':
                cuotas[num_cuota]['capital'] += monto_pendiente
            elif concepto == 'PLANINT':
                cuotas[num_cuota]['interes_programado'] += monto_pendiente
            elif concepto == 'PLANSEG':
                cuotas[num_cuota]['seguro'] += monto_pendiente
            elif concepto == 'PLANGTO':
                cuotas[num_cuota]['gastos'] += monto_pendiente

        # ✅ Tasa = x% → dividir entre 100
        tasa_mora_diaria = (self.tasa / Decimal('100')) / Decimal('360')
        for cuota in cuotas.values():
            if cuota['dias_mora'] > 0 and cuota['capital'] > 0:
                cuota['interes_mora'] = (
                    cuota['capital'] * tasa_mora_diaria * cuota['dias_mora']
                ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        cuotas_validas = [c for c in cuotas.values() if c['capital'] > Decimal('0.00')]

        for c in cuotas_validas:
            print(f"Cuota {c['numero_cuota']}: mora={c['interes_mora']}")

        return sorted(cuotas_validas, key=lambda x: x['numero_cuota'])
 

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

    # ✅ Campos adicionales para auditoría de pagos  2025-12-04
    capital_aplicado_periodo = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Monto total de capital aplicado en este período"
    )
    numero_pago_referencia = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Referencia del pago que generó este cierre de periodo"
    )
    # ✅ Campo nuevo para identificar el bloque de registros de un mismo pago 2025-12-04
    numero_asiento_contable = models.PositiveIntegerField(
        default=0,
        help_text="Número único que identifica el bloque de registros de un mismo pago"
    )

    class Meta:
        unique_together = ('prestamo_id', 'fecha_efectiva', 'ordinal_interno', 'fecha_proceso', 'numero_operacion')
        verbose_name = "Historia Prestamo"
        verbose_name_plural = "Historia Prestamos"
        indexes = [
            models.Index(fields=['numero_asiento_contable']),
            models.Index(fields=['prestamo_id', 'numero_asiento_contable']),
        ]

    def __str__(self):
        return f"{self.prestamo_id}  {self.numero_cuota}  {self.concepto_id} " 
    

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

#-----------------------------------------------------------------------------------------
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

#-----------------------------------------------------------------------------------------
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

#-----------------------------------------------------------------------------------------
class Pagos(models.Model):
    TIPO_CUENTA_CHOICES = [
        ('AHORROS', 'Ahorros'),
        ('CORRIENTE', 'Corriente'),
    ]




    ESTADO_PAGO_CHOICES = [
        ('CONCILIADO', 'Conciliado'),
        ('APLICADO', 'Aplicado'),
        ('REVERSADO', 'Reversado'),
    ]

    ESTADO_CONCILIACION_CHOICES = [
        ('cliente o prestamo no existe', 'Cliente o préstamo no existe'),
        ('prestamo_cancelado', 'Préstamo cancelado'),
    ]
    
    pago_id = models.BigIntegerField(primary_key=True)

    nombre_archivo_id = models.CharField(
        max_length=200,
        help_text="Identificador del archivo de origen (no es ForeignKey)",
        db_index=True
    )

    fecha_carga_archivo = models.DateTimeField(default=timezone.now, editable=False)

    # Datos bancarios
    banco_origen = models.CharField(max_length=100, blank=True)
    cuenta_bancaria = models.CharField(max_length=100, blank=True)
    tipo_cuenta_bancaria = models.CharField(max_length=9, choices=TIPO_CUENTA_CHOICES, blank=True)
    canal_red_pago = models.CharField(max_length=100, blank=True)
    ref_bancaria = models.CharField(max_length=100, blank=True)
    ref_red = models.CharField(max_length=100, blank=True)
    ref_cliente_1 = models.CharField(max_length=200, blank=True)
    ref_cliente_2 = models.CharField(max_length=200, blank=True)
    ref_cliente_3 = models.CharField(max_length=200, blank=True)

    # Reportado por el banco
    estado_transaccion_reportado = models.CharField(max_length=20, blank=True)
    cliente_id_reportado = models.CharField(max_length=20, blank=True)
    prestamo_id_reportado = models.CharField(max_length=20, blank=True)
    poliza_id_reportado = models.CharField(max_length=20, blank=True)

    # Resultados de conciliación
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

    # Valor principal del pago
    valor_pago = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Auditoría
    observaciones = models.CharField(max_length=200, blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, editable=False)

    class Meta:
        verbose_name = "Pagos: 3.Confirmados"
        verbose_name_plural = "Pagos: 3.Confirmados"
        
        permissions = [
                    ("can_revert_pago", "Puede revertir aplicaciones de pago"),
                ]

    def __str__(self):
        return f"Pago {self.pago_id} - {self.valor_pago}"

#------------------------------------------------------------------------------------------

# Detalle_Aplicacion  para saber el detalle de pago versus componentes cuotas   2025-11-25
class Detalle_Aplicacion_Pago(models.Model):
    pago = models.ForeignKey('Pagos', on_delete=models.CASCADE, related_name='detalles_aplicacion')
    historia_prestamo = models.ForeignKey('Historia_Prestamos', on_delete=models.CASCADE)
    monto_aplicado = models.DecimalField(max_digits=15, decimal_places=2)
    componente = models.CharField(max_length=15, choices=[
        ('CAPITAL', 'Capital'),
        ('INTERES', 'Interés'),
        ('SEGURO', 'Seguro'),
        ('GASTOS', 'Gastos'),
        ('EXCEDENTE', 'Excedente'),
    ])
    fecha_aplicacion = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Detalle de Aplicación de Pago"
        verbose_name_plural = "Detalles de Aplicación de Pago"

    def __str__(self):
        return f"{self.componente}: {self.monto_aplicado} → Cuota {self.historia_prestamo.numero_cuota}"

#-----------------------------------------------------------------------------------------
#from django.db import models
#from django.conf import settings
#from django.utils import timezone
#from django.core.exceptions import ValidationError
#from datetime import timedelta

class Fechas_Sistema(models.Model):

    ESTADO_SISTEMA_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('CERRADO', 'Cerrado'),
    ]

    MODO_FECHA_CHOICES = [
        ('MANUAL', 'Manual'),
        ('AUTOMATICO', 'Automático'),
    ]
    
    AMBIENTE_CHOICES = [
        ('PRODUCCION', 'Producción'),
        ('CAPACITACION', 'Capacitación'),
        ('PRUEBAS', 'Pruebas'),
    ]

    fecha_proceso_actual = models.DateField(verbose_name="Fecha Proceso Actual")
    fecha_proceso_anterior = models.DateField(verbose_name="Fecha Proceso Anterior")
    fecha_proximo_proceso = models.DateField(verbose_name="Fecha Próximo Proceso")

    estado_sistema = models.CharField(
        max_length=8,
        choices=ESTADO_SISTEMA_CHOICES,
        default='ABIERTO'
    )

    modo_fecha_sistema = models.CharField(
        max_length=10,
        choices=MODO_FECHA_CHOICES,
        default='AUTOMATICO'
    )

    fecha_ultima_modificacion = models.DateTimeField(auto_now=True)

    cambiado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        editable=False,
        null=True, # Permitir null temporalmente para evitar errores de integridad
        blank=True
    )
    
    ambiente_sistema = models.CharField(
        max_length=12,
        choices=AMBIENTE_CHOICES, 
        default='PRUEBAS',
        help_text="Entorno del sistema: Producción, Capacitación, Pruebas"
    )
    
    email_entrante = models.CharField(
        max_length=100,
        null=True, 
        blank=True,
        help_text="Cuenta de correo para solicitudes de Financiación"
    )
    
    email_saliente = models.CharField(
        max_length=300,
        null=True, 
        blank=True,
        help_text="Lista de correos para copias de salida"
    )
    
    class Meta:
        verbose_name = "Parámetros Sistema"
        verbose_name_plural = "Parámetros Sistema"

    def __str__(self):
        return f"Fecha de Proceso: {self.fecha_proceso_actual} - ({self.ambiente_sistema})"

    # 🔹 SINGLETON: Solo permite un registro con ID 1
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    # 🔹 MÉTODO CENTRAL DE ACTUALIZACIÓN AUTOMÁTICA
    def actualizar_fechas_automaticas(self):
        hoy = timezone.now().date()

        if self.fecha_proceso_actual != hoy:
            self.fecha_proceso_anterior = self.fecha_proceso_actual
            self.fecha_proceso_actual = hoy
            self.fecha_proximo_proceso = hoy + timedelta(days=1)

    # 🔹 VALIDACIONES
    def clean(self):

        if self.fecha_proceso_anterior and self.fecha_proceso_actual:
            if self.fecha_proceso_anterior >= self.fecha_proceso_actual:
                raise ValidationError("La fecha anterior debe ser menor a la actual.")

        if self.fecha_proceso_actual and self.fecha_proximo_proceso:
            if self.fecha_proceso_actual >= self.fecha_proximo_proceso:
                raise ValidationError("La fecha próxima debe ser mayor a la actual.")

    @classmethod
    def load(cls):
        """
        Carga el registro único. Si no existe, lo crea de forma segura.
        """
        obj = cls.objects.filter(pk=1).first()
        if not obj:
            # Intentamos obtener el primer superusuario disponible para el campo cambiado_por
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()
            
            hoy = timezone.now().date()
            obj = cls.objects.create(
                pk=1,
                fecha_proceso_anterior=hoy - timedelta(days=1),
                fecha_proceso_actual=hoy,
                fecha_proximo_proceso=hoy + timedelta(days=1),
                cambiado_por=admin_user,
                ambiente_sistema='PRUEBAS',
                estado_sistema='ABIERTO',
                modo_fecha_sistema='AUTOMATICO'
            )

        return obj

        

    def delete(self, *args, **kwargs):
        raise ValidationError("No se permite eliminar los Parámetros del Sistema.")


#-----------------------------------------------------------------------------------------
class Migrados(models.Model):
    """
    Registro de préstamos migrados desde archivos Excel.
    Permite identificar y borrar de forma segura los datos cargados por migración.
    """
    prestamo_id = models.BigIntegerField(
        help_text="ID del préstamo migrado (coincide con Desembolsos.prestamo_id)"
    )
    origen_migracion = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Nombre del archivo Excel de origen (ej. 'aresmig.xlsx')"
    )
    fecha_migracion = models.DateField(
        auto_now_add=True,
        help_text="Fecha en que se realizó la migración"
    )
    hora_migracion = models.DateTimeField(
        auto_now_add=True,
        help_text="Hora exacta en que se registró la migración"
    )

    class Meta:
        verbose_name = "Préstamo Migrado"
        verbose_name_plural = "Préstamos Migrados"
        ordering = ['-fecha_migracion', '-hora_migracion']

    def __str__(self):
        return f"Préstamo {self.prestamo_id} migrado el {self.fecha_migracion} ({self.origen_migracion})"

#-----------------------------------------------------------------------------------------
class InBox_PagosCabezal(models.Model):

    FORMATO_CHOICES = [
        ('1-FORMATO PSE', '1 - Formato PSE'),
        ('2-FORMATO ESTANDAR', '2 - Formato Estándar'),
        ('3-FORMATO EXTRACTO BANCOLOMBIA', '3 - Extracto Bancolombia'),
    ]

    ESTADO_ARCHIVO_CHOICES = [
        ('RECIBIDO', 'Recibido'),
        ('A_PROCESAR', 'A procesar'),
        ('ANULADO', 'Anulado'),
    ]

    # Archivo real subido
    archivo = models.FileField(
        upload_to='pagos_archivos/',
        null=True,
        blank=True,
        help_text="Seleccione el archivo a cargar"
    )

    # Nombre del archivo (solo referencia)
    nombre_archivo_id = models.CharField(
        max_length=100,
        unique=True,
        editable=False
    )

    formato = models.CharField(max_length=30, choices=FORMATO_CHOICES)
    fecha_carga_archivo = models.DateTimeField(default=timezone.now, editable=False)
    banco_origen = models.CharField(max_length=100, blank=True, null=True)

    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    registros_cargados = models.PositiveSmallIntegerField(default=0, editable=False)
    registros_rechazados = models.PositiveSmallIntegerField(default=0, editable=False)

    estado_proceso_archivo = models.CharField(
        max_length=20,
        choices=ESTADO_ARCHIVO_CHOICES,
        default='RECIBIDO'
    )

    observaciones = models.CharField(max_length=200, blank=True)

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        editable=False,
        null=True,
        blank=True
    )

    class Meta:

        verbose_name = "Pagos: 1.Inbox de Archivos"
        verbose_name_plural = "Pagos: 1.Inbox de Archivos"

        ordering = ['-fecha_carga_archivo']

    def __str__(self):
        return f"{self.nombre_archivo_id} ({self.get_formato_display()})"

    def save(self, *args, **kwargs):
        if self.archivo:
            self.nombre_archivo_id = self.archivo.name

        super().save(*args, **kwargs)

#-----------------------------------------------------------------------------------------
class InBox_PagosDetalle(models.Model):    

    CLASE_MOV = [
        ('PAGO_PSE', 'Pago PSE'),
        ('PAGO_BANCOL', 'Pago Bancolombia'),
        ('LOTE_PSE', 'Lote PSE'),
        ('EXLUIDO', 'Excluido'),
    ]

    TIPO_CUENTA_CHOICES = [
        ('AHORROS', 'Ahorros'),
        ('CORRIENTE', 'Corriente'),
    ]
    ESTADO_PAGO_CHOICES = [
        ('RECIBIDO', 'Recibido'),
        ('A_PROCESAR', 'A procesar'),
        ('ANULADO', 'Anulado'),
        ('CONFIRMADO', 'Confirmado'),
        ('A_NORMALIZAR', 'A regularizar'),
        ('EXCLUIDO','Excludio')
    ]
    ESTADO_FRAGMENTACION_CHOICES = [
        ('NO_REQUIERE', 'NO_REQUIERE'),
        ('A_FRAGMENTAR', 'A_FRAGMENTAR'),
        ('FRAGMENTADO', 'FRAGMENTADO'),
    ]
    
    ESTADO_CONCILIACION_CHOICES = [
        ('SI', 'Si'),
        ('NO', 'No'),
    ]
    
    CUOTA_INICIAL_CHOICES = [
        ('SI', 'Si'),
        ('NO', 'No'),
    ]
    
    # Clave primaria autonumérica
    pago_id = models.BigAutoField(primary_key=True)
    lote_pse = models.BigIntegerField(null=True, blank=True)
    fragmento_de  = models.BigIntegerField(null=True, blank=True)

    # Relación con archivo
    nombre_archivo_id = models.ForeignKey(
        InBox_PagosCabezal,
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
    ref_cliente_1 = models.CharField(max_length=200, blank=True)
    ref_cliente_2 = models.CharField(max_length=200, blank=True)
    ref_cliente_3 = models.CharField(max_length=200, blank=True)

    # Reportado por el banco
    estado_transaccion_reportado = models.CharField(max_length=20, blank=True)
    clase_movimiento = models.CharField(max_length=30,choices=CLASE_MOV, null=True, blank=True )
    estado_fragmentacion = models.CharField(max_length=20, blank=True,choices=ESTADO_FRAGMENTACION_CHOICES) 

    cliente_id_reportado = models.CharField(max_length=20, blank=True)
    prestamo_id_reportado = models.CharField(max_length=20, blank=True)
    poliza_id_reportado = models.CharField(max_length=20, blank=True)

    # Conciliado
    cliente_id_real = models.ForeignKey('Clientes', on_delete=models.SET_NULL, null=True, blank=True)
    prestamo_id_real = models.ForeignKey(Prestamos,on_delete=models.SET_NULL,null=True,blank=True)
    poliza_id_real = models.CharField(max_length=20, blank=True)

    # Fechas y horas
    valor_pago = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    #fecha_pago = models.DateField()
    fecha_pago = models.DateTimeField()
    
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, null=True)
    
    conciliacion_id = models.BigIntegerField(null=True,blank=True, db_index=True)
    fecha_conciliacion = models.DateTimeField(null=True, blank=True)
    estado_conciliacion = models.CharField(max_length=2, choices=ESTADO_CONCILIACION_CHOICES, null=True, blank=True)
    cuota_inicial = models.CharField(max_length=2, choices=CUOTA_INICIAL_CHOICES, null=True, blank=True)

    # Auditoría
    observaciones = models.CharField(max_length=200, blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, editable=False)

    class Meta:
        verbose_name = "Pagos: 4.Consultas"
        verbose_name_plural = "Pagos: 4.Consultas"

    def __str__(self):
        valor = number_format(
            self.valor_pago,
            decimal_pos=2,
            use_l10n=True,
            force_grouping=True
        )
        
        return f"Pago {self.pago_id} - $ {valor}"
         
    def save(self, *args, **kwargs):
        is_new = self.pk is None
    
        super().save(*args, **kwargs)
    
        if self.clase_movimiento == "PAGO_BANCOL":
            update_fields = []
    
            if self.lote_pse != self.pago_id:
                self.lote_pse = self.pago_id
                update_fields.append("lote_pse")
    
            if not self.fecha_conciliacion:
                self.fecha_conciliacion = timezone.now()
                update_fields.append("fecha_conciliacion")
    
            if update_fields:
                super().save(update_fields=update_fields)

#-----------------------------------------------------------------------------------------

class PagosParaRegularizar(InBox_PagosDetalle):
    class Meta:
        proxy = True
        verbose_name = "Pagos: 2.Gestión de pagos"
        verbose_name_plural = "Pagos: 2.Gestión de pagos"
        
#-------Esta Clase aun no se utiliza------------------------------------------------------
class PagosCuotaInicial(InBox_PagosDetalle):
    class Meta:
        proxy = True
        verbose_name = "InBox Pago para Regularizar"
        verbose_name_plural = "InBox Pagos para Regularizar"

#-----------------------------------------------------------------------------------------
class Financiacion(models.Model):

    ESTADO_SOLICITUD_CHOICES = [
        ('RECIBIDO', 'Recibido'),
        ('APROBADO', 'Aprobado'),
        ('NEGADO', 'Negado'),
    ]

    SI_NO_CHOICES = [
        ('SI', 'Si'),
        ('NO', 'No'),
    ]

    # Identificación
    solicitud_id = models.BigAutoField(primary_key=True)
    message_id = models.CharField(max_length=255, unique=True)
    financiacion_id = models.CharField(max_length=10, unique=True)
    
    # Datos del correo
    email_origen = models.CharField(max_length=100)
    asunto = models.CharField(max_length=200)
    fecha_solicitud = models.DateTimeField()

    # Datos del cliente
    nombre_completo = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=100)
    numero_documento = models.CharField(max_length=100)
    
    # relación REAL (opcional)
    cliente = models.ForeignKey(Clientes, null=True,blank=True, on_delete=models.PROTECT,related_name="financiaciones")
    desembolso = models.ForeignKey(Desembolsos, null=True,blank=True, on_delete=models.PROTECT,related_name="financiaciones")
    num_pago_cuota_1 = models.ForeignKey(InBox_PagosDetalle, null=True,blank=True, on_delete=models.PROTECT,related_name="financiaciones")
        
    telefono = models.CharField(max_length=100)
    correo_electronico = models.CharField(max_length=100)

    # Datos comerciales
    asesor = models.CharField(max_length=100)
    agencia = models.CharField(max_length=100)
    numero_cuotas = models.CharField(max_length=100)

    # Valores
    valor_prestamo = models.DecimalField(max_digits=13, decimal_places=2, null=True, blank=True)
    valor_cuota_inicial = models.DecimalField(max_digits=13, decimal_places=2, null=True, blank=True)
    valor_seguro_vida = models.DecimalField(max_digits=13, decimal_places=2, null=True, blank=True)
    tasa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # Opciones
    seguro_vida = models.CharField(max_length=2, choices=SI_NO_CHOICES, default='NO')
    
    cliente_nuevo = models.CharField(max_length=2, null=True, blank=True)
    cliente_vetado = models.CharField(max_length=2, null=True, blank=True)
    
    # Póliza
    placas = models.CharField(max_length=100, blank=True)
    numero_poliza = models.CharField(max_length=100, blank=True)

    # Adjuntos
    adjunta_cedula = models.FileField(upload_to='financiacion/cedulas/', null=True, blank=True)
    adjunta_poliza = models.FileField(upload_to='financiacion/polizas/', null=True, blank=True)
    adjunta_segurovida = models.FileField(upload_to='financiacion/segurovida/', null=True, blank=True)
    adjunta_archivo_a = models.FileField(upload_to='financiacion/archivo_a/', null=True, blank=True)
    adjunta_archivo_b = models.FileField(upload_to='financiacion/archivo_b/', null=True, blank=True)
    adjunta_archivo_c = models.FileField(upload_to='financiacion/archivo_c/', null=True, blank=True)
    

    # Estado
    estado_solicitud = models.CharField(
        max_length=20,
        choices=ESTADO_SOLICITUD_CHOICES,
        default='RECIBIDO'
    )

    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # --- Checklist de validación ---
    info_cliente_valida = models.BooleanField(
        default=False,
        verbose_name="Información del cliente válida"
    )
    
    adjunta_documento_identificacion = models.BooleanField(
        default=False,
        verbose_name="Adjuntó documento de identificación"
    )
    
    adjunta_poliza_seguro = models.BooleanField(
        default=False,
        verbose_name="Adjuntó póliza de seguro"
    )
    
    adjunta_autorizacion_datos = models.BooleanField(
        default=False,
        verbose_name="Adjuntó autorización de datos personales"
    )
    
    adjunta_seguro_vida = models.BooleanField(
        default=False,
        verbose_name="Adjuntó seguro de vida (opcional)"
    )

    class Meta:
        verbose_name = "Financiación"
        verbose_name_plural = "Financiación"

    def __str__(self):
        return f"Solicitud #{self.solicitud_id} - {self.nombre_completo}"
        
#-----------------------------------------------------------------------------------------
class Financiacion_PlanPago(models.Model):
    financiacion = models.OneToOneField(
        "Financiacion",
        on_delete=models.CASCADE,
        related_name="fin_plan_pago"
    )

    cliente = models.CharField(max_length=150)
    cliente_id = models.CharField(max_length=30)

    poliza = models.CharField(max_length=100)
    aseguradora = models.CharField(max_length=100)

    valor_poliza = models.DecimalField(max_digits=15, decimal_places=2)
    valor_cuota_0 = models.DecimalField(max_digits=15, decimal_places=2)
    valor_seguro_vida = models.DecimalField(max_digits=15, decimal_places=2)

    tasa_mensual = models.DecimalField(max_digits=10, decimal_places=6)
    plazo_meses = models.IntegerField()

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    aprobado = models.BooleanField(default=False)

    class Meta:
        db_table = "fin_plan_pago"

    def __str__(self):
        return f"Plan Pago - {self.cliente} ({self.plazo_meses} meses)"

#-----------------------------------------------------------------------------------------
class Financiacion_DetallePlanPago(models.Model):
    plan_pago = models.ForeignKey(
        Financiacion_PlanPago,
        on_delete=models.CASCADE,
        related_name="fin_detalles"
    )

    numero_cuota = models.IntegerField()
    valor_cuota = models.DecimalField(max_digits=15, decimal_places=2)
    abono_capital = models.DecimalField(max_digits=15, decimal_places=2)
    intereses = models.DecimalField(max_digits=15, decimal_places=2)
    saldo_capital = models.DecimalField(max_digits=15, decimal_places=2)

    fecha_pago = models.DateField(null=True, blank=True)
    pagada = models.BooleanField(default=False)

    class Meta:
        db_table = "fin_detalle_plan_pago"
        ordering = ["numero_cuota"]

    def __str__(self):
        return f"Cuota {self.numero_cuota} - {self.valor_cuota}"

#--------------------------------------------------------------------------------------

class EntidadesFinancieras(models.Model):
    from .utils import validar_nit 
    nit = models.BigIntegerField(
        primary_key=True,
        validators=[validar_nit],
        help_text="Ingrese el NIT seguido del dígito de verificación, sin espacios ni guiones (Ej: 8600000001)."
    )

    nombre_corto = models.CharField(max_length=15)
    nombre_completo = models.CharField(max_length=100)
    nombre_contacto = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    
    estado = models.CharField(
        max_length=13,
        choices=[('HABILITADO', 'HABILITADO'), ('DESHABILITADO', 'DESHABILITADO')],
        default='HABILITADO'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Entidad Financiera"
        verbose_name_plural = "Entidades Financieras"
        ordering = ['nombre_corto']

    def __str__(self):
        return f"{self.nombre_corto} ({self.nit})"

    def save(self, *args, **kwargs):
        if self.nombre_corto:
            self.nombre_corto = self.nombre_corto.strip().upper()
        if self.nombre_completo:
            self.nombre_completo = self.nombre_completo.strip().upper()
        
        # full_clean es vital para que el validador de NIT se ejecute antes de guardar
        self.full_clean()
        super().save(*args, **kwargs)

#---------------------------------------------------------------------------------------------------
class BitacoraReversiones(models.Model):
    fecha_reversion = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=100)
    proceso = models.CharField(max_length=100) # Ej: "REVERSION_DESEMBOLSO"
    objeto_id = models.CharField(max_length=50) # ID del Desembolso
    asiento_original = models.CharField(max_length=50, null=True)
    asiento_reversion = models.CharField(max_length=50, null=True)
    motivo = models.TextField()
    
    # La parte variable estilo diccionario
    dump_datos_anteriores = models.JSONField() 

    class Meta:
        verbose_name = "Bitácora de Reversión"
        verbose_name_plural = "Bitácora de Reversiones"
#-------------------------------------------------------------------------------------------------/*
class ComprobantePago(models.Model):
    pago = models.OneToOneField('Pagos', on_delete=models.CASCADE, related_name='comprobante')
    
    # Datos esenciales del comprobante
    datos_json = models.JSONField(encoder=DjangoJSONEncoder)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    
    # Campos denormalizados para búsquedas rápidas - ¡CAMBIAR A BigIntegerField!
    prestamo_id = models.BigIntegerField(db_index=True)   # ← CAMBIADO
    cliente_id = models.BigIntegerField(db_index=True)    # ← CAMBIADO
    
    # Resto del modelo igual...
    email_cliente = models.EmailField(blank=True)
    enviado_email = models.BooleanField(default=False)
    fecha_envio_email = models.DateTimeField(null=True, blank=True)
    excluir_envio_automatico = models.BooleanField(
        default=False,
        help_text="Si está marcado, este comprobante NO se enviará en envíos masivos automáticos."
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['prestamo_id']),
            models.Index(fields=['cliente_id']),
            models.Index(fields=['cliente_id', 'fecha_generacion']),
            models.Index(fields=['enviado_email', 'excluir_envio_automatico']),
        ]
        verbose_name = "Comprobante de Pago"
        verbose_name_plural = "Comprobantes de Pago"
    
    def __str__(self):
        return f"Comprobante de Pago #{self.pago.id}"
    
    def save(self, *args, **kwargs):
        # Llenar campos denormalizados si no están presentes
        if not self.prestamo_id and hasattr(self.pago, 'prestamo_id_real'):
            self.prestamo_id = self.pago.prestamo_id_real or 0  # ← Asegurar coherencia
        if not self.cliente_id and hasattr(self.pago, 'cliente_id_real'):
            self.cliente_id = self.pago.cliente_id_real or 0    # ← Asegurar coherencia
        
        # Guardar email del cliente en el momento de la generación
        if not self.email_cliente and hasattr(self.pago, 'cliente') and self.pago.cliente and self.pago.cliente.email:
            self.email_cliente = self.pago.cliente.email
            
        super().save(*args, **kwargs)
#---------------------------------------------------------------------------------------------------
