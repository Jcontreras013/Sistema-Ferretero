from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class UnidadMedida(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    abreviatura = models.CharField(max_length=10, unique=True)

    class Meta:
        verbose_name = "Unidad de medida"
        verbose_name_plural = "Unidades de medida"

    def __str__(self):
        return self.abreviatura


class Producto(models.Model):
    ISV_GENERAL = Decimal("15.00")
    ISV_EXENTO = Decimal("0.00")

    codigo = models.CharField(max_length=30, unique=True, help_text="SKU interno")
    codigo_barras = models.CharField(max_length=50, blank=True, db_index=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    marca = models.CharField(max_length=100, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos")
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.PROTECT, related_name="productos")
    precio_compra = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=4)
    porcentaje_isv = models.DecimalField(
        max_digits=5, decimal_places=2, default=ISV_GENERAL,
        help_text="ISV Honduras: 15% general, 18% bebidas/tabaco, 0% exento",
    )
    stock_minimo = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    proveedor_principal = models.ForeignKey(
        "compras.Proveedor", on_delete=models.SET_NULL, null=True, blank=True, related_name="productos"
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def stock_total(self):
        return self.stocks.aggregate(total=models.Sum("cantidad"))["total"] or 0

    def stock_en(self, sucursal):
        stock = self.stocks.filter(sucursal=sucursal).first()
        return stock.cantidad if stock else 0


class Stock(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="stocks")
    sucursal = models.ForeignKey("sucursales.Sucursal", on_delete=models.CASCADE, related_name="stocks")
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("producto", "sucursal")
        verbose_name_plural = "Stock"

    def __str__(self):
        return f"{self.producto.codigo} @ {self.sucursal.codigo}: {self.cantidad}"

    def hay_stock_bajo(self):
        return self.cantidad <= self.producto.stock_minimo


class MovimientoInventario(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada (compra)"
        SALIDA = "SALIDA", "Salida (venta)"
        AJUSTE_POSITIVO = "AJUSTE_POS", "Ajuste positivo"
        AJUSTE_NEGATIVO = "AJUSTE_NEG", "Ajuste negativo"
        TRANSFERENCIA_SALIDA = "TRANS_OUT", "Transferencia - salida"
        TRANSFERENCIA_ENTRADA = "TRANS_IN", "Transferencia - entrada"

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="movimientos")
    sucursal = models.ForeignKey("sucursales.Sucursal", on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.CharField(max_length=255, blank=True)
    referencia = models.CharField(
        max_length=100, blank=True, help_text="Ej: Venta #123, Orden de compra #45"
    )
    usuario = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.SET_NULL, null=True, related_name="movimientos_inventario"
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.codigo} ({self.cantidad})"


class TransferenciaInventario(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        COMPLETADA = "COMPLETADA", "Completada"
        CANCELADA = "CANCELADA", "Cancelada"

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="transferencias")
    sucursal_origen = models.ForeignKey(
        "sucursales.Sucursal", on_delete=models.PROTECT, related_name="transferencias_salientes"
    )
    sucursal_destino = models.ForeignKey(
        "sucursales.Sucursal", on_delete=models.PROTECT, related_name="transferencias_entrantes"
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
    usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.SET_NULL, null=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_completada = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha_solicitud"]

    def __str__(self):
        return f"{self.producto.codigo}: {self.sucursal_origen} -> {self.sucursal_destino}"

    def clean(self):
        if self.sucursal_origen_id and self.sucursal_destino_id and self.sucursal_origen_id == self.sucursal_destino_id:
            raise ValidationError("La sucursal de origen y destino no pueden ser la misma.")

    def completar(self, usuario=None):
        """Mueve el stock de la sucursal origen a la destino y registra los movimientos."""
        from django.utils import timezone

        if self.estado != self.Estado.PENDIENTE:
            raise ValidationError("Solo se pueden completar transferencias pendientes.")

        origen_stock, _ = Stock.objects.get_or_create(producto=self.producto, sucursal=self.sucursal_origen)
        if origen_stock.cantidad < self.cantidad:
            raise ValidationError("Stock insuficiente en la sucursal de origen para esta transferencia.")

        destino_stock, _ = Stock.objects.get_or_create(producto=self.producto, sucursal=self.sucursal_destino)

        origen_stock.cantidad -= self.cantidad
        origen_stock.save()
        destino_stock.cantidad += self.cantidad
        destino_stock.save()

        MovimientoInventario.objects.create(
            producto=self.producto, sucursal=self.sucursal_origen,
            tipo=MovimientoInventario.Tipo.TRANSFERENCIA_SALIDA, cantidad=self.cantidad,
            referencia=f"Transferencia #{self.pk}", usuario=usuario or self.usuario,
        )
        MovimientoInventario.objects.create(
            producto=self.producto, sucursal=self.sucursal_destino,
            tipo=MovimientoInventario.Tipo.TRANSFERENCIA_ENTRADA, cantidad=self.cantidad,
            referencia=f"Transferencia #{self.pk}", usuario=usuario or self.usuario,
        )

        self.estado = self.Estado.COMPLETADA
        self.fecha_completada = timezone.now()
        self.save()
