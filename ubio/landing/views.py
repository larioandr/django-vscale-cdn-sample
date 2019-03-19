from django.shortcuts import render, redirect


# Create your views here.
def landing_view(request):
    if request.user.is_authenticated:
        return redirect('user-home')
    return render(request, 'landing/index.html')
