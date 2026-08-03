from django.db import models


class Cliente(models.Model):
    class Tipo(models.TextChoices):
        NATURAL = "NATURAL", "Persona natural"
        JURIDICO = "JURIDICO", "Persona jurídica"

    tipo = models.CharField("tipo de cliente", max_length=10, choices=Tipo.choices, default=Tipo.NATURAL)
    nombre = models.CharField("nombre", max_length=200, help_text="Nombre completo o razón social")
    rtn = models.CharField(
        "RTN",
        max_length=14, blank=True, db_index=True,
        help_text="Registro Tributario Nacional (13-14 dígitos). Vacío = consumidor final.",
    )
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    email = models.EmailField("correo electrónico", blank=True)
    direccion = models.CharField("dirección", max_length=255, blank=True)
    limite_credito = models.DecimalField("límite de crédito", max_digits=12, decimal_places=2, default=0)
    activo = models.BooleanField("activo", default=True)
    creado = models.DateTimeField("fecha de registro", auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.rtn or 'Consumidor final'})"
