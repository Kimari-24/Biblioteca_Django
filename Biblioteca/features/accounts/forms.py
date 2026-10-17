from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(label='Correo')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)


class RegisterForm(forms.Form):
    name = forms.CharField(label='Nombre', max_length=80)
    email = forms.EmailField(label='Correo')
    password = forms.CharField(label='Contraseña', min_length=6, widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repite la contraseña', widget=forms.PasswordInput)

    def clean(self):
        data = super().clean()
        if data.get('password') and data.get('password') != data.get('password2'):
            self.add_error('password2', 'Las contraseñas no coinciden.')
        return data
