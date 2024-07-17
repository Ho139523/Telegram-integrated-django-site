from django.shortcuts import render
from utils import graph

def home(request):
    context={'y': graph.plotting()}
    return render(request, 'carpred/index.html', context=context)
