from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

# Create your views here.

@ensure_csrf_cookie
def index(request):
    return render(request, 'core/index.html')

def contact(request):
    return render(request,'core/contact.html' )
