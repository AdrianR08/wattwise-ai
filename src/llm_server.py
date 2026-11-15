import hmac
import json
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.llm import build_messages, forecast_bill_answer

ROOT = Path(__file__).resolve().parents[1]
KEY = ROOT / '.local/llm.key'
BUSY = threading.Lock()
POWER_TOOL = dict(type='function', function=dict(name='predict_power',
    description='Predict power for the hour after the uploaded file ends using observed lag readings. No arguments.',
    parameters=dict(type='object', properties={}, additionalProperties=False)))


def run_power_tool(analysis, arguments):
    if arguments != {}:
        return dict(error='predict_power takes no arguments; readings come from the uploaded file.')
    context = analysis.get('hourly_prediction')
    if not context:
        return dict(error='Upload hourly consumption data before predicting next-hour power.')
    try:
        from src.hourly_model import predict_hourly

        result = predict_hourly(context, analysis.get('timezone', 'America/New_York'), analysis.get('weather'))
        from src.anomalies import forecast_watch
        result['forecast_watch'] = forecast_watch(analysis.get('anomalies'), result['predicted_kw'])
        rate = analysis.get('cost_estimate', {}).get('rate_per_kwh')
        if isinstance(rate, (int, float)) and not isinstance(rate, bool) and 0 <= rate < float('inf'):
            result['estimated_hour_usage_cost'] = round(result['estimated_hourly_kwh'] * rate, 2)
            result['rate_per_kwh'] = rate
        return result
    except (ValueError, KeyError, TypeError) as error:
        return dict(error=str(error))
    except (ImportError, OSError):
        return dict(error='The hourly prediction model is unavailable on the AI server.')


def generate(analysis, question, history):
    messages = build_messages(analysis, question, history)
    direct = forecast_bill_answer(analysis, question)
    if direct:
        return direct
    prediction_requested = bool(re.search(r'\bnext[ -]hour\b|\bpredict(?:ion)?\s+(?:my\s+)?power\b', question, re.I))
    prediction_run = False
    prediction_result = None
    for _ in range(3):
        payload = json.dumps(dict(model='qwen3:4b', messages=messages, tools=[POWER_TOOL], think=True,
            stream=False, options=dict(temperature=.2, num_predict=4096, num_ctx=8192))).encode()
        request = Request('http://127.0.0.1:11434/api/chat', data=payload,
                          headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=120) as response:
            message = json.load(response)['message']
        calls = message.get('tool_calls', [])
        markup = re.search(r'<function_call>\s*(.*?)\s*</function_call>', message.get('content', ''), re.S)
        if not calls and markup:
            function = json.loads(markup.group(1))
            calls = [dict(function=function)]
            message = dict(role='assistant', content='', tool_calls=calls)
        if not calls and prediction_requested and not prediction_run:
            calls = [dict(function=dict(name='predict_power', arguments={}))]
            message = dict(role='assistant', content='', tool_calls=calls)
        if not calls:
            answer = message.get('content', '').strip()
            break
        if len(calls) > 4:
            raise ValueError('Too many tool requests')
        messages.append(message)
        for call in calls:
            function = call['function']
            name = function['name']
            result = (run_power_tool(analysis, function.get('arguments', {}))
                      if name == 'predict_power' else dict(error='Unknown tool'))
            prediction_run = prediction_run or name == 'predict_power'
            if name == 'predict_power' and 'predicted_kw' in result:
                prediction_result = result
            messages.append(dict(role='tool', tool_name=name,
                                 content=json.dumps(result, allow_nan=False)))
    else:
        raise ValueError('Tool request limit reached')
    answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.S).strip()
    if '</think>' in answer:
        answer = answer.rsplit('</think>', 1)[-1].strip()
    if not answer or '<think>' in answer:
        raise ValueError('Empty model answer')
    if prediction_result and prediction_result.get('model'):
        model = prediction_result['model']
        label = {'RandomForest': 'Random Forest', 'ExtraTrees': 'Extra Trees',
                 'HistGradientBoosting': 'Histogram Gradient Boosting', 'Ridge': 'Ridge Regression'}.get(model, model)
        weather = 'with weather' if prediction_result.get('weather_used') else 'without weather'
        answer += f'\n\n*Model used: {label} ({weather}).*'
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
