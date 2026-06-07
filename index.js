// Cloudflare Worker - DomainFront Relay
// جایگزین کد Google Apps Script

const AUTH_KEY = "M_r_HUSSEIN2079139523";
const DIAGNOSTIC_MODE = false;

// حذف بخش Spreadsheet Cache چون Worker از KV یا D1 استفاده می‌کند
// برای کش کردن می‌توانید از KV استور Worker استفاده کنید

const SKIP_HEADERS = {
  host: 1, connection: 1, "content-length": 1,
  "transfer-encoding": 1, "proxy-connection": 1, "proxy-authorization": 1,
  "priority": 1, te: 1,
  "x-forwarded-for": 1, "x-forwarded-host": 1, "x-forwarded-proto": 1,
  "x-forwarded-port": 1, "x-real-ip": 1, "forwarded": 1, "via": 1,
};

const SAFE_REPLAY_METHODS = { GET: 1, HEAD: 1, OPTIONS: 1 };

const DECOY_HTML = '<!DOCTYPE html><html><head><title>Web App</title></head>' +
  '<body><p>The script completed but did not return anything.</p>' +
  '</body></html>';

// هندلر اصلی Worker
export default {
  async fetch(request, env, ctx) {
    // برای GET درخواست
    if (request.method === 'GET') {
      return new Response(DECOY_HTML, {
        headers: { 'Content-Type': 'text/html' }
      });
    }

    // برای POST درخواست
    if (request.method === 'POST') {
      try {
        const body = await request.json();
        
        // بررسی احراز هویت
        if (body.k !== AUTH_KEY) {
          return unauthorizedResponse();
        }

        // حالت Batch
        if (Array.isArray(body.q)) {
          return await handleBatch(body.q);
        }

        // حالت Single
        return await handleSingle(body);
      } catch (err) {
        return unauthorizedResponse();
      }
    }

    return new Response('Method not allowed', { status: 405 });
  }
};

function unauthorizedResponse() {
  if (DIAGNOSTIC_MODE) {
    return new Response(JSON.stringify({ e: "unauthorized" }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  return new Response(DECOY_HTML, {
    headers: { 'Content-Type': 'text/html' }
  });
}

async function handleSingle(req) {
  // اعتبارسنجی URL
  if (!req.u || typeof req.u !== "string" || !req.u.match(/^https?:\/\//i)) {
    return new Response(JSON.stringify({ e: "bad url" }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    const options = buildOptions(req);
    const response = await fetch(req.u, options);
    
    const bodyBytes = await response.arrayBuffer();
    const bodyBase64 = arrayBufferToBase64(bodyBytes);
    
    // استخراج هدرها
    const headers = {};
    response.headers.forEach((value, key) => {
      headers[key] = value;
    });

    return new Response(JSON.stringify({
      s: response.status,
      h: headers,
      b: bodyBase64
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (err) {
    return new Response(JSON.stringify({ e: "fetch failed: " + err.message }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function handleBatch(items) {
  const fetchPromises = [];
  const fetchIndex = [];
  const errorMap = {};

  // آماده‌سازی درخواست‌ها
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    
    if (!item || typeof item !== "object") {
      errorMap[i] = "bad item";
      continue;
    }
    
    if (!item.u || typeof item.u !== "string" || !item.u.match(/^https?:\/\//i)) {
      errorMap[i] = "bad url";
      continue;
    }
    
    try {
      const options = buildOptions(item);
      fetchPromises.push(
        fetch(item.u, options)
          .then(async (resp) => ({
            index: i,
            response: resp,
            error: null
          }))
          .catch((err) => ({
            index: i,
            response: null,
            error: err.message
          }))
      );
      fetchIndex.push(i);
    } catch (buildErr) {
      errorMap[i] = buildErr.message;
    }
  }

  // اجرای موازی همه درخواست‌ها
  const results = await Promise.all(fetchPromises);
  
  // پردازش نتایج
  const finalResults = [];
  for (let i = 0; i < items.length; i++) {
    if (errorMap[i]) {
      finalResults.push({ e: errorMap[i] });
      continue;
    }
    
    const result = results.find(r => r.index === i);
    if (!result || !result.response) {
      finalResults.push({ e: result?.error || "fetch failed" });
    } else {
      const bodyBytes = await result.response.arrayBuffer();
      finalResults.push({
        s: result.response.status,
        h: Object.fromEntries(result.response.headers),
        b: arrayBufferToBase64(bodyBytes)
      });
    }
  }
  
  return new Response(JSON.stringify({ q: finalResults }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

function buildOptions(req) {
  const options = {
    method: (req.m || "GET").toUpperCase(),
    redirect: req.r !== false ? 'follow' : 'manual',
  };
  
  // هدرها
  if (req.h && typeof req.h === "object") {
    const headers = {};
    for (const [k, v] of Object.entries(req.h)) {
      if (!SKIP_HEADERS[k.toLowerCase()]) {
        headers[k] = v;
      }
    }
    options.headers = headers;
  }
  
  // Body
  if (req.b) {
    const binaryString = atob(req.b);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    options.body = bytes;
    
    if (req.ct) {
      if (!options.headers) options.headers = {};
      options.headers['Content-Type'] = req.ct;
    }
  }
  
  return options;
}

// Utility: تبدیل ArrayBuffer به Base64
function arrayBufferToBase64(buffer) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}