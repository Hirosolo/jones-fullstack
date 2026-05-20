from django.shortcuts import render
from django.http import HttpResponse


def home_view(request, **kwargs):
    """
    Trang chủ của ACP Client Web
    """
    return render(request, 'home.html')


def fake_view(request, **kwargs):
    """
    View giả lập
    """
    return HttpResponse('OK')
