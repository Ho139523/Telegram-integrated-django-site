from django.db import models

class heart(models.Model):
    age = models.FloatField()
    anaemia = models.IntegerField()
    creatinine_phosphokinase = models.IntegerField()
    diabetes =  models.IntegerField()
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
        return str(self.created)
    

from django.db import models

class Person(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    
    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='books')
    published_year = models.IntegerField()
    
    def __str__(self):
        return self.title