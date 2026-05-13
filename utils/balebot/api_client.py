# utils/balebot/api_client.py
import json
import time
import uuid
import hmac
import hashlib
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class APIResponse:
    success: bool
    data: Optional[Dict] = None
    status_code: int = 0
    error: Optional[str] = None

class BaleAPIClient:
    """Async API client for all backend communication"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", secret: str = None):
        self.base_url = base_url
        self.secret = secret or "9cb87c53630243ab6244c20321c00acae9ee896624010ad1b81dd16c89edee91"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _sign_payload(self, body_bytes: bytes) -> tuple:
        """Generate timestamp and HMAC signature for request"""
        ts = str(int(time.time()))
        msg = ts.encode() + b"." + body_bytes
        signature = hmac.new(self.secret.encode(), msg, hashlib.sha256).hexdigest()
        return ts, signature
    
    def _build_headers(self, body_bytes: bytes) -> Dict[str, str]:
        """Build signed headers for API request"""
        ts, sig = self._sign_payload(body_bytes)
        return {
            "X-Bot-Timestamp": ts,
            "X-Bot-Signature": sig,
            "X-Bot-Nonce": str(uuid.uuid4()),
            "Content-Type": "application/json",
        }
    
    # utils/balebot/api_client.py
    async def _request(self, method: str, endpoint: str, payload: Dict = None) -> APIResponse:
        """Make signed request to API endpoint"""
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        if not endpoint.endswith('/'):
            endpoint = endpoint + '/'
        url = f"{self.base_url}{endpoint}"
        body_bytes = json.dumps(payload or {}, separators=(',', ':'), ensure_ascii=False).encode("utf-8")
        headers = self._build_headers(body_bytes)
    
        try:
            if method.upper() == "GET":
                response = await self.client.get(
                    url, 
                    headers=headers, 
                    follow_redirects=False  # ✅ جلوگیری از ریدایرکت
                )
            else:
                response = await self.client.post(
                    url, 
                    headers=headers, 
                    content=body_bytes, 
                    follow_redirects=False  # ✅ جلوگیری از ریدایرکت
                )
    
            data = response.json() if response.text else {}
            return APIResponse(
                success=200 <= response.status_code < 300,
                data=data,
                status_code=response.status_code
            )
        except httpx.TimeoutException:
            return APIResponse(success=False, error="Request timeout", status_code=408)
        except Exception as e:
            return APIResponse(success=False, error=str(e), status_code=500)
                
    
    async def close(self):
        """Close HTTP client session"""
        await self.client.aclose()
