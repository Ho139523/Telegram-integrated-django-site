from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


@login_required
def cv_view(request, username):
    context={}
    return render(request, 'cv/resume.html', context=context)
