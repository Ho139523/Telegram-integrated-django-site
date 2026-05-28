from attr import field
import rest_framework
from heartpred.models import Person, Book
from accounts.models import ProfileModel
from myapi.accounts.ProfileSerializerFile import *
from myapi import serializer
from myapi.accounts.serializers import *
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import BasePermission



class MCP(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get("TOKEN")
        has_valid_token = token == "123456789"

        is_authenticated = request.user.is_authenticated

        allowed_ips = ['127.0.0.1', '192.168.1.100']
        ip_address = request.META.get("REMOTE_ADDR")

        has_valid_id = ip_address in allowed_ips
        
        from datetime import datetime
        is_in_time = 11 < datetime.now().hour < 20
        is_even_day = datetime.now().day%2 == 0
        
        if has_valid_token and is_authenticated and has_valid_id and is_in_time:
            return True
        return True


from rest_framework.pagination import PageNumberPagination

class MCG(PageNumberPagination):
    page_size = 7
    page_query_param = "p"
    max_page_size = 100


from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters



class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [MCP]
    pagination_class = MCG


    @action(detail=False, methods=["get"])
    def recent(self, request):
        person = Person.objects.all().order_by('-id')[:2]
        serializer = self.get_serializer(person, many=True)
        return Response(serializer.data)


    @action(detail=True, url_path="add", methods=['get', 'post'])
    def add_age(self, request, pk):
        person = self.get_object()
        person.age += 1
        person.save()
        serializer = self.get_serializer(person)
        return Response(serializer.data)
    
    @action(detail=False, url_path="adults", methods=["get"])
    def show_adults(self, request):
        persons = Person.objects.filter(age__gte=18)
        serializer = self.get_serializer(persons, many=True)
        return Response(serializer.data)


# اصلاح شده و کامل
class BookFilter(filters.FilterSet):
    # فیلترهای سال انتشار
    min_year = filters.NumberFilter(field_name="published_year", lookup_expr="gte")  # ✅ اصلاح شد
    max_year = filters.NumberFilter(field_name="published_year", lookup_expr="lte")  # ✅ اصلاح شد
    
    # فیلترهای عنوان
    title_contains = filters.CharFilter(field_name='title', lookup_expr='icontains')
    title_startswith = filters.CharFilter(field_name='title', lookup_expr='startswith')
    title_endswith = filters.CharFilter(field_name='title', lookup_expr='endswith')
    
    # فیلتر نویسنده (چندتایی)
    author = filters.ModelMultipleChoiceFilter(
        field_name='author',
        to_field_name='id',
        queryset=Person.objects.all()
    )
    
    # فیلتر دقیق سال
    published_year_exact = filters.NumberFilter(field_name='published_year', lookup_expr='exact')
    
    class Meta:
        model = Book
        fields = ['author', 'title', 'published_year']

from rest_framework import filters

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]  # این خط را هم اضافه کنید
    filterset_class = BookFilter
    ordering_fields = ['published_year', 'title']
    ordering = ['-published_year']

    def get_serializer_class(self):
        """اگر درخواست ایجاد یا آپدیت باشد، از NestedBookSerializer استفاده کن"""
        if self.action in ['create', 'update', 'partial_update']:
            return NestedBookSerializer
        return BookSerializer 






from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from accounts.models import ProfileModel
from myapi.accounts.ProfileSerializerFile import ProfileSerializer, ProfileCheckSerializer
from utils.permissions import BotSignaturePermission, IsAdminOrReadOnly
from utils.balebot.nested_crud_mixin import NestedCRUDMixin  # اضافه کردن mixin جدید
from utils.balebot.dynamic_serializers import get_serializer_for_model


