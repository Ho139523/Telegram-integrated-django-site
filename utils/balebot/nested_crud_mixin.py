# utils/nested_crud_mixin.py
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from django.core.exceptions import FieldError
from utils.balebot.dynamic_serializers import get_serializer_for_model

class NestedCRUDMixin:
    """
    Mixin برای اضافه کردن قابلیت CRUD روی تمام روابط یک مدل
    """
    
    # تنظیمات
    NESTED_DEPTH = 1  # عمق nested serialization
    EXCLUDED_RELATIONS = []  # روابطی که نباید expose شوند
    
    def _get_relation_field(self, relation_name):
        """دریافت فیلد رابطه از مدل"""
        try:
            return self.queryset.model._meta.get_field(relation_name)
        except FieldError:
            return None
    
    def _is_valid_relation(self, relation_name):
        """بررسی معتبر بودن نام رابطه"""
        if relation_name in self.EXCLUDED_RELATIONS:
            return False
        
        field = self._get_relation_field(relation_name)
        if not field:
            return False
        
        # انواع رابطه‌های پشتیبانی شده
        supported = (
            models.ForeignKey,
            models.OneToOneField,
            models.ManyToManyField,
        )
        return isinstance(field, supported)
    
    def _get_related_object(self, instance, relation_name):
        """دریافت شیء مرتبط"""
        field = self._get_relation_field(relation_name)
        
        if isinstance(field, models.ManyToManyField):
            return getattr(instance, relation_name).all()
        else:
            return getattr(instance, relation_name)
    
    def _set_related_object(self, instance, relation_name, value):
        """تنظیم شیء مرتبط"""
        field = self._get_relation_field(relation_name)
        
        if isinstance(field, models.ManyToManyField):
            # برای ManyToMany، value باید لیستی از IDها باشد
            if isinstance(value, list):
                getattr(instance, relation_name).set(value)
            return True
        elif isinstance(field, (models.ForeignKey, models.OneToOneField)):
            # برای ForeignKey و OneToOne
            if isinstance(value, dict):
                # ایجاد یا بروزرسانی شیء مرتبط
                ModelClass = field.related_model
                existing = getattr(instance, relation_name)
                
                if existing:
                    serializer = get_serializer_for_model(ModelClass)(
                        existing, data=value, partial=True
                    )
                else:
                    serializer = get_serializer_for_model(ModelClass)(data=value)
                
                if serializer.is_valid():
                    new_obj = serializer.save()
                    setattr(instance, relation_name, new_obj)
                    return True
                else:
                    raise ValueError(serializer.errors)
            elif isinstance(value, int):
                # اتصال به شیء موجود با ID
                ModelClass = field.related_model
                obj = ModelClass.objects.get(id=value)
                setattr(instance, relation_name, obj)
                return True
        return False
    
    @action(detail=False, methods=['get'], url_path='(?P<identifier>[^/.]+)/relations')
    def list_relations(self, request, identifier=None):
        """
        لیست تمام روابط قابل دسترس یک پروفایل
        
        GET /api/bot/profiles/123/relations/
        """
        try:
            instance = self.get_object_by_identifier(identifier) if hasattr(self, 'get_object_by_identifier') else self.get_object()
            
            relations = {}
            for field in instance._meta.get_fields():
                if self._is_valid_relation(field.name):
                    relations[field.name] = {
                        'type': field.__class__.__name__,
                        'model': field.related_model.__name__ if field.related_model else None,
                        'url': f"/api/bot/profiles/{identifier}/{field.name}/"
                    }
            
            return Response({
                "success": True,
                "profile_id": instance.id,
                "relations": relations
            })
        except Exception as e:
            return Response({"error": str(e)}, status=404)
    
    @action(detail=False, methods=['get'], url_path='(?P<identifier>[^/.]+)/(?P<relation_name>[a-zA-Z_]+)')
    def get_relation(self, request, identifier=None, relation_name=None):
        """
        دریافت داده‌های یک رابطه خاص
        
        GET /api/bot/profiles/123/owned_store/
        GET /api/bot/profiles/123/addresses/
        GET /api/bot/profiles/123/transactions/
        """
        try:
            instance = self.get_object_by_identifier(identifier) if hasattr(self, 'get_object_by_identifier') else self.get_object()
            
            if not self._is_valid_relation(relation_name):
                return Response({
                    "success": False,
                    "error": f"Relation '{relation_name}' is not accessible"
                }, status=400)
            
            related = self._get_related_object(instance, relation_name)
            
            if related is None:
                return Response({
                    "success": False,
                    "error": f"No {relation_name} found"
                }, status=404)
            
            # تشخیص نوع QuerySet یا مدل
            if hasattr(related, 'all'):  # ManyToMany یا reverse relation
                serializer_class = get_serializer_for_model(related.model)
                serializer = serializer_class(related.all(), many=True)
            else:  # OneToOne یا ForeignKey
                serializer_class = get_serializer_for_model(related.__class__)
                serializer = serializer_class(related)
            
            return Response({
                "success": True,
                "relation": relation_name,
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=404)
    
    @action(detail=False, methods=['post', 'put', 'patch'], url_path='(?P<identifier>[^/.]+)/(?P<relation_name>[a-zA-Z_]+)')
    def update_relation(self, request, identifier=None, relation_name=None):
        """
        ایجاد یا بروزرسانی یک رابطه
        
        POST /api/bot/profiles/123/owned_store/  {"name": "New Store", ...}
        PUT /api/bot/profiles/123/server_store/  {"id": 10}
        PATCH /api/bot/profiles/123/user/        {"first_name": "John"}
        """
        try:
            instance = self.get_object_by_identifier(identifier) if hasattr(self, 'get_object_by_identifier') else self.get_object()
            
            if not self._is_valid_relation(relation_name):
                return Response({"error": "Invalid relation"}, status=400)
            
            success = self._set_related_object(instance, relation_name, request.data)
            
            if success:
                instance.save()
                
                # برگرداندن داده به‌روز شده
                related = self._get_related_object(instance, relation_name)
                if hasattr(related, 'all'):
                    serializer_class = get_serializer_for_model(related.model)
                    serializer = serializer_class(related.all(), many=True)
                else:
                    serializer_class = get_serializer_for_model(related.__class__)
                    serializer = serializer_class(related)
                
                return Response({
                    "success": True,
                    "action": "updated",
                    "relation": relation_name,
                    "data": serializer.data
                })
            else:
                return Response({"error": "Failed to update relation"}, status=400)
                
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=404)
    
    @action(detail=False, methods=['delete'], url_path='(?P<identifier>[^/.]+)/(?P<relation_name>[a-zA-Z_]+)')
    def delete_relation(self, request, identifier=None, relation_name=None):
        """
        حذف یا قطع ارتباط یک رابطه
        
        DELETE /api/bot/profiles/123/owned_store/              # قطع ارتباط
        DELETE /api/bot/profiles/123/owned_store/?hard=true    # حذف کامل
        """
        try:
            instance = self.get_object_by_identifier(identifier) if hasattr(self, 'get_object_by_identifier') else self.get_object()
            
            if not self._is_valid_relation(relation_name):
                return Response({"error": "Invalid relation"}, status=400)
            
            field = self._get_relation_field(relation_name)
            related = self._get_related_object(instance, relation_name)
            
            if not related:
                return Response({"error": f"No {relation_name} to delete"}, status=404)
            
            hard_delete = request.query_params.get('hard', 'false').lower() == 'true'
            
            if hard_delete and isinstance(field, (models.OneToOneField, models.ForeignKey)):
                # حذف فیزیکی شیء مرتبط
                if hasattr(related, 'delete'):
                    related.delete()
                message = f"{relation_name} permanently deleted"
            else:
                # فقط قطع ارتباط
                if isinstance(field, models.ManyToManyField):
                    getattr(instance, relation_name).clear()
                else:
                    setattr(instance, relation_name, None)
                    instance.save()
                message = f"{relation_name} disconnected from profile"
            
            return Response({
                "success": True,
                "message": message,
                "relation": relation_name
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=404)
    
    @action(detail=False, methods=['post'], url_path='(?P<identifier>[^/.]+)/batch')
    def batch_update(self, request, identifier=None):
        """
        بروزرسانی همزمان چندین رابطه و فیلد
        
        POST /api/bot/profiles/123/batch/
        {
            "relations": {
                "owned_store": {"name": "Updated Store"},
                "server_store": {"id": 10},
                "addresses": [{"shipping_line1": "New Address"}]
            },
            "fields": {
                "fname": "John",
                "lname": "Doe"
            }
        }
        """
        try:
            instance = self.get_object_by_identifier(identifier) if hasattr(self, 'get_object_by_identifier') else self.get_object()
            results = {
                "relations": {},
                "fields": {},
                "errors": {}
            }
            
            # بروزرسانی فیلدهای مستقیم
            fields_data = request.data.get('fields', {})
            for field_name, value in fields_data.items():
                if hasattr(instance, field_name):
                    setattr(instance, field_name, value)
                    results['fields'][field_name] = "updated"
                else:
                    results['errors'][field_name] = "Field not found"
            
            instance.save()
            
            # بروزرسانی روابط
            relations_data = request.data.get('relations', {})
            for relation_name, data in relations_data.items():
                try:
                    if self._is_valid_relation(relation_name):
                        self._set_related_object(instance, relation_name, data)
                        results['relations'][relation_name] = "updated"
                    else:
                        results['errors'][relation_name] = "Invalid relation"
                except Exception as e:
                    results['errors'][relation_name] = str(e)
            
            instance.save()
            
            # برگرداندن داده کامل
            serializer_class = get_serializer_for_model(instance.__class__)
            serializer = serializer_class(instance)
            
            return Response({
                "success": True,
                "results": results,
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=400)