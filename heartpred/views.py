from django.shortcuts import render, redirect
from .form import heartpredform
import joblib
import pandas as pd
import numpy as np
from django.conf import settings

def heartpredformshow(request):
    form = heartpredform()
    prediction = request.session.get('prediction', None)

    if request.method == 'POST':
        form = heartpredform(request.POST)
        if form.is_valid():
            # Save form data or handle it as needed, not necessarily saving in DB
            return redirect('heartpred:prediction')  # Redirect to prediction logic
        else:
            print('Form is not valid')

    # Clear prediction from session after it is shown
    if 'prediction' in request.session:
        del request.session['prediction']

    context = {'form': form, 'prediction': prediction}
    return render(request, 'heartpred/heartpredform.html', context=context)

def heartpred(request):
    try:
        # Load the trained model and scaler
        model = joblib.load(settings.BASE_DIR / "utils/heart_failure_ann.pkl")
        s_scaler = joblib.load(settings.BASE_DIR / "utils/scaler.pkl")
        
        # Collect form data
        form_data = request.POST
        print(form_data)
        
        # Define the feature names in the order your model expects
        feature_names = ['age', 'anaemia', 'creatinine_phosphokinase', 'diabetes',
                         'ejection_fraction', 'high_blood_pressure', 'platelets',
                         'serum_creatinine', 'serum_sodium', 'sex', 'smoking', 'time']
        
        input_data = []
        
        for feature in feature_names:
            value = form_data.get(feature)
            
            # Handle missing or None values
            if value is None or value == "":
                # Either set a default value or raise an error
                print(f"Missing value for feature: {feature}")
                return redirect('heartpred:heartpred')  # Redirect or show error message if needed
            
            # Convert to float
            input_data.append(float(value))
        
        # Reshape the input data into 2D array
        input_data = np.array(input_data).reshape(1, -1)
        
        # Scale the input data
        input_scaled = s_scaler.transform(input_data)
        
        # Make prediction with the ANN model
        y_pred = model.predict(input_scaled)
        y_pred = (y_pred > 0.5)  # Apply threshold for binary classification
        
        # Interpret the result
        result = "die" if y_pred else "stay alive"
        
        # Store the result in the session
        request.session['prediction'] = result
        
        # Redirect back to the form
        return redirect('heartpred:heartpred')
    
    except Exception as e:
        print(f"Error occurred: {e}")
        return redirect('heartpred:heartpred')
