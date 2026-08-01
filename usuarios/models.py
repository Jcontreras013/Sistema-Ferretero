from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        GERENTE = "GERENTE", "Gerente de sucursal"
        VENDEDOR = "VENDEDOR", "Vendedor / Cajero"
        BODEGUERO = "BODEGUERO", "Bodeguero"
        CONTADOR = "CONTADOR", "Contador"

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.VENDEDOR)
    sucursal = models.ForeignKey(
        "sucursales.Sucursal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
        help_text="Sucursal a la que pertenece el usuario. Vacío para administradores globales.",
    )
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN or self.is_superuser
