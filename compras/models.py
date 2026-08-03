from django.core.exceptions import ValidationError
from django.db import models


class Proveedor(models.Model):
    nombre = models.CharField("nombre", max_length=200)
    rtn = models.CharField("RTN", max_length=14, blank=True)
    contacto = models.CharField("contacto", max_length=150, blank=True)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    email = models.EmailField("correo electrónico", blank=True)
    direccion = models.CharField("dirección", max_length=255, blank=True)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class OrdenCompra(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        RECIBIDA = "RECIBIDA", "Recibida"
        CANCELADA = "CANCELADA", "Cancelada"

    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, related_name="ordenes_compra", verbose_name="proveedor"
    )
    sucursal = models.ForeignKey(
        "sucursales.Sucursal", on_delete=models.PROTECT, related_name="ordenes_compra", verbose_name="sucursal"
    )
    estado = models.CharField("estado", max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
    usuario = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.SET_NULL, null=True, verbose_name="usuario"
    )
    fecha = models.DateTimeField("fecha", auto_now_add=True)
    fecha_recepcion = models.DateTimeField("fecha de recepción", null=True, blank=True)
    notas = models.TextField("notas", blank=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Orden de compra"
        verbose_name_plural = "Órdenes de compra"

    def __str__(self):
        return f"OC-{self.pk} · {self.proveedor}"

    @property
    def total(self):
        return sum((d.subtotal for d in self.detalles.all()), start=0)

    def recibir(self, usuario=None):
        """Marca la orden como recibida e incrementa el stock de la sucursal."""
        from django.utils import timezone

        from inventario.models import MovimientoInventario, Stock

        if self.estado != self.Estado.PENDIENTE:
            raise ValidationError("Solo se pueden recibir órdenes pendientes.")

        for detalle in self.detalles.select_related("producto"):
            stock, _ = Stock.objects.get_or_create(producto=detalle.producto, sucursal=self.sucursal)
            stock.cantidad += detalle.cantidad
            stock.save()
            MovimientoInventario.objects.create(
                producto=detalle.producto, sucursal=self.sucursal,
                tipo=MovimientoInventario.Tipo.ENTRADA, cantidad=detalle.cantidad,
                referencia=f"Orden de compra #{self.pk}", usuario=usuario or self.usuario,
            )

        self.estado = self.Estado.RECIBIDA
        self.fecha_recepcion = timezone.now()
        self.save()


class DetalleOrdenCompra(models.Model):
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name="detalles", verbose_name="orden")
    producto = models.ForeignKey("inventario.Producto", on_delete=models.PROTECT, verbose_name="producto")
    cantidad = models.DecimalField("cantidad", max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField("precio unitario", max_digits=12, decimal_places=4)

    class Meta:
        verbose_name = "Detalle de orden de compra"
        verbose_name_plural = "Detalles de orden de compra"

    def __str__(self):
        return f"{self.producto.codigo} x {self.cantidad}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
