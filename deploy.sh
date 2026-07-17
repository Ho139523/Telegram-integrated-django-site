#!/bin/bash

# ============================================
# تنظیمات Cloudflare
# ============================================
ACCOUNT_ID="828e4b3c945cad5218e370a7fae7db71"
API_TOKEN="cfat_kGiygnVyEBL4brrR9GrfoWAdfgfoc3Bcp0TqP5jea06da576"
SCRIPT_NAME="telegram-webhook"

echo "🚀 Deploying Telegram Webhook Worker..."

# ============================================
# 1. حذف Worker قبلی
# ============================================
echo "📝 Removing existing Worker..."
curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}" \
     -H "Authorization: Bearer ${API_TOKEN}" \
     -H "Content-Type: application/json" > /dev/null

# ============================================
# 2. دیپلوی Worker جدید
# ============================================
echo "📤 Deploying Worker..."
RESPONSE=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}" \
     -H "Authorization: Bearer ${API_TOKEN}" \
     -H "Content-Type: application/javascript" \
     --data-binary @worker.js)

# بررسی نتیجه
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ Worker deployed successfully!"
else
    echo "❌ Deployment failed!"
    echo "$RESPONSE" | jq '.errors[] | {code, message}' 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

# ============================================
# 3. تنظیم Webhook در تلگرام
# ============================================
echo "🔗 Setting webhook on Telegram..."
WEBHOOK_URL="https://${SCRIPT_NAME}.${ACCOUNT_ID}.workers.dev"

WEBHOOK_RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot1234567890:ABCdefGHIjklMNOpqrsTUVwxyz/setWebhook" \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"${WEBHOOK_URL}\", \"allowed_updates\": [\"message\", \"callback_query\"]}")

echo "📡 Webhook response:"
echo "$WEBHOOK_RESPONSE" | jq '.'

# ============================================
# 4. نمایش اطلاعات نهایی
# ============================================
echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo "📡 Worker URL: ${WEBHOOK_URL}"
echo "🔑 Auth Key: M_r_HUSSEIN2079139523"
echo "📨 Webhook (your server): ${WEBHOOK_URL}"
echo "=========================================="
