const http = require('http');
const https = require('https');

const WORKER_URL = 'https://telegram-relay.m-r-husseinmohammadi.workers.dev';
const AUTH_KEY = 'M_r_HUSSEIN2079139523';
const PORT = 8085;

async function sendToWorker(targetUrl, method, headers, bodyBuffer) {
    let finalBody = bodyBuffer;
    let finalHeaders = { ...headers };

    const payload = {
        k: AUTH_KEY,
        u: targetUrl,
        m: method,
        h: finalHeaders || {}
    };

    if (!payload.h['user-agent']) {
        payload.h['user-agent'] = 'Mozilla/5.0 (compatible; Telebot-Proxy/1.0)';
    }

    if (finalBody && finalBody.length > 0) {
        payload.b = finalBody.toString('base64');
    }

    console.log(`📤 → Worker: ${method} ${targetUrl.split('/').pop()}`);

    const response = await fetch(WORKER_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (data.e) throw new Error(data.e);

    return {
        status: data.s || 500,
        headers: data.h || {},
        body: data.b ? Buffer.from(data.b, 'base64') : Buffer.alloc(0)
    };
}

// Main HTTP Handler
const server = http.createServer(async (req, res) => {
    console.log(`📥 ${req.method} ${req.url}`);

    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', async () => {
        const bodyBuffer = Buffer.concat(chunks);

        let targetUrl = req.url;
        if (!targetUrl.startsWith('http')) {
            targetUrl = 'https://' + (targetUrl.startsWith('/') ? targetUrl.substring(1) : targetUrl);
        }

        const headers = {};
        for (const [k, v] of Object.entries(req.headers)) {
            if (!['host', 'connection', 'content-length', 'transfer-encoding'].includes(k.toLowerCase())) {
                headers[k] = v;
            }
        }

        try {
            const result = await sendToWorker(targetUrl, req.method, headers, bodyBuffer);
            res.writeHead(result.status, result.headers);
            res.end(result.body);
            console.log(`✅ ${result.status} ${targetUrl.split('/').pop()}`);
        } catch (err) {
            console.error(`❌ ${err.message}`);
            res.writeHead(502);
            res.end('Proxy Error');
        }
    });
});

// Improved CONNECT Handler (Critical Fix)
server.on('connect', (req, clientSocket, head) => {
    console.log(`🔗 CONNECT ${req.url}`);

    const [host] = req.url.split(':');
    clientSocket.write('HTTP/1.1 200 Connection Established\r\n\r\n');

    let buffer = Buffer.from(head);

    clientSocket.on('data', async (chunk) => {
        buffer = Buffer.concat([buffer, chunk]);

        // Try to detect end of headers
        const dataStr = buffer.toString();
        const headerEnd = dataStr.indexOf('\r\n\r\n');

        if (headerEnd !== -1) {
            const fullRequest = buffer;
            const requestLine = dataStr.split('\r\n')[0];
            const parts = requestLine.split(' ');

            if (parts.length >= 2) {
                const method = parts[0];
                const path = parts[1];
                const fullUrl = `https://${host}${path}`;

                // Extract headers (simplified)
                const headers = {};
                const lines = dataStr.split('\r\n');
                for (let i = 1; i < lines.length; i++) {
                    if (lines[i] === '') break;
                    const [key, ...val] = lines[i].split(':');
                    if (key) headers[key.trim().toLowerCase()] = val.join(':').trim();
                }

                const body = buffer.slice(headerEnd + 4);

                try {
                    const result = await sendToWorker(fullUrl, method, headers, body);

                    const statusLine = `HTTP/1.1 ${result.status} OK\r\n`;
                    let resHeaders = '';
                    for (const [k, v] of Object.entries(result.headers)) {
                        if (!['transfer-encoding', 'content-length'].includes(k.toLowerCase())) {
                            resHeaders += `${k}: ${v}\r\n`;
                        }
                    }
                    resHeaders += '\r\n';

                    clientSocket.write(Buffer.from(statusLine + resHeaders));
                    clientSocket.write(result.body);
                    clientSocket.end();
                    console.log(`✅ ${result.status} ${fullUrl.split('/').pop()}`);
                } catch (err) {
                    console.error(`❌ CONNECT error: ${err.message}`);
                    clientSocket.end();
                }
            }
        }
    });

    clientSocket.on('error', err => console.error(`Client socket error: ${err.message}`));
});

server.listen(PORT, '127.0.0.1', () => {
    console.log(`🚀 Telegram Proxy running on http://127.0.0.1:${PORT}`);
});
