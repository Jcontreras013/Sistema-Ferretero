from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Empresa(models.Model):
    """Configuración fiscal de la empresa emisora (Honduras - SAR)."""

    razon_social = models.CharField("razón social", max_length=200)
    nombre_comercial = models.CharField("nombre comercial", max_length=200, blank=True)
    rtn = models.CharField("RTN", max_length=14, help_text="RTN de la empresa (13-14 dígitos)")
    direccion = models.CharField("dirección", max_length=255, blank=True)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    email = models.EmailField("correo electrónico", blank=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresa (configuración fiscal)"

    def __str__(self):
        return self.razon_social


class RangoAutorizado(models.Model):
    """
    Rango de numeración autorizado por el SAR (Servicio de Administración de
    Rentas de Honduras) bajo el esquema de CAI (Código de Autorización de
    Impresión). El número de documento sigue el formato:
        EEE-PPP-TT-CCCCCCCC
    (Establecimiento-PuntoDeEmisión-TipoDocumento-Correlativo)
    """

    class TipoDocumento(models.TextChoices):
        FACTURA = "01", "Factura"
        NOTA_CREDITO = "02", "Nota de crédito"
        NOTA_DEBITO = "03", "Nota de débito"

    sucursal = models.ForeignKey(
        "sucursales.Sucursal", on_delete=models.PROTECT, related_name="rangos_autorizados",
        verbose_name="sucursal",
    )
    cai = models.CharField(
        "CAI", max_length=50, help_text="Código de Autorización de Impresión emitido por el SAR"
    )
    punto_emision = models.CharField("punto de emisión", max_length=3, default="001")
    tipo_documento = models.CharField(
        "tipo de documento", max_length=2, choices=TipoDocumento.choices, default=TipoDocumento.FACTURA
    )
    rango_inicial = models.PositiveIntegerField("rango inicial")
    rango_final = models.PositiveIntegerField("rango final")
    numero_actual = models.PositiveIntegerField("número actual", help_text="Próximo correlativo a emitir")
    fecha_limite_emision = models.DateField("fecha límite de emisión")
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "Rango autorizado (CAI)"
        verbose_name_plural = "Rangos autorizados (CAI)"
        ordering = ["-activo", "sucursal"]

    def __str__(self):
        return f"{self.sucursal.codigo}-{self.punto_emision}-{self.tipo_documento} ({self.cai})"

    def clean(self):
        if self.rango_inicial > self.rango_final:
            raise ValidationError("El rango inicial no puede ser mayor al rango final.")

    def correlativo_disponible(self):
        return (
            self.activo
            and self.rango_inicial <= self.numero_actual <= self.rango_final
            and self.fecha_limite_emision >= timezone.localdate()
        )

    def siguiente_numero(self):
        """Formatea y reserva el siguiente correlativo del rango. No hace save()."""
        if not self.activo:
            raise ValidationError("Este rango de CAI no está activo.")
        if self.fecha_limite_emision < timezone.localdate():
            raise ValidationError("El CAI venció su fecha límite de emisión.")
        if self.numero_actual > self.rango_final:
            raise ValidationError("Se agotó el rango de numeración autorizado por el SAR.")

        numero_formateado = (
            f"{self.sucursal.codigo}-{self.punto_emision}-"
            f"{self.tipo_documento}-{self.numero_actual:08d}"
        )
        self.numero_actual += 1
        return numero_formateado


class DocumentoFiscal(models.Model):
    class Estado(models.TextChoices):
        EMITIDA = "EMITIDA", "Emitida"
        ANULADA = "ANULADA", "Anulada"

    venta = models.OneToOneField(
        "ventas.Venta", on_delete=models.PROTECT, related_name="documento_fiscal", verbose_name="venta"
    )
    rango = models.ForeignKey(
        RangoAutorizado, on_delete=models.PROTECT, related_name="documentos", verbose_name="rango autorizado"
    )
    numero_documento = models.CharField("número de documento", max_length=30, unique=True)
    tipo_documento = models.CharField(
        "tipo de documento", max_length=2, choices=RangoAutorizado.TipoDocumento.choices
    )
    rtn_receptor = models.CharField("RTN del receptor", max_length=14, blank=True)
    nombre_receptor = models.CharField("nombre del receptor", max_length=200, blank=True)
    subtotal = models.DecimalField("subtotal", max_digits=12, decimal_places=2)
    total_isv = models.DecimalField("ISV total", max_digits=12, decimal_places=2)
    total = models.DecimalField("total", max_digits=12, decimal_places=2)
    estado = models.CharField("estado", max_length=10, choices=Estado.choices, default=Estado.EMITIDA)
    codigo_verificacion = models.CharField(
        "código de verificación",
        max_length=100, blank=True,
        help_text="Código de verificación del proveedor de facturación electrónica (DTE), si aplica.",
    )
    fecha_emision = models.DateTimeField("fecha de emisión", auto_now_add=True)
    fecha_anulacion = models.DateTimeField("fecha de anulación", null=True, blank=True)

    class Meta:
        verbose_name = "Documento fiscal"
        verbose_name_plural = "Documentos fiscales"
        ordering = ["-fecha_emision"]

    def __str__(self):
        return self.numero_documento

    def anular(self):
        if self.estado == self.Estado.ANULADA:
            raise ValidationError("El documento ya está anulado.")
        self.estado = self.Estado.ANULADA
        self.fecha_anulacion = timezone.now()
        self.save()
