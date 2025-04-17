from django import forms
from .models import *

class heartpredform(forms.ModelForm):
    class Meta:
        model=heart
        fields='__all__'
        widgets={
            
        'created':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'age': forms.NumberInput(attrs={'class': 'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'anaemia':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'creatinine_phosphokinase':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'diabetes':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top: 5px; margin-bottom: 10px;'}),
        'ejection_fraction':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'high_blood_pressure':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'platelets':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'serum_creatinine':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'serum_sodium':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'sex':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'smoking':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'time':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        'DEATH_EVENT':forms.NumberInput(attrs={'class':'form-control', 'style': 'margin-top:5px; margin-bottom: 10px;'}),
        }
    
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is None:
            raise forms.ValidationError("Age is required.")
        return age
    
    
    class Media:
        css={'all': ('cv/form/css/formcss.css',)}