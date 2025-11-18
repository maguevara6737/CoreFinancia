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
        return f"{self.nombre} {self.apellido} ({self.cliente_id})"

  
  
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
#from dateutil.relativedelta import relativedelta

# models.py
 # Asegúrate de tener estas funciones

class Desembolsos(models.Model):
    ESTADO_CHOICES = [
        ('ELABORACION', 'ELABORACION'),
        ('PENDIENTE', 'PENDIENTE'),
        ('DESEMBOLSADO', 'DESEMBOLSADO'),
        ('ANULADO', 'ANULADO'),
    ]

    TIENE_FEE_CHOICES = [
        ('SI', 'SI'),
        ('NO', 'NO'),
    ]

    # Clave primaria autogenerada
    prestamo_id = models.BigIntegerField(
        primary_key=True,
        editable=False,
        help_text="ID único del préstamo, generado automáticamente."
    )

    # Claves foráneas
    cliente_id = models.ForeignKey(
        'Clientes',
        on_delete=models.PROTECT,
        to_field='cliente_id',
        help_text="Cliente asociado."
    )

    asesor_id = models.ForeignKey(
        'Asesores',
        on_delete=models.PROTECT,
        to_field='asesor_id',
        help_text="Asesor responsable."
    )

    aseguradora_id = models.ForeignKey(
        'Aseguradoras',
        on_delete=models.PROTECT,
        to_field='aseguradora_id',
        help_text="Aseguradora del préstamo."
    )

    vendedor_id = models.ForeignKey(
        'Vendedores',
        on_delete=models.PROTECT,
        to_field='cod_venta_id',
        help_text="Vendedor asociado."
    )

    tipo_tasa = models.ForeignKey(
        'Tasas',
        on_delete=models.PROTECT,
        to_field='tipo_tasa',
        blank=True,
        help_text="Tipo de tasa (ej. 'CON SEGURO')."
    )

    # Valores financieros
    tasa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        help_text="Tasa de interés aplicada (dos enteros, dos decimales)."
    )

    valor = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Valor total del préstamo."
    )

    valor_cuota_1 = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Valor de la primera cuota."
    )

    numero_transaccion_cuota_1 = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="#Trans.Cuota 1",
        help_text="Número de transacción de la primera cuota (opcional)."
    )

    valor_cuota_mensual = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Valor de la cuota mensual."
    )

    valor_seguro_mes = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Valor del seguro mensual."
    )

    tiene_fee = models.CharField(
        max_length=2,
        choices=TIENE_FEE_CHOICES,
        help_text="Indica si el préstamo tiene fee ('SI' o 'NO')."
    )

    dia_cobro = models.PositiveSmallIntegerField(
        blank=True,
        help_text="Día de cobro mensual (1 a 30)."
    )

    plazo_en_meses = models.PositiveSmallIntegerField(
        blank=True,
        default=0,
        help_text="Plazo en meses."
    )

    fecha_desembolso = models.DateField(
        default=timezone.now,
        help_text="Fecha de desembolso."
    )

    fecha_vencimiento = models.DateField(
        editable=False,
        null=True,
        blank=True,
        help_text="Fecha de vencimiento calculada automáticamente."
    )

    estado = models.CharField(
        max_length=13,
        choices=ESTADO_CHOICES,
        default='ELABORACION',
        help_text="Estado del desembolso."
    )

    #    fecha_creacion = models.DateTimeField(
    #        auto_now_add=True,
    #        help_text="Fecha y hora de creación (automática)."
    #    )

    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora de creación (automática, no editable)."
    )

    class Meta:
        verbose_name = "Desembolso"
        verbose_name_plural = "Desembolsos"
        ordering = ['-fecha_desembolso']

    def __str__(self):
        return f"Desembolso {self.prestamo_id} -  {self.cliente_id}"


    def clean(self):        
        super().clean()

        try:
            politicas = get_politicas()
        except Exception as e:
            raise ValidationError(f"Error al cargar políticas: {e}")

        # Validar tasa          
        if self.tasa is not None:
            if not (politicas.tasa_min <= self.tasa <= politicas.tasa_max):
               raise ValidationError({
                'tasa': f"La tasa debe estar entre {politicas.tasa_min} y {politicas.tasa_max}."
                })

        # Validar valor_cuota_1 (solo si valor > 0)
        if self.valor and self.valor > 0 and self.valor_cuota_1 is not None:
            min_cuota = Decimal(self.valor) * Decimal(politicas.porcentaje_min_cuota_ini) * Decimal(0.01)
            max_cuota = Decimal(self.valor) * Decimal(politicas.porcentaje_max_cuota_ini) * Decimal(0.01) 
            if not (min_cuota <= Decimal(self.valor_cuota_1) <= max_cuota):
                raise ValidationError({
                    'valor_cuota_1': f"La cuota inicial debe estar entre {min_cuota:,.2f} y {max_cuota:,.2f}."
                })
        
        
        # Validar valor_seguro_mes ≤ 20% del valor
        if self.valor and self.valor_seguro_mes is not None:
            max_seguro = Decimal(self.valor) * Decimal(0.020)
            if Decimal(self.valor_seguro_mes) > max_seguro:
                raise ValidationError({
                    'valor_seguro_mes': f"El seguro no puede superar el 20% del valor ({max_seguro:,.2f})."
                })

        # Validar plazo_en_meses
        if self.plazo_en_meses:
            if not (politicas.plazo_min <= self.plazo_en_meses <= politicas.plazo_max):
                raise ValidationError({
                    'plazo_en_meses': f"El plazo debe estar entre {politicas.plazo_min} y {politicas.plazo_max} meses."
                })

        # Validar dia_cobro (1-30)
        if self.dia_cobro and not (1 <= self.dia_cobro <= 30):
            raise ValidationError({'dia_cobro': 'El día de cobro debe estar entre 1 y 30.'})

        # Validar fecha_desembolso
        if self.fecha_desembolso:
            hoy = date.today()
            if self.fecha_desembolso > hoy:
                raise ValidationError({'fecha_desembolso': 'No puede ser futura.'})
            
            # Suponemos que politicas tiene dias_max_desembolso_atras
            #dias_atras = getattr(politicas, 'dias_max_desembolso_atras', 10)
            dias_atras = politicas.dias_max_desembolso_atras
            min_fecha = hoy - timedelta(days=dias_atras)
            if self.fecha_desembolso < min_fecha:
                raise ValidationError({
                    'fecha_desembolso': f"No puede ser menor a {min_fecha} ({dias_atras} días atrás)."
                })

        # Validar si el desembolso es cero, el Valor de la Cuota_1 también será cero
        if Decimal(self.valor) == 0: 
           self.valor_cuota_1 = 0

        #Validar si la tasa es con seguro, debe ingresar el valor del seguro
        
        if not self.tipo_tasa:
            tip_tasa = self.tipo_tasa.tipo_tasa
            if tip_tasa.startswith("CON") and Decimal(self.valor_seguro_mes) == 0:
               raise ValidationError("La tasa es con seguro. Debe ingresar el valor del seguro mensual.")
            if tip_tasa.startswith("SIN"):
               self.valor_seguro_mes = 0
                         
        #print(f"Tipo de tasa seleccionada: {self.tipo_tasa}")
        #print(f"Tipo de tasa tip_tasa: {tip_tasa}")
        #print(f"valor seguro mes: {self.valor_seguro_mes}")
        
                  
    def save(self, *args, **kwargs):
        # 1. Asignar prestamo_id
        if not self.prestamo_id:
            self.prestamo_id = get_next_prestamo_id()

        # 2. Asignar tasa desde tipo_tasa (si no se sobrescribe)        
        if self.tipo_tasa and not self.tasa:
           self.tasa = self.tipo_tasa.tasa

        # 3. Asignar fecha_desembolso = hoy si no se define
        if not self.fecha_desembolso:
            self.fecha_desembolso = date.today()

        # 4. Calcular fecha_vencimiento
        if self.fecha_desembolso and self.plazo_en_meses:
            self.fecha_vencimiento = self.fecha_desembolso + relativedelta(months=self.plazo_en_meses)

        # 5. Estado por defecto
        if not self.estado:
            self.estado = 'PENDIENTE'
        
        # 6. Validar
        self.full_clean()

        super().save(*args, **kwargs)

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
        help_text="Usuario que registró el comentario."
    )


    # Propiedades para acceder a campos del catálogo (solo lectura)
    @property
    def operacion_id(self):
        return self.comentario_catalogo.operacion_id if self.comentario_catalogo else None

    @property
    def evento_id(self):
        return self.comentario_catalogo.evento_id if self.comentario_catalogo else None

    @property
    def prestamo_id(self):
        return self.prestamo.prestamo_id if self.prestamo else None

    @property
    def comentario_id(self):
        return self.comentario_catalogo_id

    class Meta:
        verbose_name = "Comentario de Préstamo"
        verbose_name_plural = "Comentarios de Préstamos"
        ordering = ['-fecha_comentario']

    def __str__(self):
        return f"Comentario {self.numero_comentario} - Préstamo {self.prestamo_id}"

    def save(self, *args, **kwargs):
        # Bloquear modificación después de creado
        if self.pk:
            raise ValueError("❌ No se permiten modificaciones en comentarios ya creados.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Bloquear eliminación
        raise ValueError("❌ No se permite eliminar comentarios.")
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
    prestamo_id = models.ForeignKey('Desembolsos', on_delete=models.CASCADE)
    cliente_id = models.ForeignKey('Clientes', on_delete=models.CASCADE)
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
    suspender_causacion =  models.CharField(
        max_length=2,
        choices=SUSPENSION_INTRS_CHOICES,
        help_text="Tiene suspendida la causacion intrs ('SI' o 'NO')."
    )
    fecha_suspension_causacion =  models.DateField(null=True, blank=True)

    revocatoria =  models.CharField(
        max_length=2,
        choices=REVOCATORIA_CHOICES,
        help_text="Tiene Revocatoria ('SI' o 'NO')."
    )
    fecha_revocatoria =  models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Prestamo"
        verbose_name_plural = "Prestamos"

    def __str__(self):
        return f" {self.prestamo_id}"

    #-------------------------------
    # ✅ NUEVO MÉTODO: Obtiene el plan de pagos desde Historia_Prestamos y debe estar aqui en prestamos
    def get_payment_schedule(self):
        """
        Devuelve el plan de pagos completo del préstamo como una lista de diccionarios.
        Lee los registros de Historia_Prestamos con concepto_id='CUOTA'.
        
        Cada elemento tiene:
        - numero_cuota: número de la cuota (1, 2, 3...)
        - capital: abono a capital
        - intereses: intereses causados
        - seguro: valor del seguro mensual
        - total_cuota: suma de capital + intereses + seguro
        - fecha_vencimiento: fecha de vencimiento
        - estado: 'PROYECTADO', 'PAGADO' o 'MOROSO' (basado en fecha actual)
        
        Solo devuelve cuotas (concepto_id='CUOTA').
        """
        from .models import Historia_Prestamos, Conceptos_Transacciones

        try:
            concepto_cuota = Conceptos_Transacciones.objects.get(concepto_id="CUOTA")
        except Conceptos_Transacciones.DoesNotExist:
            return []  # Si no existe el concepto, no hay cuotas

        # Filtrar solo las cuotas asociadas a este préstamo
        cuotas_qs = Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=concepto_cuota
        ).order_by('numero_operacion')  # Ordenado por número de cuota

        today = timezone.now().date()

        schedule = []
        for cuota in cuotas_qs:
            total_cuota = cuota.abono_capital + cuota.intrs_ctes + cuota.seguro

            # Determinar estado
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
    #-------------------------------




#17--------------------------------------------------------------------------------------------------------
#2025-11-15 actualizo Historia con campos de cuotas
from django.db import models
class Historia_Prestamos(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('CANCELADO', 'Cancelado'),
        ('MOROSO', 'Moroso'),
    ]

    prestamo_id = models.ForeignKey('Prestamos', on_delete=models.CASCADE)
    fecha_efectiva = models.DateField()
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
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='PENDIENTE')

    def detalle_breve(self):
        return f"{self.prestamo_id} - {self.numero_cuota} - {self.concepto_id} - {self.fecha_vencimiento} - {self.monto_transaccion:,.2f}"
    detalle_breve.short_description = "Detalle Breve"


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