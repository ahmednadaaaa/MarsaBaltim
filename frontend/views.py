from django.shortcuts import render

def index(request):
    """يخدم صفحة الـ frontend الرئيسية"""
    return render(request, 'frontend/index.html')
