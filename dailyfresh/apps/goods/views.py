from django.shortcuts import render, redirect
from django.http import HttpResponse
# Create your views here.


def index(request):
    """首页视图"""
    return render(request, 'index.html')
