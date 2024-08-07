from django.shortcuts import render
from .form import heartpredform


def heartpred(request):
    form = heartpredform()
    if request.method=='POST':
        form = heartpredform(request.POST)
        if form.is_valid():
            form.save()
        else:
            form = heartpredform()
    context={'form': form}
    return render(request, 'heartpred/heartpredform.html', context=context)