class ProfileViewSet(
    NestedCRUDMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,  # ⭐ اضافه شد
    viewsets.GenericViewSet
):
    """
    Complete CRUD operations for Profile model
    """
    
    EXCLUDED_RELATIONS = ['hidden_videos']
    NESTED_DEPTH = 1
    
    queryset = ProfileModel.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = []
    lookup_field = 'identifier'
    lookup_value_regex = '[^/.]+'
    throttle_classes = []

    # ============================================================
    # LIST (GET all profiles) - ⭐ جدید
    # ============================================================
    def list(self, request, *args, **kwargs):
        """List all profiles"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Optional search
        search_term = request.query_params.get('search')
        if search_term:
            queryset = queryset.filter(
                Q(fname__icontains=search_term) |
                Q(lname__icontains=search_term) |
                Q(tel_id__icontains=search_term) |
                Q(bale_id__icontains=search_term)
            )
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                "success": True,
                "data": serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "count": queryset.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ============================================================
    # GET OBJECT BY IDENTIFIER
    # ============================================================
    def get_object_by_identifier(self, identifier: str) -> ProfileModel:
        """Get profile by either tel_id or bale_id"""
        try:
            profile = ProfileModel.objects.get(
                Q(tel_id=identifier) | Q(bale_id=identifier)
            )
            return profile
        except ProfileModel.DoesNotExist:
            raise ProfileModel.DoesNotExist(f"Profile with identifier '{identifier}' not found")

    def get_relation_instance(self, identifier):
        """Helper method to get instance by identifier"""
        return self.get_object_by_identifier(identifier)

    # ============================================================
    # RETRIEVE (GET by identifier)
    # ============================================================
    def retrieve(self, request, identifier=None, *args, **kwargs):
        """Get profile by either tel_id or bale_id"""
        try:
            profile = self.get_object_by_identifier(identifier)
            serializer = self.get_serializer(profile)
            return Response({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)

    # ============================================================
    # CREATE (UPSERT)
    # ============================================================
    def create(self, request, *args, **kwargs):
        """Create or update profile (UPSERT)"""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tel_id = serializer.validated_data.get('tel_id')
        bale_id = serializer.validated_data.get('bale_id')
        
        if not tel_id and not bale_id:
            return Response({
                "success": False,
                "error": "Either tel_id or bale_id must be provided"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        query = Q()
        if tel_id:
            query |= Q(tel_id=tel_id)
        if bale_id:
            query |= Q(bale_id=bale_id)
        
        existing_profile = ProfileModel.objects.filter(query).first()
        
        if existing_profile:
            update_data = {}
            for key, value in serializer.validated_data.items():
                if value is not None:
                    update_data[key] = value
            
            if tel_id is None and existing_profile.tel_id:
                update_data.pop('tel_id', None)
            if bale_id is None and existing_profile.bale_id:
                update_data.pop('bale_id', None)
            
            for key, value in update_data.items():
                setattr(existing_profile, key, value)
            existing_profile.save()
            
            output_serializer = self.get_serializer(existing_profile)
            return Response({
                "success": True,
                "created": False,
                "updated": True,
                "data": output_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            profile = serializer.save()
            output_serializer = self.get_serializer(profile)
            return Response({
                "success": True,
                "created": True,
                "updated": False,
                "data": output_serializer.data
            }, status=status.HTTP_201_CREATED)

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self, request, identifier=None, *args, **kwargs):
        """Full update profile by tel_id or bale_id"""
        try:
            profile = self.get_object_by_identifier(identifier)
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(profile, data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ============================================================
    # PARTIAL UPDATE
    # ============================================================
    def partial_update(self, request, identifier=None, *args, **kwargs):
        """Partial update profile by tel_id or bale_id"""
        try:
            profile = self.get_object_by_identifier(identifier)
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ============================================================
    # DELETE
    # ============================================================
    def destroy(self, request, identifier=None, *args, **kwargs):
        """Delete profile by tel_id or bale_id"""
        try:
            profile = self.get_object_by_identifier(identifier)
            profile.delete()
            return Response({
                "success": True,
                "message": "Profile deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)

    # ============================================================
    # CHECK ENDPOINT
    # ============================================================
    @action(detail=False, methods=['post'], url_path='check', serializer_class=ProfileCheckSerializer)
    def check_exists(self, request):
        """Check if profile exists"""
        serializer = ProfileCheckSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        identifier = serializer.validated_data.get('identifier')
        tel_id = serializer.validated_data.get('tel_id')
        bale_id = serializer.validated_data.get('bale_id')
        
        if identifier:
            exists = ProfileModel.objects.filter(
                Q(tel_id=identifier) | Q(bale_id=identifier)
            ).exists()
            profile = ProfileModel.objects.filter(
                Q(tel_id=identifier) | Q(bale_id=identifier)
            ).first() if exists else None
            
            return Response({
                "success": True,
                "exists": exists,
                "profile_id": profile.id if profile else None,
            }, status=status.HTTP_200_OK)
        
        elif tel_id or bale_id:
            query = Q()
            if tel_id:
                query |= Q(tel_id=tel_id)
            if bale_id:
                query |= Q(bale_id=bale_id)
            exists = ProfileModel.objects.filter(query).exists()
            profile = ProfileModel.objects.filter(query).first() if exists else None
            
            return Response({
                "success": True,
                "exists": exists,
                "profile_id": profile.id if profile else None,
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "error": "No identifier provided"
        }, status=status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # MERGE PROFILES
    # ============================================================
    @action(detail=False, methods=['post'], url_path='merge')
    def merge_profiles(self, request):
        """Merge two profiles into one"""
        main_id = request.data.get('main_identifier')
        secondary_id = request.data.get('secondary_identifier')
        merge_relations = request.data.get('merge_relations', False)
        
        if not main_id or not secondary_id:
            return Response({
                "success": False,
                "error": "Both main_identifier and secondary_identifier are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            main_profile = self.get_object_by_identifier(main_id)
            secondary_profile = self.get_object_by_identifier(secondary_id)
            
            if main_profile.id == secondary_profile.id:
                return Response({
                    "success": False,
                    "error": "Cannot merge profile with itself"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            fields_to_transfer = [
                'fname', 'lname', 'phone', 'telegram', 'bale',
                'avatar', 'birthday', 'about_me', 'instagram', 'tweeter'
            ]
            
            for field in fields_to_transfer:
                if not getattr(main_profile, field) and getattr(secondary_profile, field):
                    setattr(main_profile, field, getattr(secondary_profile, field))
            
            if secondary_profile.tel_id and not main_profile.tel_id:
                main_profile.tel_id = secondary_profile.tel_id
            if secondary_profile.bale_id and not main_profile.bale_id:
                main_profile.bale_id = secondary_profile.bale_id
            
            if merge_relations:
                for address in secondary_profile.addresses.all():
                    address.profile = main_profile
                    address.save()
                
                for cart in secondary_profile.carts.all():
                    cart.profile = main_profile
                    cart.save()
                
                for transaction in secondary_profile.transactions.all():
                    transaction.profile = main_profile
                    transaction.save()
            
            main_profile.save()
            
            return Response({
                "success": True,
                "message": "Profiles merged successfully",
                "data": self.get_serializer(main_profile).data
            }, status=status.HTTP_200_OK)
            
        except ProfileModel.DoesNotExist as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)

    # ============================================================
    # LIST RELATIONS
    # ============================================================
    @action(detail=False, methods=['get'], url_path='(?P<identifier>[^/.]+)/relations')
    def list_relations(self, request, identifier=None):
        """List all accessible relations"""
        try:
            instance = self.get_relation_instance(identifier)
            
            relations = {}
            for field in instance._meta.get_fields():
                if self._is_valid_relation(field.name):
                    relations[field.name] = {
                        'type': field.__class__.__name__,
                        'model': field.related_model.__name__ if field.related_model else None,
                        'url': f"/myapi/profiles/{identifier}/{field.name}/"
                    }
            
            return Response({
                "success": True,
                "profile_id": instance.id,
                "relations": relations
            })
        except ProfileModel.DoesNotExist as e:
            return Response({"error": str(e)}, status=404)

    # ============================================================
    # GET RELATION
    # ============================================================
    @action(
        detail=False,
        methods=['get'],
        url_path='(?P<identifier>[^/.]+)/(?P<relation_name>[a-zA-Z_]+)'
    )
    def get_relation(self, request, identifier=None, relation_name=None):
        """Get relation data"""
        try:
            instance = self.get_relation_instance(identifier)
            
            if not self._is_valid_relation(relation_name):
                return Response({"error": "Invalid relation"}, status=400)
            
            related = self._get_related_object(instance, relation_name)
            
            if related is None:
                return Response({"error": f"No {relation_name} found"}, status=404)
            
            if hasattr(related, 'all'):
                serializer_class = get_serializer_for_model(related.model)
                serializer = serializer_class(related.all(), many=True)
            else:
                serializer_class = get_serializer_for_model(related.__class__)
                serializer = serializer_class(related)
            
            return Response({
                "success": True,
                "data": serializer.data
            })
            
        except ProfileModel.DoesNotExist as e:
            return Response({"error": str(e)}, status=404)

    # ============================================================
    # UPDATE RELATION
    # ============================================================
    @action(
        detail=False,
        methods=['post', 'put', 'patch'],
        url_path='(?P<identifier>[^/.]+)/(?P<relation_name>[a-zA-Z_]+)'
    )
    def update_relation(self, request, identifier=None, relation_name=None):
        """Create or update relation"""
        try:
            instance = self.get_relation_instance(identifier)
            
            if not self._is_valid_relation(relation_name):
                return Response({"error": "Invalid relation"}, status=400)
            
            success = self._set_related_object(instance, relation_name, request.data)
            
            if success:
                instance.save()
                related = self._get_related_object(instance, relation_name)
                
                if hasattr(related, 'all'):
                    serializer_class = get_serializer_for_model(related.model)
                    data = serializer_class(related.all(), many=True).data if related.count() > 0 else []
                else:
                    serializer_class = get_serializer_for_model(related.__class__)
                    data = serializer_class(related).data
                
                return Response({
                    "success": True,
                    "data": data
                })
            
            return Response({"error": "Failed to update relation"}, status=400)
            
        except ProfileModel.DoesNotExist as e:
            return Response({"error": str(e)}, status=404)

    # ============================================================
    # DELETE RELATION
    # ============================================================
    @action(
        detail=False,
        methods=['delete'],
        url_path='(?P<identifier>[^/.]+)/(?P<relation_name>[a-zA-Z_]+)'
    )
    def delete_relation(self, request, identifier=None, relation_name=None):
        """Delete relation"""
        try:
            instance = self.get_relation_instance(identifier)
            
            if not self._is_valid_relation(relation_name):
                return Response({"error": "Invalid relation"}, status=400)
            
            success = self._remove_related_object(instance, relation_name)
            
            if success:
                return Response({
                    "success": True,
                    "message": f"{relation_name} deleted successfully"
                })
            
            return Response({"error": "Failed to delete relation"}, status=400)
            
        except ProfileModel.DoesNotExist as e:
            return Response({"error": str(e)}, status=404)
    
# class ProfileViewSet(viewsets.ModelViewSet):
#     queryset = ProfileModel.objects.all()
#     serializer_class = ProfileSerializer
#     lookup_field = "bale_id"
#     permission_classes = [BotSignaturePermission]

#     @action(detail=False, methods=['post'], url_path='check', serializer_class=ProfileCheckSerializer)
#     def check_exists(self, request):
#         """Check if profile exists"""
#         serializer = ProfileCheckSerializer(data=request.data)
        
#         if not serializer.is_valid():
#             return Response(
#                 {"success": False, "errors": serializer.errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         identifier = serializer.validated_data.get('identifier')
#         tel_id = serializer.validated_data.get('tel_id')
#         bale_id = serializer.validated_data.get('bale_id')
        
#         if identifier:
#             exists = ProfileModel.objects.filter(
#                 Q(tel_id=identifier) | Q(bale_id=identifier)
#             ).exists()
#             profile = ProfileModel.objects.filter(
#                 Q(tel_id=identifier) | Q(bale_id=identifier)
#             ).first() if exists else None
            
#             return Response({
#                 "success": True,
#                 "exists": exists,
#                 "profile_id": profile.id if profile else None,
#             }, status=status.HTTP_200_OK)
        
#         elif tel_id or bale_id:
#             query = Q()
#             if tel_id:
#                 query |= Q(tel_id=tel_id)
#             if bale_id:
#                 query |= Q(bale_id=bale_id)
#             exists = ProfileModel.objects.filter(query).exists()
#             profile = ProfileModel.objects.filter(query).first() if exists else None
            
#             return Response({
#                 "success": True,
#                 "exists": exists,
#                 "profile_id": profile.id if profile else None,
#             }, status=status.HTTP_200_OK)
        
#         return Response({
#             "success": False,
#             "error": "No identifier provided"
#         }, status=status.HTTP_400_BAD_REQUEST)
