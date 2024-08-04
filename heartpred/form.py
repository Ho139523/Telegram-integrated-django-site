from django import forms
from .models import *

class heartpredform(forms.ModelForm):
    class Meta:
        model=heart
        fields='__all__'
        widgets={
            
        'created':forms.NumberInput(attrs={class:'form-control'}),
        'age':forms.NumberInput(attrs={class:'form-control'}),
        'anaemia':forms.NumberInput(attrs={class:'form-control'}),
        'creatinine_phosphokinase':forms.NumberInput(attrs={class:'form-control'}),
        'ejection_fraction':forms.NumberInput(attrs={class:'form-control'}),
        'high_blood_pressure':forms.NumberInput(attrs={class:'form-control'}),
        'platelets':forms.NumberInput(attrs={class:'form-control'}),
        'serum_creatinine':forms.NumberInput(attrs={class:'form-control'}),
        'serum_sodium':forms.NumberInput(attrs={class:'form-control'}),
        'sex':forms.NumberInput(attrs={class:'form-control'}),
        'smoking':forms.NumberInput(attrs={class:'form-control'}),
        'time':forms.NumberInput(attrs={class:'form-control'}),
        'DEATH_EVENT':forms.NumberInput(attrs={class:'form-control'}),
        }
        
    class Media:
        css={'all': ('cv/assets/css/main.css',)}