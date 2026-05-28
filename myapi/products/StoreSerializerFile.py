from pyexpat import model
from products.models import Store
from rest_framework import serializers


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "owner", "name", "logo", "tel_group", "tel_channel", "lang", "markant_id", "tagline", "description", "banner_image", "intro_video", "website", "support_phone", "support_email", "is_verified", "verification_level", "legal_name", "company_type", "tax_id", "min_order_amount", "lead_time_days", "payment_terms", "return_policy", "social_links"]
