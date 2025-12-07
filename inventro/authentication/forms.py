from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

ROLE_CHOICES = [
    ("ADMIN", "Admin"),
    ("MANAGER", "Manager"),
    ("STAFF", "Staff"),
]

class AddUserForm(UserCreationForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username", "email", "role")
