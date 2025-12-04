from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages

def logout_view(request):
    """Log the user out and redirect to the login page.

    Accepts GET or POST so clicking a link will also log out.
    """

    logout(request)

    messages.info(request, "You have been signed out.")
    return redirect('login_page')