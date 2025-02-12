from django.shortcuts import render

# Create your views here.
def render_accounts(request):
    return render(request,'accounts.html')
