from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_GET

from .forms import DeleteUserForm, UpdateUserForm


@login_required
def user_delete(request):
    if request.method == 'POST':
        form = DeleteUserForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = DeleteUserForm(request.user)

    return render(request, 'users/user_delete.html', {'form': form})


@login_required
def user_update(request):
    if request.method == 'POST':
        form = UpdateUserForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('user-home')
    else:
        form = UpdateUserForm(
            request.user,
            initial={'email': request.user.email}
        )
    return render(request, 'users/user_update.html', {'form': form})


@require_GET
@login_required
def user_home(request):
    return redirect('profile-detail', pk=request.user.pk)
