// ============================================
// Cloudflare Worker - Telegram Webhook Relay (Optimized)
// ============================================

const CONFIG = {
    BOT_TOKEN: "8299606011:AAGUom7zYxGUR-9Dm17aiECVhfFe2uwIvCs",
    WEBHOOK_URL: "https://intelleum.ir/telbot/webhook/",
    AUTH_KEY: "M_r_HUSSEIN2079139523",
    TELEGRAM_API_BASE: "https://api.telegram.org/bot",
    
    // تنظیمات جدید برای کاهش تأخیر
    TIMEOUT_MS: 5000,  // 5 ثانیه timeout
    MAX_RETRIES: 2,    // تعداد تلاش مجدد
    CACHE_TTL: 0       // بدون کش
};

// ==================== کد اصلی ====================
async function handleRequest(request) {
    // فقط POST
    if (request.method !== 'POST') {
        return new Response(JSON.stringify({ error: "Use POST" }), {
            status: 405,
            headers: { 
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        });
    }

    try {
        // دریافت داده
        const payload = await request.json();
        console.log("📥 Received:", JSON.stringify(payload).substring(0, 200));

        // ============================================
        // ارسال به Webhook شما با timeout
        // ============================================
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.TIMEOUT_MS);

        let webhookResponse;
        try {
            webhookResponse = await fetch(CONFIG.WEBHOOK_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Auth-Key': CONFIG.AUTH_KEY,
                    'X-Telegram-Update': 'true'
                },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            clearTimeout(timeoutId);
        } catch (error) {
            clearTimeout(timeoutId);
            console.error("⏱️ Webhook timeout or error:", error.message);
            // حتی با خطا، به تلگرام پاسخ 200 بدهید
            return new Response(JSON.stringify({ 
                status: "ok",
                message: "Webhook processing started (async)"
            }), {
                status: 200,
                headers: { 
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                }
            });
        }

        // بررسی پاسخ Webhook
        if (!webhookResponse.ok) {
            console.error("❌ Webhook error:", webhookResponse.status);
            return new Response(JSON.stringify({ 
                status: "ok",
                message: "Webhook received, but server error"
            }), {
                status: 200,
                headers: { 
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                }
            });
        }

        // دریافت پاسخ
        let webhookResult = await webhookResponse.text();
        let parsedResult = null;
        
        try {
            parsedResult = JSON.parse(webhookResult);
        } catch (e) {
            parsedResult = { message: webhookResult };
        }

        // ============================================
        // ارسال پاسخ به تلگرام (با Promise.all برای سرعت)
        // ============================================
        const sendPromises = [];
        
        if (parsedResult) {
            if (parsedResult.send_message) {
                sendPromises.push(
                    sendToTelegram('sendMessage', parsedResult.send_message)
                    .catch(e => console.error("❌ sendMessage error:", e.message))
                );
            }
            
            if (parsedResult.send_photo) {
                sendPromises.push(
                    sendToTelegram('sendPhoto', parsedResult.send_photo)
                    .catch(e => console.error("❌ sendPhoto error:", e.message))
                );
            }
            
            if (parsedResult.edit_message_text) {
                sendPromises.push(
                    sendToTelegram('editMessageText', parsedResult.edit_message_text)
                    .catch(e => console.error("❌ editMessage error:", e.message))
                );
            }
            
            if (parsedResult.answer_callback_query) {
                sendPromises.push(
                    sendToTelegram('answerCallbackQuery', parsedResult.answer_callback_query)
                    .catch(e => console.error("❌ callback error:", e.message))
                );
            }
            
            if (parsedResult.method && parsedResult.params) {
                sendPromises.push(
                    sendToTelegram(parsedResult.method, parsedResult.params)
                    .catch(e => console.error(`❌ ${parsedResult.method} error:`, e.message))
                );
            }
        }

        // منتظر ماندن برای ارسال همه پیام‌ها (حداکثر 3 ثانیه)
        if (sendPromises.length > 0) {
            await Promise.race([
                Promise.all(sendPromises),
                new Promise(resolve => setTimeout(resolve, 3000))
            ]);
        }

        // پاسخ سریع به تلگرام
        return new Response(JSON.stringify({ 
            status: "ok",
            message: "Webhook processed successfully"
        }), {
            status: 200,
            headers: { 
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        });

    } catch (error) {
        console.error("❌ Worker error:", error);
        return new Response(JSON.stringify({ 
            status: "ok",
            message: "Error occurred, but acknowledged"
        }), {
            status: 200,
            headers: { 
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        });
    }
}

// ==================== توابع کمکی ====================

async function sendToTelegram(method, params) {
    const url = `${CONFIG.TELEGRAM_API_BASE}${CONFIG.BOT_TOKEN}/${method}`;
    
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Telegram API error (${response.status}): ${errorText}`);
    }

    return await response.json();
}

// ==================== نقطه ورودی ====================
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request));
});
