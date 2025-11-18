from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .forms import AddUserForm

def _is_admin(user):
    return user.is_superuser

@user_passes_test(_is_admin)
def add_user(request):
    if request.method == "POST":
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data.get("role")

            # Map roles to Django flags
            if role == "ADMIN":
                user.is_superuser = True
                user.is_staff = True
            elif role == "MANAGER":
                user.is_superuser = False
                user.is_staff = True
            else:
                user.is_superuser = False
                user.is_staff = False

            user.save()
            messages.success(request, f"User '{user.username}' created.")
            return redirect("dashboard_home")
    else:
        form = AddUserForm()
    return render(request, "users/add_user.html", {"form": form})
