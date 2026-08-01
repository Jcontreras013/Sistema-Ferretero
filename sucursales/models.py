from django.db import models


class Sucursal(models.Model):
    codigo = models.CharField(
        max_length=3,
        unique=True,
        help_text="Código de establecimiento asignado por SAR, 3 dígitos. Ej: 001",
    )
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    es_matriz = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
