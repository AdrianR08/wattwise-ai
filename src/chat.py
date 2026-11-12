import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError

import streamlit as st

from src.llm import ask


def render_chat(analysis, electricity_rate):
    st.subheader('✦ Ask WattWise')
    if analysis is None:
        st.info('Upload a valid consumption file before asking a question.')
        return
    context = dict(analysis)
    context['cost_estimate'] = dict(rate_per_kwh=electricity_rate, currency='USD',
        observed_usage_cost=round(analysis['summary']['observed_kwh'] * electricity_rate, 2),
        forecast_usage_cost=round(analysis['forecast']['predicted_kwh'] * electricity_rate, 2)
        if analysis['forecast']['status'] == 'available' else None,
        excludes='Fixed fees and taxes')
    signature = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()
    if st.session_state.get('chat_signature') != signature:
        st.session_state.chat_signature = signature
        st.session_state.chat_messages = []
    try:
        config = dict(st.secrets.get('wattwise_llm', {}))
    except FileNotFoundError:
        config = {}
    url = config.get('url') or os.environ.get('WATTWISE_LLM_URL', 'http://127.0.0.1:8765')
    token = config.get('token') or os.environ.get('WATTWISE_LLM_TOKEN', '')
    local_key = Path(__file__).resolve().parents[1] / '.local/llm.key'
    if not token and url == 'http://127.0.0.1:8765' and local_key.exists():
        token = local_key.read_text(encoding='utf-8').strip()
    if not token:
        st.info('The AI assistant is not connected yet. Consumption analysis and forecasting remain available.')
        return
    st.caption('Questions and your consumption summary are processed by WattWise’s locally hosted AI. It explains the analysis; it cannot diagnose appliance faults.')
    for message in st.session_state.chat_messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    question = st.chat_input('Ask about your consumption, unusual days, or forecast', max_chars=2000)
    if question:
        with st.chat_message('user'):
            st.write(question)
        try:
            with st.spinner('Reviewing your consumption…'):
                answer = ask(context, question, st.session_state.chat_messages, url=url, token=token)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError):
            st.warning('The AI is busy or offline. Please try again shortly. Your analysis is still available.')
            return
        st.session_state.chat_messages.extend([dict(role='user', content=question), dict(role='assistant', content=answer)])
        st.session_state.chat_messages = st.session_state.chat_messages[-20:]
        with st.chat_message('assistant'):
            st.markdown(answer)
