import os
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class ChatTests(unittest.TestCase):
    def test_answer_and_new_upload_reset(self):
        source = '''
import streamlit as st
from src.chat import render_chat
total = st.number_input('Test consumption', value=123)
render_chat(dict(summary=dict(observed_kwh=total), forecast=dict(status='unavailable')), .15)
'''
        with patch.dict(os.environ, WATTWISE_LLM_TOKEN='test-key'), patch('src.chat.ask', return_value='You used 123 kWh.') as ask:
            app = AppTest.from_string(source).run()
            app.chat_input[0].set_value('How much did I use?').run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state['chat_messages']), 2)
            ask.assert_called_once()
            app.number_input[0].set_value(456).run()
            self.assertEqual(app.session_state['chat_messages'], [])
