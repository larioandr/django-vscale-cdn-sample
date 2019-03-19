from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect

from .models import Profile
from .forms import ProfileUpdateForm


@login_required
def profile_detail(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    return render(request, 'profiles/profile_detail.html', context={
        'profile': profile
    })


@login_required
def profile_update(request, pk):
    if request.user.pk == pk:
        profile = get_object_or_404(Profile, pk=pk)
        if request.method == 'POST':
            form = ProfileUpdateForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                return redirect('home')
        else:
            form = ProfileUpdateForm(instance=profile)
        return render(request, 'profiles/profile_update.html', context={
            'profile': profile,
            'form': form,
        })
    raise Http404
