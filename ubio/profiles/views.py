from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect

from .models import Profile, generate_avatar
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


@login_required
def profile_setup(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Since first_name and last_name are known now, generate
            # the avatar:
            profile.avatar = generate_avatar(profile)
            profile.save()
            return redirect('home')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'profiles/profile_setup.html', context={
        'profile': request.user.profile,
        'form': form,
    })
