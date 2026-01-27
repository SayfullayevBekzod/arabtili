from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio']

from .models import UserReminder
class ReminderUpdateForm(forms.ModelForm):
    class Meta:
        model = UserReminder
        fields = ['reminder_time', 'is_enabled', 'notes']
        widgets = {
            'reminder_time': forms.TimeInput(attrs={'type': 'time', 'class': 'bg-slate-900 border-white/10 rounded-xl text-white px-4 py-2 w-full'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'bg-slate-900 border-white/10 rounded-xl text-white px-4 py-2 w-full', 'placeholder': 'Eslatma yozing...'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-white/10 bg-slate-900 text-emerald-500 focus:ring-emerald-500'}),
        }
