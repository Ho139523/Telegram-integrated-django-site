from django.shortcuts import render

def cv_view(request):
    context={}
    return render(request, 'cv/resume.html', context=context)
