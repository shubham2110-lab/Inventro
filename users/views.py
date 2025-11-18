from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render

from .forms import AddUserForm


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
            return redirect("dashboard")
    else:
        form = AddUserForm()

    return render(request, "users/add_user.html", {"form": form})
