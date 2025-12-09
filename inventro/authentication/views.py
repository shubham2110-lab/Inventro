from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages

from django.contrib.auth.decorators import login_required

from .forms import AddUserForm

def logout_view(request):
    """Log the user out and redirect to the login page.

    Accepts GET or POST so clicking a link will also log out.
    """

    logout(request)

    messages.info(request, "You have been signed out.")
    return redirect('login_page')


@login_required
def add_user(request):
    """
    Simple "Add User" page using Django's built-in User model.
    We also put the user into a Group named by the selected role.
    """
    if request.method == "POST":
        form = AddUserForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data.get("role")
            user = form.save()  # creates with username/email/password
            if role:
                grp, _ = Group.objects.get_or_create(name=role)
                user.groups.add(grp)

            messages.success(request, f"User '{user.username}' created.")
            return redirect("dashboard_home")
    else:
        form = AddUserForm()

    return render(request, "auth/add_user.html", {"form": form})