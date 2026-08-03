from django.db import models


class Sucursal(models.Model):
    codigo = models.CharField(
        "código",
        max_length=3,
        unique=True,
        help_text="Código de establecimiento asignado por SAR, 3 dígitos. Ej: 001",
    )
    nombre = models.CharField("nombre", max_length=150)
    direccion = models.CharField("dirección", max_length=255, blank=True)
    ciudad = models.CharField("ciudad", max_length=100, blank=True)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    es_matriz = models.BooleanField("es matriz", default=False)
    activa = models.BooleanField("activa", default=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
