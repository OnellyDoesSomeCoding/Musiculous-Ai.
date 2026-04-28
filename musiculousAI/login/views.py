from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import SignUpForm


def home_view(request):
    return render(request, "login/home.html")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("library_home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect("library_home")
    else:
        form = SignUpForm()

    return render(request, "login/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("library_home")

    error_message = ""

    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")

        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user_obj = user_model.objects.filter(email__iexact=identifier).first()
        username = user_obj.username if user_obj else identifier

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("library_home")

        error_message = "Invalid credentials. Please try again."

    return render(request, "login/login.html", {"error_message": error_message})


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")

    return render(request, "login/logout.html")
