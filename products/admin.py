from django.contrib import admin
from .models import TutorialModel, CategoryModel, ArticleModel


admin.site.register(TutorialModel)
admin.site.register(CategoryModel)
admin.site.register(ArticleModel)

