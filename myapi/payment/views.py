# carts/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from payment.models import Cart, CartItem
from accounts.models import ProfileModel
from myapi.payment.CartSerializerFile import CartSerializer
from myapi.payment.CartItemSerializerFile import CartItemSerializer
from products.models import Product, ProductVariant
from django.core.exceptions import ValidationError as DjangoValidationError


class CartViewSet(viewsets.GenericViewSet):
    """
    ViewSet برای مدیریت سبد خرید
    پشتیبانی از:
    - شناسایی پروفایل از طریق tel_id یا bale_id
    - کاربران مهمان (با session_key)
    - ادغام سبد خرید مهمان پس از احراز هویت
    """
    serializer_class = CartSerializer
    queryset = Cart.objects.all()
    
    def _get_profile_by_identifier(self, tel_id=None, bale_id=None):
        """
        دریافت پروفایل بر اساس tel_id یا bale_id
        اولویت: اگر tel_id وجود داشت → با tel_id
        اگر tel_id نداشت ولی bale_id داشت → با bale_id
        اگر هیچکدام نداشت → None
        """
        # اولویت اول: tel_id
        if tel_id:
            try:
                return ProfileModel.objects.get(tel_id=tel_id)
            except ProfileModel.DoesNotExist:
                return None
        
        # اولویت دوم: bale_id
        if bale_id:
            try:
                return ProfileModel.objects.get(bale_id=bale_id)
            except ProfileModel.DoesNotExist:
                return None
        
        return None
    
    def _get_profile_from_request(self, request):
        """
        دریافت پروفایل از درخواست
        از query_params یا data
        """
        # ابتدا از query_params (GET)
        tel_id = request.query_params.get('tel_id')
        bale_id = request.query_params.get('bale_id')
        
        # اگر در query_params نبود، از data (POST, PUT)
        if not tel_id and not bale_id:
            tel_id = request.data.get('tel_id')
            bale_id = request.data.get('bale_id')
        
        # اگر باز هم نبود، از هدرها
        if not tel_id and not bale_id:
            tel_id = request.headers.get('X-Tel-ID')
            bale_id = request.headers.get('X-Bale-ID')
        
        return self._get_profile_by_identifier(tel_id, bale_id)
    
    def _get_session_key_from_request(self, request):
        """
        دریافت یا ایجاد session_key برای کاربران مهمان
        """
        session_key = request.session.session_key
        if not session_key:
            # اگر session وجود ندارد، یکی بساز
            request.session.create()
            session_key = request.session.session_key
        return session_key
    
    def _get_or_create_cart(self, profile=None, session_key=None):
        """
        دریافت یا ساخت سبد خرید بر اساس اولویت:
        1. اگر profile داریم → سبد خرید کاربر احراز هویت شده
        2. اگر session_key داریم → سبد خرید مهمان
        3. اگر هیچکدام → خطا
        """
        if profile:
            cart, created = Cart.objects.get_or_create(profile=profile)
            return cart, created
        
        elif session_key:
            cart, created = Cart.objects.get_or_create(session_key=session_key)
            return cart, created
        
        else:
            raise ValueError("Either profile (tel_id/bale_id) or session_key is required")
    
    def _merge_guest_cart_to_user_cart(self, user_cart, guest_cart):
        """
        ادغام سبد خرید مهمان با سبد خرید کاربر احراز هویت شده
        وقتی کاربر لاگین می‌کند، آیتم‌های سبد خرید مهمان را به سبد خرید کاربر منتقل می‌کند
        """
        for guest_item in guest_cart.items.all():
            # بررسی آیا محصول مشابه (با واریانت یکسان) در سبد خرید کاربر وجود دارد
            user_item = user_cart.items.filter(
                product=guest_item.product,
                variant=guest_item.variant
            ).first()
            
            if user_item:
                # اگر وجود دارد، quantity را جمع کن
                user_item.quantity += guest_item.quantity
                user_item.save()
            else:
                # اگر وجود ندارد، منتقل کن
                guest_item.cart = user_cart
                guest_item.save()
        
        # حذف سبد خرید مهمان
        guest_cart.delete()
    
    @action(detail=False, methods=['get'], url_path='current')
    def get_current_cart(self, request):
        """
        دریافت سبد خرید فعلی
        - اگر tel_id یا bale_id فرستاده شده → سبد خرید مربوط به پروفایل
        - اگر نه → سبد خرید مهمان با session_key
        """
        try:
            profile = self._get_profile_from_request(request)
            session_key = None
            print(profile)
            if not profile:
                session_key = self._get_session_key_from_request(request)
                user_type = "guest"
            else:
                user_type = "authenticated"
            
            cart, created = self._get_or_create_cart(profile=profile, session_key=session_key)
            
            serializer = self.get_serializer(cart)
            
            response_data = {
                'cart': serializer.data,
                'is_new': created,
                'item_count': cart.total_items(),
                'total_price': str(cart.total_price()),
                'user_type': user_type,
                'sellers_split': {str(k): v for k, v in cart.get_sellers_split().items()}
            }
            
            # اگر پروفایل داشتیم، اطلاعات آن را هم اضافه کن
            if profile:
                response_data['profile'] = {
                    'id': profile.id,
                    'tel_id': profile.tel_id,
                    'bale_id': profile.bale_id,
                    'fname': profile.fname,
                    'lname': profile.lname
                }
            
            return Response(response_data)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='add-item')
    def add_cart_item(self, request):
        """
        اضافه کردن آیتم به سبد خرید
        پارامترها:
        - tel_id یا bale_id (اختیاری، برای کاربران احراز هویت شده)
        - product_id (اجباری)
        - variant_id (اختیاری)
        - quantity (پیش‌فرض 1)
        """
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        quantity = request.data.get('quantity', 1)
        
        # اعتبارسنجی
        if not product_id:
            return Response(
                {"error": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            return Response(
                {"error": "quantity must be a positive integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # دریافت محصول
        try:
            product = Product.objects.get(id=product_id, status=True)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found or inactive"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # دریافت واریانت (اگر وجود داشته باشد)
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
            except ProductVariant.DoesNotExist:
                return Response(
                    {"error": "Variant not found for this product"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # بررسی موجودی
        if variant:
            if quantity > variant.stock:
                return Response(
                    {"error": f"موجودی واریانت ({variant.stock}) کافی نیست"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            if quantity > product.stock:
                return Response(
                    {"error": f"موجودی محصول ({product.stock}) کافی نیست"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # دریافت یا ساخت سبد خرید
        profile = self._get_profile_from_request(request)
        session_key = None
        
        if not profile:
            session_key = self._get_session_key_from_request(request)
            user_type = "guest"
        else:
            user_type = "authenticated"
        
        try:
            cart, cart_created = self._get_or_create_cart(profile=profile, session_key=session_key)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # اضافه کردن یا آپدیت آیتم
        try:
            with transaction.atomic():
                cart_item, item_created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    defaults={'quantity': quantity}
                )
                
                if not item_created:
                    # بررسی موجودی قبل از افزایش
                    new_quantity = cart_item.quantity + quantity
                    if variant:
                        if new_quantity > variant.stock:
                            return Response(
                                {"error": f"موجودی کافی نیست. حداکثر {variant.stock} عدد"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    else:
                        if new_quantity > product.stock:
                            return Response(
                                {"error": f"موجودی کافی نیست. حداکثر {product.stock} عدد"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    
                    cart_item.quantity = new_quantity
                    cart_item.save()
            
            # سerialize کردن نتیجه
            cart_serializer = self.get_serializer(cart)
            item_serializer = CartItemSerializer(cart_item)
            
            return Response({
                'message': 'Item added to cart successfully',
                'cart': cart_serializer.data,
                'item': item_serializer.data,
                'is_new_item': item_created,
                'item_count': cart.total_items(),
                'cart_total': str(cart.total_price()),
                'user_type': user_type
            }, status=status.HTTP_200_OK)
            
        except DjangoValidationError as e:
            return Response(
                {"error": e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='update-item')
    def update_cart_item(self, request):
        """
        به‌روزرسانی quantity یک آیتم در سبد خرید
        """
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        if not item_id or not quantity:
            return Response(
                {"error": "item_id and quantity are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {"error": "quantity must be positive"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "quantity must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # دریافت آیتم
        try:
            cart_item = CartItem.objects.get(id=item_id)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی موجودی
        if quantity > cart_item.available_stock():
            return Response(
                {"error": f"موجودی کافی نیست. حداکثر {cart_item.available_stock()} عدد"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item.quantity = quantity
            cart_item.save()
            
            cart_serializer = self.get_serializer(cart_item.cart)
            
            return Response({
                'message': 'Cart item updated successfully',
                'cart': cart_serializer.data,
                'item': CartItemSerializer(cart_item).data,
                'cart_total': str(cart_item.cart.total_price())
            }, status=status.HTTP_200_OK)
            
        except DjangoValidationError as e:
            return Response(
                {"error": e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['delete'], url_path='remove-item')
    def remove_cart_item(self, request):
        """
        حذف یک آیتم از سبد خرید
        """
        item_id = request.query_params.get('item_id') or request.data.get('item_id')
        
        if not item_id:
            return Response(
                {"error": "item_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item = CartItem.objects.get(id=item_id)
            cart = cart_item.cart
            cart_item.delete()
            
            cart_serializer = self.get_serializer(cart)
            
            return Response({
                'message': 'Item removed from cart successfully',
                'cart': cart_serializer.data,
                'item_count': cart.total_items(),
                'cart_total': str(cart.total_price())
            }, status=status.HTTP_200_OK)
            
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'], url_path='clear')
    def clear_cart(self, request):
        """
        خالی کردن کامل سبد خرید
        """
        profile = self._get_profile_from_request(request)
        session_key = None
        
        if not profile:
            session_key = self._get_session_key_from_request(request)
        
        try:
            cart, _ = self._get_or_create_cart(profile=profile, session_key=session_key)
            cart.items.all().delete()
            
            return Response({
                'message': 'Cart cleared successfully',
                'cart_id': cart.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='merge')
    def merge_carts(self, request):
        """
        ادغام سبد خرید مهمان با سبد خرید کاربر پس از احراز هویت
        پارامترها:
        - session_key (اجباری)
        - tel_id یا bale_id (اجباری)
        """
        session_key = request.data.get('session_key')
        tel_id = request.data.get('tel_id')
        bale_id = request.data.get('bale_id')
        
        if not session_key:
            return Response(
                {"error": "session_key is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not tel_id and not bale_id:
            return Response(
                {"error": "Either tel_id or bale_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile = self._get_profile_by_identifier(tel_id, bale_id)
        if not profile:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            guest_cart = Cart.objects.get(session_key=session_key)
            user_cart, _ = Cart.objects.get_or_create(profile=profile)
            
            self._merge_guest_cart_to_user_cart(user_cart, guest_cart)
            
            serializer = self.get_serializer(user_cart)
            
            return Response({
                'message': 'Carts merged successfully',
                'cart': serializer.data,
                'item_count': user_cart.total_items(),
                'total_price': str(user_cart.total_price())
            }, status=status.HTTP_200_OK)
            
        except Cart.DoesNotExist:
            return Response(
                {"error": "Guest cart not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='by-profile')
    def get_cart_by_profile(self, request):
        """
        دریافت سبد خرید بر اساس tel_id یا bale_id
        """
        tel_id = request.query_params.get('tel_id')
        bale_id = request.query_params.get('bale_id')
        
        if not tel_id and not bale_id:
            return Response(
                {"error": "Either tel_id or bale_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile = self._get_profile_by_identifier(tel_id, bale_id)
        
        if not profile:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        cart, created = Cart.objects.get_or_create(profile=profile)
        serializer = self.get_serializer(cart)
        
        return Response({
            'cart': serializer.data,
            'profile': {
                'id': profile.id,
                'tel_id': profile.tel_id,
                'bale_id': profile.bale_id,
                'fname': profile.fname,
                'lname': profile.lname
            }
        })


class CartItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت مستقیم آیتم‌های سبد خرید
    """
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        """
        فیلتر کردن آیتم‌ها بر اساس سبد خرید
        """
        queryset = super().get_queryset()
        
        # فیلتر بر اساس cart_id
        cart_id = self.request.query_params.get('cart_id')
        if cart_id:
            queryset = queryset.filter(cart_id=cart_id)
        
        # فیلتر بر اساس profile (از طریق tel_id یا bale_id)
        tel_id = self.request.query_params.get('tel_id')
        bale_id = self.request.query_params.get('bale_id')
        
        if tel_id or bale_id:
            try:
                if tel_id:
                    profile = ProfileModel.objects.get(tel_id=tel_id)
                else:
                    profile = ProfileModel.objects.get(bale_id=bale_id)
                
                cart = Cart.objects.filter(profile=profile).first()
                if cart:
                    queryset = queryset.filter(cart=cart)
                else:
                    queryset = queryset.none()
            except ProfileModel.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
