from django.db import models

class heart(models.Model):
    age = models.FloatField()
    anaemia = models.IntegerField()
    creatinine_phosphokinase = models.IntegerField()
    ejection_fraction = models.IntegerField()
    high_blood_pressure = models.IntegerField()
    platelets = models.FloatField()
    serum_creatinine = models.FloatField()
    serum_sodium = models.IntegerField()
    sex = models.IntegerField()
    smoking = models.IntegerField()
    time = models.IntegerField()
    DEATH_EVENT = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.ceated