from django.db import models


class Cliente(models.Model):
    class Tipo(models.TextChoices):
        NATURAL = "NATURAL", "Persona natural"
        JURIDICO = "JURIDICO", "Persona jurídica"

    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.NATURAL)
    nombre = models.CharField(max_length=200, help_text="Nombre completo o razón social")
    rtn = models.CharField(
        max_length=14, blank=True, db_index=True,
        help_text="Registro Tributario Nacional (13-14 dígitos). Vacío = consumidor final.",
    )
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.rtn or 'Consumidor final'})"
