import requests
import json
from typing import Dict, List, Optional, Union, Iterator
import time

class QwenOllamaClient:
    """
    کلاس پایتون برای تعامل با مدل‌های Qwen از طریق Ollama
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        default_model: str = "qwen2.5:0.5B"
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.default_model = default_model
        self.headers = {'Content-Type': 'application/json'}
        self._test_connection()

    def _test_connection(self):
        """بررسی اتصال به سرور Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                print("✅ اتصال به سرور Ollama برقرار شد")
                model_names = [m['name'] for m in models]
                print(f"📋 مدل‌های موجود: {model_names}")
                
                # بررسی مدل پیش‌فرض
                if self.default_model not in model_names and models:
                    print(f"⚠️ مدل پیش‌فرض '{self.default_model}' یافت نشد")
                    self.default_model = models[0]['name']
                    print(f"   مدل جدید: {self.default_model}")
        except Exception as e:
            print(f"❌ خطا در اتصال: {e}")

    def _make_request(self, endpoint: str, method: str = "POST", data: Optional[Dict] = None) -> Dict:
        """ارسال درخواست HTTP"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=data, headers=self.headers, timeout=self.timeout)
            else:
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 404:
                # تست آدرس جایگزین
                if endpoint.startswith("/api/"):
                    alt_endpoint = endpoint[5:]
                    print(f"⚠️ تست آدرس جایگزین: {alt_endpoint}")
                    return self._make_request(alt_endpoint, method, data)
                raise Exception(f"آدرس {endpoint} یافت نشد (404)")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"اتصال به Ollama برقرار نیست. 'ollama serve' را اجرا کنید.")
        except Exception as e:
            raise Exception(f"خطا در درخواست API: {str(e)}")

    def list_models(self) -> List[Dict]:
        """لیست مدل‌های موجود"""
        try:
            response = self._make_request("/api/tags", "GET")
            return response.get('models', [])
        except:
            return []

    def generate(
        self,
        prompt: str,
        model: str = None,
        system: Optional[str] = None,
        options: Optional[Dict] = None,
        stream: bool = False
    ) -> Union[Dict, Iterator[str]]:
        """
        تولید پاسخ برای یک متن ورودی
        """
        if model is None:
            model = self.default_model

        data = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }

        if system:
            data["system"] = system

        if options is None:
            options = {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 1500,
                "repeat_penalty": 1.1,
                "num_ctx": 4096
            }

        data["options"] = options

        if stream:
            return self._stream_generate(data)
        else:
            return self._make_request("/api/generate", data=data)

    def _stream_generate(self, data: Dict) -> Iterator[str]:
        """
        تولید پاسخ استریمی - نسخه اصلاح شده
        """
        url = f"{self.base_url}/api/generate"
        
        try:
            with requests.post(
                url,
                json=data,
                headers=self.headers,
                timeout=300,
                stream=True
            ) as response:
                response.raise_for_status()
                
                buffer = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        try:
                            json_line = json.loads(line)
                            if 'response' in json_line:
                                chunk = json_line['response']
                                buffer += chunk
                                # ارسال هنگامی که جمله کامل شد
                                if chunk.endswith(('.', '!', '?', '،', '؛', '\n')) or len(buffer) > 50:
                                    yield buffer
                                    buffer = ""
                        except:
                            continue
                
                if buffer:
                    yield buffer
                    
        except requests.exceptions.Timeout:
            yield "⏱️ پاسخ به دلیل محدودیت زمان قطع شد."
        except Exception as e:
            yield f"⚠️ خطا در استریم: {str(e)[:100]}"

    def simple_generate(self, prompt: str, model: str = None, max_tokens: int = 800) -> str:
        """
        روش ساده برای دریافت پاسخ
        """
        if model is None:
            model = self.default_model
            
        try:
            options = {
                "temperature": 0.7,
                "num_predict": max_tokens,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
            
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": options
            }
            
            result = self._make_request("/api/generate", data=data)
            return result.get('response', 'پاسخی دریافت نشد')
            
        except Exception as e:
            return f"خطا: {str(e)}"

    def ask(self, question: str, model: str = None, max_length: int = 1500) -> str:
        """متد ساده برای پرسیدن سوال"""
        try:
            response = self.simple_generate(question, model, 500)
            
            if len(response) > max_length:
                response = response[:max_length] + "..."
                
            return response
            
        except Exception as e:
            return f"خطا: {str(e)}"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        options: Optional[Dict] = None,
        stream: bool = False
    ) -> Union[Dict, Iterator[str]]:
        """چت با تاریخچه مکالمه"""
        if model is None:
            model = self.default_model
            
        data = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        if options:
            data["options"] = options
            
        if stream:
            return self._stream_chat(data)
        else:
            return self._make_request("/api/chat", data=data)

    def _stream_chat(self, data: Dict) -> Iterator[str]:
        """استریم چت"""
        url = f"{self.base_url}/api/chat"
        
        try:
            with requests.post(
                url,
                json=data,
                headers=self.headers,
                timeout=300,
                stream=True
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        try:
                            json_line = json.loads(line)
                            if 'message' in json_line and 'content' in json_line['message']:
                                yield json_line['message']['content']
                        except:
                            continue
                            
        except Exception as e:
            yield f"خطا در چت استریمی: {str(e)}"

    def get_model_info(self, model_name: str = None) -> Dict:
        """دریافت اطلاعات مدل"""
        if model_name is None:
            model_name = self.default_model
            
        data = {"name": model_name}
        return self._make_request("/api/show", data=data)


# کلاس ربات چت اصلاح شده
class QwenChatBot:
    """ربات چت برای مکالمه‌های پیوسته"""
    
    def __init__(
        self,
        model: str = "qwen2.5:0.5B",
        system_prompt: str = "تو یک دستیار هوشمند فارسی‌زبان هستی. پاسخ‌هایت را به زبان فارسی بده."
    ):
        self.client = QwenOllamaClient(default_model=model)
        self.model = model
        self.system_prompt = system_prompt
        self.conversations = {}
        
    def chat(self, message: str, chat_id: str = "default", use_history: bool = True) -> str:
        """ارسال پیام و دریافت پاسخ"""
        try:
            if not use_history or chat_id not in self.conversations:
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message}
                ]
            else:
                messages = self.conversations[chat_id]
                messages.append({"role": "user", "content": message})
                
                if len(messages) > 11:
                    messages = [messages[0]] + messages[-10:]
            
            result = self.client.chat(messages=messages)
            response = result['message']['content']
            
            if use_history:
                if chat_id not in self.conversations:
                    self.conversations[chat_id] = messages
                self.conversations[chat_id].append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            return f"⚠️ خطا: {str(e)}"
    
    def clear_history(self, chat_id: str = "default"):
        """پاک کردن تاریخچه"""
        if chat_id in self.conversations:
            del self.conversations[chat_id]
    
    def get_history(self, chat_id: str = "default") -> List[Dict[str, str]]:
        """دریافت تاریخچه"""
        return self.conversations.get(chat_id, []).copy()


# توابع تست
def test_simple_usage():
    """تست استفاده ساده"""
    print("🔧 تست استفاده ساده")
    print("=" * 50)
    
    client = QwenOllamaClient()
    
    models = client.list_models()
    print(f"مدل‌های موجود: {[m['name'] for m in models]}")
    
    response = client.ask("سلام! حالت چطوره؟")
    print(f"پاسخ: {response}")
    
    return client

def test_chat_bot():
    """تست ربات چت"""
    print("\n🤖 تست ربات چت")
    print("=" * 50)
    
    bot = QwenChatBot(
        model="my-qwen:latest",
        system_prompt="تو یک دستیار فارسی‌زبان مفید هستی."
    )
    
    questions = [
        "سلام، اسمت چیه؟",
        "چطور می‌تونم پایتون یاد بگیرم؟"
    ]
    
    for question in questions:
        print(f"\nمن: {question}")
        response = bot.chat(question, chat_id="test")
        print(f"ربات: {response}")

if __name__ == "__main__":
    print("🧪 اجرای تست‌ها")
    print("=" * 60)
    
    test_simple_usage()
    test_chat_bot()
    
    print("\n✅ تست‌ها کامل شدند!")
