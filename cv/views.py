from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import User
from accounts.models import ProfileModel



def cv_view(request, username):
    profile=ProfileModel.objects.get(user__username=username)
    context={'profile': profile}
    return render(request, 'cv/resume.html', context=context)
