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
