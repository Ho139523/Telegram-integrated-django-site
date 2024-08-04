from django.shortcuts import render
from .form import heartpredform


def heartpred(request):
    form = heartpredform()
    context={'form': form}
    return render(request, 'heartpred/heartpredform.html', context=context)
