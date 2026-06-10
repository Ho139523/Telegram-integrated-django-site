// Cloudflare Worker - FINAL VERSION (JSON + Form Fallback)
const AUTH_KEY = "M_r_HUSSEIN2079139523";

const SKIP_HEADERS = {
  host: 1, connection: 1, "content-length": 1,
  "transfer-encoding": 1, "proxy-connection": 1, "proxy-authorization": 1,
  "priority": 1, te: 1,
  "x-forwarded-for": 1, "x-forwarded-host": 1, "x-forwarded-proto": 1,
  "x-forwarded-port": 1, "x-real-ip": 1, "forwarded": 1, "via": 1,
};

const DECOY_HTML = '<!DOCTYPE html><html><head><title>OK</title></head><body><p>OK</p></body></html>';

export default {
  async fetch(request) {
    if (request.method === 'GET') {
      return new Response(DECOY_HTML, { headers: { 'Content-Type': 'text/html' } });
    }
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const body = await request.json();
      if (body.k !== AUTH_KEY) {
        return new Response(JSON.stringify({ e: "unauthorized" }), { 
          status: 401, headers: { 'Content-Type': 'application/json' }
        });
      }
      return await handleSingle(body);
    } catch (err) {
      console.error("Parse error:", err.message);
      return new Response(JSON.stringify({ e: "parse error: " + err.message }), { 
        status: 400, headers: { 'Content-Type': 'application/json' }
      });
    }
  }
};

async function handleSingle(req) {
  try {
    const options = buildOptions(req);
    const response = await fetch(req.u, options);

    const bodyBytes = await response.arrayBuffer();
    const bodyBase64 = arrayBufferToBase64(bodyBytes);
    const headers = Object.fromEntries(response.headers);

    return new Response(JSON.stringify({
      s: response.status,
      h: headers,
      b: bodyBase64
    }), { headers: { 'Content-Type': 'application/json' } });
  } catch (err) {
    console.error("Fetch failed:", err.message, "→", req.u);
    return new Response(JSON.stringify({ e: "fetch failed: " + err.message }), { 
      headers: { 'Content-Type': 'application/json' } 
    });
  }
}

function buildOptions(req) {
  const options = {
    method: (req.m || "GET").toUpperCase(),
    redirect: 'follow',
  };

  // Headers
  if (req.h && typeof req.h === "object") {
    const headers = {};
    for (const [k, v] of Object.entries(req.h)) {
      if (!SKIP_HEADERS[k.toLowerCase()]) headers[k] = v;
    }
    options.headers = headers;
  }

  // === PREFERRED: JSON Body (Best for emojis) ===
  if (req.d && typeof req.d === "object" && Object.keys(req.d).length > 0) {
    options.body = JSON.stringify(req.d);
    if (!options.headers) options.headers = {};
    options.headers['Content-Type'] = 'application/json';
    console.log("✅ JSON sent:", req.d);
  }
  // Fallback: Form data
  else if (req.f && typeof req.f === "object") {
    const formData = new URLSearchParams();
    for (const [key, value] of Object.entries(req.f)) {
      formData.append(key, String(value));
    }
    options.body = formData.toString();
    if (!options.headers) options.headers = {};
    options.headers['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
    console.log("✅ Form sent:", Object.fromEntries(formData));
  }
  // Raw body
  else if (req.b) {
    try {
      const binaryString = atob(req.b);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      options.body = bytes;
      if (req.ct) options.headers['Content-Type'] = req.ct;
    } catch (e) {
      console.error("Base64 error:", e);
    }
  }

  return options;
}

function arrayBufferToBase64(buffer) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
