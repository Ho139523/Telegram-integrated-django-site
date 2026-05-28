from pyexpat import model
from attr import field
from executing import Source
from rest_framework.serializers import ModelSerializer
from heartpred.models import Person, Book
from rest_framework import serializers


from rest_framework import serializers

from rest_framework import serializers
from heartpred.models import Person, Book

# ========== Book Serializer ساده ==========
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'published_year']


# ========== Person Serializer (با قابلیت ایجاد همزمان کتاب) ==========
class PersonSerializer(serializers.ModelSerializer):
    books = BookSerializer(many=True, required=False)
    
    class Meta:
        model = Person
        fields = ['id', 'name', 'age', 'books']
    
    def create(self, validated_data):
        books_data = validated_data.pop('books', [])
        person = Person.objects.create(**validated_data)
        
        for book_data in books_data:
            Book.objects.create(author=person, **book_data)
        
        return person
    
    def update(self, instance, validated_data):
        books_data = validated_data.pop('books', None)
        
        instance.name = validated_data.get('name', instance.name)
        instance.age = validated_data.get('age', instance.age)
        instance.save()
        
        if books_data is not None:
            instance.books.all().delete()
            for book_data in books_data:
                Book.objects.create(author=instance, **book_data)
        
        return instance


# ========== Nested Person Serializer (برای Book) - اصلاح شده ==========
class NestedPersonSerializer(serializers.ModelSerializer):
    # name باید حتماً وجود داشته باشد (required=True پیش‌فرض است)
    # age هم می‌تواند اختیاری باشد یا نباشد
    
    class Meta:
        model = Person
        fields = ['name', 'age']
        # حذف required=False
        # می‌توانیم age را اختیاری کنیم
        extra_kwargs = {
            'age': {'required': False, 'allow_null': True}
        }


# ========== Nested Book Serializer (با قابلیت ایجاد همزمان Person) ==========
class NestedBookSerializer(serializers.ModelSerializer):
    author = NestedPersonSerializer()
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'published_year', 'author']
    
    def create(self, validated_data):
        author_data = validated_data.pop('author')
        
        # بررسی وجود name
        if not author_data.get('name'):
            raise serializers.ValidationError({
                "author": {"name": "نام نویسنده الزامی است"}
            })
        
        # ساخت یا پیدا کردن نویسنده
        author, created = Person.objects.get_or_create(
            name=author_data['name'],
            defaults={'age': author_data.get('age', 0)}
        )
        
        # آپدیت سن اگر نویسنده قبلاً وجود داشت و age داده شده بود
        if not created and author_data.get('age') is not None:
            if author.age != author_data['age']:
                author.age = author_data['age']
                author.save()
        
        return Book.objects.create(author=author, **validated_data)
    
    def update(self, instance, validated_data):
        books_data = validated_data.pop('books', None)
        
        # به‌روزرسانی فیلدهای Person
        instance.name = validated_data.get('name', instance.name)
        instance.age = validated_data.get('age', instance.age)
        instance.save()
        
        if books_data is not None:
            existing_books = {book.title: book for book in instance.books.all()}
            new_titles = set()
            
            for book_data in books_data:
                title = book_data['title']
                new_titles.add(title)
                
                if title in existing_books:
                    # کتاب وجود دارد → آپدیتش کن
                    book = existing_books[title]
                    book.published_year = book_data.get('published_year', book.published_year)
                    book.save()
                else:
                    # کتاب جدید است → بسازش
                    Book.objects.create(author=instance, **book_data)
            
            # (اختیاری) کتاب‌هایی که در درخواست جدید نیستند را حذف کن
            # for title, book in existing_books.items():
            #     if title not in new_titles:
            #         book.delete()
        
        return instance
