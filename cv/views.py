from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def cv_view(request):
    context={}
    return render(request, 'cv/resume.html', context=context)
