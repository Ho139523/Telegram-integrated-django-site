from django.shortcuts import render
from .form import heartpredform
from rest_framework.decorators import api_view
import joblib
import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from rest_framework import status
from rest_framework.response import Response



def heartpredformshow(request):
    form = heartpredform()
    if request.method=='POST':
        form = heartpredform(request.POST)
        if form.is_valid():
            form.save()
        else:
            form = heartpredform()
    context={'form': form, "prediction": ''}
    return render(request, 'heartpred/heartpredform.html', context=context)
    
    
@api_view(["POST"])
def heartpred(request):
    # try:
    model = joblib.load("utils/heart_failure_ann.pkl")
    data = request
    input_data = np.array(list(data.values())[1:13]).reshape(1,-1)
    input_col = list(data.keys())[1:13]
    s_scaler = joblib.load("utils/heart_failure_ann.pkl")
    input_scaled= s_scaler.fit_transform(input_data)
    input=pd.DataFrame(input_scaled, columns=input_col)
    y_pred = model.predict(input_scaled)
    y_pred = (y_pred>58)
    y_df = pd.DataFrame(y_pred, columns=["Death_event"])
    y_df = y_df.replace({1: "die", 0: "stay alive"})
    print(y_df)
    return redirect("heartpred/heartpredform.html", prediction=y_df)
    # except ValueError as e:
        # return Response(e.args[0], status.HTTP_400_BAD_REQUEST)
        
        
