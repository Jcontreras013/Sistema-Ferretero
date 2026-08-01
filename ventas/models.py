from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction


class Venta(models.Model):
    class FormaPago(models.TextChoices):
        CONTADO = "CONTADO", "Contado"
        CREDITO = "CREDITO", "Crédito"
        TARJETA = "TARJETA", "Tarjeta"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia bancaria"

    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        COMPLETADA = "COMPLETADA", "Completada"
        ANULADA = "ANULADA", "Anulada"

    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.PROTECT, null=True, blank=True, related_name="ventas",
        help_text="Vacío = consumidor final",
    )
    sucursal = models.ForeignKey("sucursales.Sucursal", on_delete=models.PROTECT, related_name="ventas")
    vendedor = models.ForeignKey("usuarios.Usuario", on_delete=models.PROTECT, related_name="ventas")
    forma_pago = models.CharField(max_length=15, choices=FormaPago.choices, default=FormaPago.CONTADO)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.BORRADOR)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_isv = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_anulacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Venta #{self.pk} - {self.sucursal.codigo}"

    def recalcular_totales(self, commit=False):
        subtotal = Decimal("0")
        total_isv = Decimal("0")
        for detalle in self.detalles.all():
            base = detalle.subtotal
            isv_linea = base * (detalle.porcentaje_isv / Decimal("100"))
            subtotal += base
            total_isv += isv_linea

        self.subtotal = subtotal
        self.total_isv = total_isv
        self.total = subtotal + total_isv - self.descuento
        if commit:
            self.save(update_fields=["subtotal", "total_isv", "total"])
        return self.total

    @transaction.atomic
    def confirmar(self, usuario=None, rtn_receptor="", nombre_receptor=""):
        """
        Confirma la venta: valida y descuenta stock, calcula totales y emite
        el DocumentoFiscal correspondiente usando el CAI vigente de la sucursal.
        """
        from facturacion.models import RangoAutorizado
        from facturacion.services import emitir_documento_fiscal
        from inventario.models import MovimientoInventario, Stock

        if self.estado != self.Estado.BORRADOR:
            raise ValidationError("Solo se pueden confirmar ventas en borrador.")

        detalles = list(self.detalles.select_related("producto"))
        if not detalles:
            raise ValidationError("La venta no tiene productos.")

        for detalle in detalles:
            stock = Stock.objects.filter(producto=detalle.producto, sucursal=self.sucursal).first()
            disponible = stock.cantidad if stock else Decimal("0")
            if disponible < detalle.cantidad:
                raise ValidationError(
                    f"Stock insuficiente de {detalle.producto.codigo} en {self.sucursal.codigo} "
                    f"(disponible: {disponible}, requerido: {detalle.cantidad})."
                )

        rango = (
            RangoAutorizado.objects.filter(
                sucursal=self.sucursal, tipo_documento=RangoAutorizado.TipoDocumento.FACTURA, activo=True
            )
            .order_by("id")
            .first()
        )
        if not rango or not rango.correlativo_disponible():
            raise ValidationError(
                f"No hay un CAI vigente con correlativos disponibles para la sucursal {self.sucursal.codigo}."
            )

        for detalle in detalles:
            stock = Stock.objects.get(producto=detalle.producto, sucursal=self.sucursal)
            stock.cantidad -= detalle.cantidad
            stock.save()
            MovimientoInventario.objects.create(
                producto=detalle.producto, sucursal=self.sucursal,
                tipo=MovimientoInventario.Tipo.SALIDA, cantidad=detalle.cantidad,
                referencia=f"Venta #{self.pk}", usuario=usuario or self.vendedor,
            )

        self.recalcular_totales()
        self.estado = self.Estado.COMPLETADA
        self.save()

        nombre_receptor = nombre_receptor or (self.cliente.nombre if self.cliente else "Consumidor final")
        rtn_receptor = rtn_receptor or (self.cliente.rtn if self.cliente else "")
        emitir_documento_fiscal(self, rango, rtn_receptor=rtn_receptor, nombre_receptor=nombre_receptor)
        return self

    def anular(self):
        from django.utils import timezone

        from inventario.models import MovimientoInventario, Stock

        if self.estado != self.Estado.COMPLETADA:
            raise ValidationError("Solo se pueden anular ventas completadas.")

        if hasattr(self, "documento_fiscal"):
            self.documento_fiscal.anular()

        for detalle in self.detalles.select_related("producto"):
            stock, _ = Stock.objects.get_or_create(producto=detalle.producto, sucursal=self.sucursal)
            stock.cantidad += detalle.cantidad
            stock.save()
            MovimientoInventario.objects.create(
                producto=detalle.producto, sucursal=self.sucursal,
                tipo=MovimientoInventario.Tipo.AJUSTE_POSITIVO, cantidad=detalle.cantidad,
                referencia=f"Anulación venta #{self.pk}", usuario=self.vendedor,
            )

        self.estado = self.Estado.ANULADA
        self.fecha_anulacion = timezone.now()
        self.save()


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey("inventario.Producto", on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True,
        help_text="Se autocompleta con el precio de venta del producto si se deja en 0.",
    )
    porcentaje_isv = models.DecimalField(max_digits=5, decimal_places=2, blank=True)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Detalle de venta"
        verbose_name_plural = "Detalles de venta"

    def __str__(self):
        return f"{self.producto.codigo} x {self.cantidad}"

    def save(self, *args, **kwargs):
        if not self.precio_unitario:
            self.precio_unitario = self.producto.precio_venta
        if self.porcentaje_isv is None:
            self.porcentaje_isv = self.producto.porcentaje_isv
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return (self.cantidad * self.precio_unitario) - self.descuento


class CierreCaja(models.Model):
    class Estado(models.TextChoices):
        ABIERTA = "ABIERTA", "Abierta"
        CERRADA = "CERRADA", "Cerrada"

    sucursal = models.ForeignKey("sucursales.Sucursal", on_delete=models.PROTECT, related_name="cierres_caja")
    usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.PROTECT, related_name="cierres_caja")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ABIERTA)
    monto_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_final = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha_apertura"]
        verbose_name = "Cierre de caja"
        verbose_name_plural = "Cierres de caja"

    def __str__(self):
        return f"Caja {self.sucursal.codigo} - {self.fecha_apertura:%d/%m/%Y}"

    def total_ventas(self):
        from django.utils import timezone

        return (
            Venta.objects.filter(
                sucursal=self.sucursal, estado=Venta.Estado.COMPLETADA,
                fecha__gte=self.fecha_apertura,
                fecha__lte=self.fecha_cierre or timezone.now(),
            ).aggregate(total=models.Sum("total"))["total"]
            or 0
        )

    def cerrar(self, monto_final):
        from django.utils import timezone

        if self.estado != self.Estado.ABIERTA:
            raise ValidationError("La caja ya está cerrada.")
        self.monto_final = monto_final
        self.fecha_cierre = timezone.now()
        self.estado = self.Estado.CERRADA
        self.save()
