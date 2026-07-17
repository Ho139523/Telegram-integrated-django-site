#!/bin/bash

# ============================================
# تنظیمات - این مقادیر را بررسی کنید
# ============================================
ACCOUNT_ID="828e4b3c945cad5218e370a7fae7db71"
API_TOKEN="cfat_kGiygnVyEBL4brrR9GrfoWAdfgfoc3Bcp0TqP5jea06da576"
SCRIPT_NAME="telegram-relay"

echo "🚀 Deploying Worker to Cloudflare..."

# ============================================
# 1. حذف Worker قبلی (در صورت وجود)
# ============================================
echo "📝 Removing existing Worker (if any)..."
curl -X DELETE "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}" \
     -H "Authorization: Bearer ${API_TOKEN}" \
     -H "Content-Type: application/json" 2>/dev/null

# ============================================
# 2. ایجاد فایل worker.js با کد نهایی
# ============================================
cat > worker.js << 'EOF'
const AUTH_KEY = "M_r_HUSSEIN2079139523";

async function handleRequest(request) {
    // فقط درخواست‌های POST
    if (request.method !== 'POST') {
        return new Response(JSON.stringify({ error: "Use POST method" }), {
            status: 405,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    try {
        const payload = await request.json();
        
        // بررسی کلید احراز هویت
        if (payload.k !== AUTH_KEY) {
            return new Response(JSON.stringify({ error: "Unauthorized" }), {
                status: 401,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // اعتبارسنجی URL
        if (!payload.u) {
            return new Response(JSON.stringify({ error: "Missing target URL" }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // آماده‌سازی گزینه‌های درخواست
        const options = {
            method: payload.m || 'GET',
            headers: payload.h || {},
            redirect: 'follow'
        };

        // اضافه کردن body (در صورت وجود)
        if (payload.b) {
            try {
                const binaryString = atob(payload.b);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                options.body = bytes;
            } catch (e) {
                return new Response(JSON.stringify({ error: "Invalid base64 body" }), {
                    status: 400,
                    headers: { 'Content-Type': 'application/json' }
                });
            }
        }

        // ارسال درخواست به هدف نهایی
        const response = await fetch(payload.u, options);
        const responseBody = await response.arrayBuffer();
        
        // فیلتر هدرهای پاسخ
        const responseHeaders = {};
        for (const [key, value] of response.headers) {
            if (!['connection', 'content-length', 'transfer-encoding', 'cf-ray', 'cf-cache-status'].includes(key.toLowerCase())) {
                responseHeaders[key] = value;
            }
        }

        // تبدیل پاسخ به base64
        const base64Body = btoa(
            String.fromCharCode(...new Uint8Array(responseBody))
        );

        // بازگشت پاسخ به صورت JSON
        return new Response(JSON.stringify({
            status: response.status,
            headers: responseHeaders,
            body: base64Body
        }), {
            headers: { 
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });

    } catch (error) {
        console.error("Worker error:", error);
        return new Response(JSON.stringify({ 
            error: "Internal error: " + error.message 
        }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// نقطه ورودی Worker
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request));
});
EOF

echo "✅ Worker code prepared."

# ============================================
# 3. دیپلوی Worker
# ============================================
echo "📤 Deploying Worker script..."
RESPONSE=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}" \
     -H "Authorization: Bearer ${API_TOKEN}" \
     -H "Content-Type: application/javascript" \
     --data-binary @worker.js)

# بررسی نتیجه دیپلوی
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ Worker deployed successfully!"
else
    echo "❌ Deployment failed!"
    echo "$RESPONSE" | jq '.errors[] | {code, message}' 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

# ============================================
# 4. فعال‌سازی روی subdomain (اختیاری)
# ============================================
echo "🌐 Enabling subdomain (optional)..."
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}/subdomain" \
     -H "Authorization: Bearer ${API_TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{"enabled": true}' > /dev/null 2>&1

# ============================================
# 5. نمایش اطلاعات نهایی
# ============================================
echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo "📡 Worker URL: https://${SCRIPT_NAME}.${ACCOUNT_ID}.workers.dev"
echo "🔑 Auth Key: M_r_HUSSEIN2079139523"
echo "=========================================="
echo ""
echo "🧪 Test with:"
echo "curl -X POST https://${SCRIPT_NAME}.${ACCOUNT_ID}.workers.dev \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"k\":\"M_r_HUSSEIN2079139523\",\"u\":\"https://api.telegram.org/botTEST/getMe\",\"m\":\"GET\"}'"
echo ""
