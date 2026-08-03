from django.contrib.auth.forms import AuthenticationForm
from django.forms import PasswordInput, TextInput


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget = TextInput(
            attrs={"class": "form-control", "placeholder": "Usuario", "autofocus": True}
        )
        self.fields["password"].widget = PasswordInput(
            attrs={"class": "form-control", "placeholder": "Contraseña"}
        )
