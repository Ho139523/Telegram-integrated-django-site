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




#class ShoeModel(models.Model):
#    title = models.CharField(max_length=100, unique=True, blank=False, null=False)
#    description = models.TextField(max_length=1000, unique=False, blank=True, null=True)
#    price = models.DecimalField(max_digits=10, decimal_places=2)  # Preliminary price
#    size = models.IntegerField()
#    length = models.DecimalField(max_digits=3, decimal_places=1)
#    stock = models.BooleanField(default=True)
#    pic1 = models.ImageField(upload_to='shoes_image')
#    pic2 = models.ImageField(upload_to='shoes_image')
#    pic3 = models.ImageField(upload_to='shoes_image')
#    pic4 = models.ImageField(upload_to='shoes_image')
#
#

#    def __str__(self):
#

#    @property
#    def final_price(self):
#        """Calculate the price after applying the discount percentage."""
#        discount_amount = (self.price * self.off) / 100
#


class Category(models.Model):
    title = models.CharField(max_length=50, unique=True, verbose_name='Category Title')
    slug = models.SlugField(unique=True, verbose_name='Slug')
    status = models.BooleanField(default=True, verbose_name='Publish Status')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories',
        verbose_name='Parent Category'
    )
    position = models.IntegerField(verbose_name='Position')
    stores = models.ManyToManyField('Store', blank=True, related_name='categories', verbose_name='Stores')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["position"]

    # Recursive method to get full hierarchy of parents
    def get_parents(self):
        parents = []
        category = self
        while category.parent:
            parents.append(category.parent)
            category = category.parent
        return parents
        
    def get_full_path(self):
    	return " > ".join([parent.title for parent in reversed(self.get_parents())] + [self.title])

	def get_all_subcategories(self):
		subcategories = set()
		categories_to_check = [self]
		
		while categories_to_check:
		current = categories_to_check.pop()
		children = current.subcategories.all()
		subcategories.update(children)
		categories_to_check.extend(children)
		
		return subcategories

class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Product Name')
    slug = models.SlugField(unique=True, verbose_name='Slug')
    brand = models.CharField(max_length=50, blank=True, null=True, verbose_name='Brand')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')
    stock = models.PositiveIntegerField(default=0, verbose_name='Stock')
    is_available = models.BooleanField(default=True, verbose_name='Is Available')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name='Category'
    )
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    main_image = models.ImageField(upload_to='product_images/', blank=True, null=True, verbose_name='Main Image')  # تغییر نام از images
    additional_images = models.ManyToManyField('ProductImage', blank=True, related_name='product_images')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"


class ProductImage(models.Model):
    image = models.ImageField(upload_to='product_images/', verbose_name='Product Image')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='image_set', verbose_name='Product')  # تغییر related_name

    def __str__(self):
        return f"Image: {self.id}"
        
        
        
class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    key = models.CharField(max_length=50, verbose_name='Attribute Key')  # مثل "Weight" یا "Size"
    value = models.CharField(max_length=100, verbose_name='Attribute Value')  # مثل "1kg" یا "42"

    def __str__(self):
        return f"{self.key}: {self.value}"
        
        
        
class Store(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store', verbose_name='Store Owner')
    name = models.CharField(max_length=100, verbose_name='Store Name')
    address = models.CharField(max_length=255, verbose_name='Address')
    city = models.CharField(max_length=50, verbose_name='City')
    province = models.CharField(max_length=50, verbose_name='Province')
    products = models.ManyToManyField(Product, blank=True, related_name='stores', verbose_name='Products')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Store"
        verbose_name_plural = "Stores"