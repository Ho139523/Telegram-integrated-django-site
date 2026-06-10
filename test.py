import requests
import base64
import json

def test_via_proxy():
    payload = {
        "chat_id": "5629898030",
        "text": "Proxy Test 👋 Hello!"
    }
    
    print("Sending via local proxy...")
    response = requests.post(
        "http://127.0.0.1:8085/api.telegram.org/bot7777543551:AAHJYYN3VwfC686y1Ir_aYewX1IzUMOlU68/sendMessage",
        data=payload,   # Using form data
        timeout=30
    )
    
    print(f"Proxy Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_via_proxy()
