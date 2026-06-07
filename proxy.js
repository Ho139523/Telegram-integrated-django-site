// proxy-v2.js - نسخه بهبود یافته
const http = require('http');
const https = require('https');

const WORKER_URL = 'https://domainfront-relay.m-r-husseinmohammadi.workers.dev';
const AUTH_KEY = 'M_r_HUSSEIN2079139523';
const LOCAL_PORT = 8085;

const server = http.createServer(async (req, res) => {
  console.log(`📥 ${req.method} ${req.url}`);
  
  try {
    // استخراج URL واقعی از درخواست
    // فرمت: http://127.0.0.1:8085/https://example.com/path
    let targetUrl = req.url.substring(1); // حذف slash اول
    
    // اگه با http:// یا https:// شروع نشده بود، اضافه کن
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      targetUrl = 'https://' + targetUrl;
    }
    
    console.log(`🎯 Target: ${targetUrl}`);
    
    // جمع‌آوری body درخواست (برای POST, PUT, etc)
    const bodyBuffer = await collectBody(req);
    
    // ساختن هدرها
    const headers = {};
    for (const [key, value] of Object.entries(req.headers)) {
      // حذف هدرهای مشکل‌ساز
      if (!['host', 'connection', 'content-length'].includes(key.toLowerCase())) {
        headers[key] = value;
      }
    }
    
    // اضافه کردن User-Agent پیش‌فرض اگه نبود
    if (!headers['user-agent']) {
      headers['user-agent'] = 'LocalProxy/1.0';
    }
    
    // آماده‌سازی payload برای Worker
    const workerPayload = {
      k: AUTH_KEY,
      u: targetUrl,
      m: req.method,
      h: headers
    };
    
    // اگه body داریم، به base64 تبدیل کن
    if (bodyBuffer.length > 0) {
      workerPayload.b = bodyBuffer.toString('base64');
      if (headers['content-type']) {
        workerPayload.ct = headers['content-type'];
      }
    }
    
    // ارسال به Worker
    console.log(`🚀 Sending to Worker...`);
    const workerResponse = await fetch(WORKER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workerPayload)
    });
    
    const responseText = await workerResponse.text();
    let responseData;
    
    try {
      responseData = JSON.parse(responseText);
    } catch (e) {
      console.error(`❌ Invalid JSON response: ${responseText.substring(0, 200)}`);
      res.writeHead(502, { 'Content-Type': 'text/plain' });
      res.end(`Proxy Error: Worker returned invalid response`);
      return;
    }
    
    // چک کردن خطا
    if (responseData.e) {
      console.error(`❌ Worker error: ${responseData.e}`);
      res.writeHead(502, { 'Content-Type': 'text/plain' });
      res.end(`Proxy Error: ${responseData.e}`);
      return;
    }
    
    // ارسال پاسخ
    const statusCode = responseData.s || 500;
    const responseHeaders = responseData.h || {};
    const bodyBase64 = responseData.b || '';
    
    // حذف هدرهای مشکل‌ساز
    delete responseHeaders['content-length'];
    delete responseHeaders['transfer-encoding'];
    delete responseHeaders['connection'];
    
    // اضافه کردن هدر CORS برای تست راحت‌تر
    responseHeaders['Access-Control-Allow-Origin'] = '*';
    
    // ارسال هدرها
    res.writeHead(statusCode, responseHeaders);
    
    // دیکد کردن body از base64
    if (bodyBase64) {
      const bodyBuffer2 = Buffer.from(bodyBase64, 'base64');
      res.end(bodyBuffer2);
      console.log(`✅ ${statusCode} - ${bodyBuffer2.length} bytes`);
    } else {
      res.end();
      console.log(`✅ ${statusCode} - empty body`);
    }
    
  } catch (err) {
    console.error(`❌ Proxy error:`, err.message);
    res.writeHead(500, { 'Content-Type': 'text/plain' });
    res.end(`Internal Proxy Error: ${err.message}`);
  }
});

function collectBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

server.listen(LOCAL_PORT, '127.0.0.1', () => {
  console.log(`
╔══════════════════════════════════════════════════════════╗
║     DomainFront Relay - Local Proxy v2                   ║
╠══════════════════════════════════════════════════════════╣
║  ✅ Proxy running on: http://127.0.0.1:${LOCAL_PORT}        ║
║  🚀 Worker: ${WORKER_URL}
║                                                          ║
║  مثال‌های تست:                                           ║
║  curl http://127.0.0.1:${LOCAL_PORT}/api.github.com/zen     ║
║  curl http://127.0.0.1:${LOCAL_PORT}/jsonplaceholder.typicode.com/posts/1
║                                                          ║
╚══════════════════════════════════════════════════════════╝
  `);
});
