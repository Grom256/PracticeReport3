from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile

User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label='Електронна пошта')
    first_name = forms.CharField(label="Ім’я", max_length=150, required=True)
    last_name = forms.CharField(label='Прізвище', max_length=150, required=True)

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
    first_name = forms.CharField(label="Ім’я", max_length=150, required=True)
    last_name = forms.CharField(label='Прізвище', max_length=150, required=True)
    email = forms.EmailField(label='Електронна пошта', required=True)

    class Meta:
        model = Profile
        fields = ('phone', 'avatar', 'date_of_birth', 'telegram_chat_id')
        labels = {
            'phone': 'Телефон',
            'avatar': 'Аватар',
            'date_of_birth': 'Дата народження',
            'telegram_chat_id': 'Telegram Chat ID (для сповіщень)',
        }
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'telegram_chat_id': forms.TextInput(attrs={'placeholder': 'Наприклад: 123456789 або натисніть /start у боті'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.user
        if not self.is_bound:
            self.initial.setdefault('first_name', user.first_name)
            self.initial.setdefault('last_name', user.last_name)
            self.initial.setdefault('email', user.email)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.user_id).exists():
            raise forms.ValidationError('Ця електронна пошта вже використовується.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if commit:
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save(update_fields=('first_name', 'last_name', 'email'))
        return profile


class EmailVerificationForm(forms.Form):
    code = forms.CharField(
        label='Код підтвердження з листа',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                'placeholder': '123456',
                'autocomplete': 'one-time-code',
                'pattern': '[0-9]{6}',
                'maxlength': '6',
                'autofocus': True,
            }
        ),
    )

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError('Код має складатися рівно з 6 цифр.')
        return code
