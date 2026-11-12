import hmac
import json
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.llm import build_messages

ROOT = Path(__file__).resolve().parents[1]
KEY = ROOT / '.local/llm.key'
BUSY = threading.Lock()


def generate(analysis, question, history):
    messages = build_messages(analysis, question, history)
    payload = json.dumps(dict(model='qwen3:4b', messages=messages, think=True,
        stream=False, options=dict(temperature=.2, num_predict=4096, num_ctx=8192))).encode()
    request = Request('http://127.0.0.1:11434/api/chat', data=payload,
                      headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=120) as response:
        answer = json.load(response)['message']['content'].strip()
    answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.S).strip()
    if not answer or '<think>' in answer:
        raise ValueError('Empty model answer')
    return answer


def make_handler(token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, content):
            body = json.dumps(content).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != '/ask':
                return self.reply(404, {'error': 'Not found'})
            if not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token):
                return self.reply(401, {'error': 'Unauthorized'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                return self.reply(400, {'error': 'Invalid request'})
            if not 0 < length <= 100_000:
                return self.reply(413, {'error': 'Request too large or empty'})
            if not BUSY.acquire(blocking=False):
                return self.reply(429, {'error': 'Model is busy; try again shortly'})
            try:
                self.connection.settimeout(150)
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict) or not isinstance(data.get('analysis'), dict) or not isinstance(data.get('history', []), list):
                    raise ValueError('Invalid request')
                self.reply(200, {'answer': generate(data['analysis'], data.get('question'), data.get('history', []))})
            except (ValueError, KeyError, TypeError, AttributeError):
                self.reply(400, {'error': 'Invalid question or analysis'})
            except (URLError, TimeoutError, OSError):
                self.reply(503, {'error': 'The local model is unavailable'})
            finally:
                BUSY.release()
    return Handler


def main():
    KEY.parent.mkdir(exist_ok=True)
    if not KEY.exists():
        KEY.write_text(secrets.token_urlsafe(32), encoding='utf-8')
    token = KEY.read_text(encoding='utf-8').strip()
    if len(token) < 32:
        raise ValueError('Local access key is invalid')
    server = ThreadingHTTPServer(('127.0.0.1', 8765), make_handler(token))
    server.daemon_threads = True
    print('WattWise model bridge is ready on localhost:8765.', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
