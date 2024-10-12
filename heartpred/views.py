from django.shortcuts import render, redirect
from .form import heartpredform
from rest_framework.decorators import api_view
import joblib
import pandas as pd
import numpy as np
# from sklearn import preprocessing
# from sklearn.preprocessing import StandardScaler
from rest_framework import status
from rest_framework.response import Response



def heartpredformshow(request):
    form = heartpredform()
    prediction = request.session.get('prediction', None)
    
    if request.method == 'POST':
        form = heartpredform(request.POST)
        if form.is_valid():
            # Save the form data
            form.save()
            
            # Redirect to prediction view to process form data and get prediction
            return redirect('heartpred:prediction')  # This will handle the prediction logic
        else:
            print('Form is not valid')

    # Clear prediction after showing it
    if 'prediction' in request.session:
        del request.session['prediction']
    
    context = {'form': form, 'prediction': prediction}
    return render(request, 'heartpred/heartpredform.html', context=context)

    
    
# @api_view(["POST"])
def heartpred(request):
    try:
        model = joblib.load("utils/heart_failure_ann.pkl")
        data = request.POST  # Use POST to get the form data
        input_data = np.array(list(data.values())[1:13]).reshape(1, -1)
        input_col = list(data.keys())[1:13]
        
        # Load the scaler (ensure you're loading the correct file, this looks incorrect as it reloads the model)
        s_scaler = joblib.load("utils/scaler.pkl")
        
        # Apply the scaler on the input data
        input_scaled = s_scaler.transform(input_data)
        input_df = pd.DataFrame(input_scaled, columns=input_col)
        
        # Make prediction
        y_pred = model.predict(input_scaled)
        y_pred = (y_pred > 0.5)  # Assuming a threshold of 0.5
        
        # Map prediction to result
        result = "die" if y_pred else "stay alive"
        
        # Store the result in the session
        request.session['prediction'] = result
        
        # Redirect back to the form view
        return redirect('heartpred:heartpred')
    
    except Exception as e:
        print(f"Error occurred: {e}")
        return redirect('heartpred:heartpred')

        
