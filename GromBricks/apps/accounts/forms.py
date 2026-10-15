from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label='Електронна пошта')
    first_name = forms.CharField(label="Ім’я", max_length=150, required=False)
    last_name = forms.CharField(label='Прізвище', max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {'username': 'Логін'}

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Користувач із такою поштою вже зареєстрований.')
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Логін')
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput,
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': "Ім’я",
            'last_name': 'Прізвище',
            'email': 'Електронна пошта',
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ця електронна пошта вже використовується.')
        return email
