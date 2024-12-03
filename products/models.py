from django.db import models
from accounts.models import User


class CategoryModel(models.Model):
    title = models.CharField(max_length=50, unique=True, verbose_name='Title')
    slug = models.SlugField(unique=True)  # Ensure the slug is unique
    status = models.BooleanField(default=True, verbose_name='Publish Status') 
    position = models.IntegerField(verbose_name='Position')

    def __str__(self):
        return self.title
        
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["position"]


class TutorialModel(models.Model):
    title = models.CharField(max_length=50, unique=True, blank=False, null=False, verbose_name='Title')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')  # Price field for tutorial
    video = models.FileField(upload_to='tutorial_videos/', verbose_name='Video')  # Upload location for videos
    video_poster = models.ImageField(upload_to='tutorial_posters/', verbose_name='Video Poster')  # Video poster image
    poster = models.ImageField(upload_to='tutorial_poster/', verbose_name='Tutorial Poster')  # Poster image
    about = models.TextField(max_length=5000, blank=False, null=False, verbose_name='Description')
    tag = models.ForeignKey(CategoryModel, on_delete=models.SET_NULL, null=True, verbose_name='Tag')  # ForeignKey to Tag model
    status = models.BooleanField(default=False, verbose_name='Publish Status')
    slug = models.SlugField(unique=True)  # Ensure the slug is unique
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tutorials_authored', verbose_name='Author')  # Tutorial author
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tutorials_taught', verbose_name='Teacher')  # Tutorial teacher
    attachment = models.FileField(upload_to='tutorial_attachments/', blank=True, null=True, verbose_name='Attachments')  # Optional attachment
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date of creation")
    installment = models.BooleanField(default=False, verbose_name='Installment Purchase')

    def __str__(self):
        return self.title
        
    class Meta:
        verbose_name = "Tutorial"
        verbose_name_plural = "Toturials"
        ordering = ["created"]
        
        
        
class ArticleModel(models.Model):
    title = models.CharField(max_length=50, unique=True, blank=False, null=False, verbose_name='Title')
    poster = models.ImageField(upload_to='article_poster/', verbose_name='Artilce Poster')  # Poster image
    context = models.TextField(max_length=5000, blank=False, null=False, verbose_name='Description')
    tag = models.ForeignKey(CategoryModel, on_delete=models.SET_NULL, null=True, verbose_name='Tag')  # ForeignKey to Tag model
    status = models.BooleanField(default=False, verbose_name='Publish Status')
    slug = models.SlugField(unique=True)  # Ensure the slug is unique
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='article_authored', verbose_name='Author')  # Tutorial author
    attachment = models.FileField(upload_to='tutorial_attachments/', blank=True, null=True, verbose_name='Attachments')  # Optional attachment
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date of creation")
    time_takes = models.IntegerField(verbose_name='Time it takes to read it')

    def __str__(self):
        return self.title
        
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["created"]
    
    @property
    def required_time(self):
        hour = self.time_takes//60
        min =  self.time_takes-hour
        return [hour, min]



class ShoeModel(models.Model):
    title = models.CharField(max_length=100, unique=True, blank=False, null=False)
    description = models.TextField(max_length=1000, unique=False, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.IntegerField()
    length = models.DecimalField(max_digits=3, decimal_places=1)
    stock = models.BooleanField(default=True)
    pic1 = models.ImageField(upload_to='shoes_image')
    pic2 = models.ImageField(upload_to='shoes_image')
    pic3 = models.ImageField(upload_to='shoes_image')
    pic4 = models.ImageField(upload_to='shoes_image')
    
    
    def __str__(self):
        return self.title + str(self.price)