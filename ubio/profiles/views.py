import base64

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET

from .models import Profile, generate_avatar
from .forms import ProfileUpdateForm, AvatarDeleteForm


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


@login_required
@require_POST
def avatar_update(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    # Received base64 string starts with 'data:image/jpeg;base64,........'
    # We need to use 'jpeg' as an extension and everything after base64,
    # as the image itself:
    fmt, imgstr = request.POST['avatar'].split(';base64')
    print(fmt)
    print(imgstr)
    ext = fmt.split('/')[-1]
    if ext == 'svg+xml':
        ext = 'svg'
    img = ContentFile(base64.b64decode(imgstr), name=f'{profile.pk}.{ext}')
    if profile.avatar:
        profile.avatar.delete()
    profile.avatar = img
    profile.save()
    return redirect('profile-update', pk=profile.pk)


@login_required
@require_POST
def avatar_delete(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    form = AvatarDeleteForm(request.POST, instance=profile)
    form.save()
    return redirect('profile-update', pk=profile.pk)


@login_required
@require_GET
def profile_list(request):
    return render(request, 'profiles/profile_list.html', context={
        'profiles': Profile.objects.all()
    })
