from django.contrib import admin
from .models import TutorialModel, CategoryModel, ArticleModel, ShoeModel


admin.site.register(TutorialModel)
admin.site.register(CategoryModel)
admin.site.register(ArticleModel)
admin.site.register(ShoeModel)

