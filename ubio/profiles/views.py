from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.

def profile_detail(request, pk):
    return HttpResponse(f'Profile #{pk} home page')
