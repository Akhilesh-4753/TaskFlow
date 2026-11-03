"""
Tests for Chatbot App and Centralized AI Integration.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ai.prompts import (
    load_core_instructions,
    get_chatbot_system_prompt,
    get_task_suggestion_prompt,
    get_learning_roadmap_prompt,
    get_technical_assistance_prompt,
)
from ai.services import (
    generate_chat_response,
    generate_task_suggestion,
    generate_learning_roadmap,
    generate_technical_assistance,
    is_groq_configured,
)


class CentralizedAIPromptsAndServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='mentor_user', password='Password123!')

    def test_core_instructions_loaded_dynamically(self):
        """Verify ai_instructions.md is loaded with key rules."""
        instructions = load_core_instructions()
        self.assertIn("TaskFlow AI", instructions)
        self.assertIn("Beginner Level", instructions)
        self.assertIn("Intermediate Level", instructions)
        self.assertIn("Advanced Level", instructions)
        self.assertIn("Task Generation Guidelines", instructions)

    def test_chatbot_system_prompt_includes_user_context(self):
        """Verify system prompt dynamically injects user info when user is authenticated."""
        prompt_with_user = get_chatbot_system_prompt(user=self.user)
        self.assertIn("mentor_user", prompt_with_user)
        self.assertIn("Pending Tasks", prompt_with_user)

        prompt_without_user = get_chatbot_system_prompt(user=None)
        self.assertNotIn("mentor_user", prompt_without_user)

    def test_task_suggestion_prompt_structure(self):
        """Verify task suggestion prompt configures single-sentence actionable output."""
        messages = get_task_suggestion_prompt("JavaScript")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['role'], 'system')
        self.assertIn("Task Generation", messages[0]['content'])
        self.assertEqual(messages[1]['role'], 'user')
        self.assertIn("JavaScript", messages[1]['content'])

    def test_learning_roadmap_prompt_structure(self):
        """Verify learning roadmap prompt includes 3-level roadmap requirements."""
        messages = get_learning_roadmap_prompt("Django")
        self.assertEqual(len(messages), 2)
        self.assertIn("Learning Roadmap", messages[0]['content'])
        self.assertIn("Django", messages[1]['content'])

    def test_technical_assistance_prompt_structure(self):
        """Verify technical assistance prompt guides step-by-step problem solving."""
        messages = get_technical_assistance_prompt("How to create Django REST API?")
        self.assertEqual(len(messages), 2)
        self.assertIn("Technical Assistance", messages[0]['content'])
        self.assertIn("REST API", messages[1]['content'])

    @patch('requests.post')
    def test_generate_task_suggestion_cleans_output(self, mock_post):
        """Verify task suggestion strips quotes and prefixes."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'choices': [{
                'message': {
                    'content': '"Practice JavaScript variables, data types, operators, and basic functions by writing simple programs."'
                }
            }]
        }
        mock_post.return_value = mock_resp

        with patch('ai.services.is_groq_configured', return_value=True):
            res = generate_task_suggestion("JavaScript")
            self.assertTrue(res['success'])
            self.assertEqual(
                res['description'],
                'Practice JavaScript variables, data types, operators, and basic functions by writing simple programs.'
            )
            self.assertEqual(res['title'], 'Practice Javascript')

    @patch('requests.post')
    def test_generate_learning_roadmap_success(self, mock_post):
        """Verify 3-level roadmap generation succeeds."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'choices': [{
                'message': {
                    'content': '### Beginner Level\n- Syntax\n### Intermediate Level\n- Views\n### Advanced Level\n- Caching'
                }
            }]
        }
        mock_post.return_value = mock_resp

        with patch('ai.services.is_groq_configured', return_value=True):
            res = generate_learning_roadmap("Django")
            self.assertTrue(res['success'])
            self.assertIn('Beginner Level', res['roadmap'])
            self.assertIn('Intermediate Level', res['roadmap'])
            self.assertIn('Advanced Level', res['roadmap'])


class ChatbotViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='chatuser', password='Password123!')

    def test_unauthenticated_chat_rejected(self):
        """Unauthenticated access redirects to login."""
        res = self.client.post(reverse('chatbot:chat'), data=json.dumps({'message': 'Hi'}), content_type='application/json')
        self.assertEqual(res.status_code, 302)

    def test_empty_message_returns_400(self):
        self.client.login(username='chatuser', password='Password123!')
        res = self.client.post(reverse('chatbot:chat'), data=json.dumps({'message': '   '}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()['success'])

    @patch('requests.post')
    def test_chatbot_successful_response(self, mock_post):
        """Chatbot view returns markdown-formatted assistant response."""
        self.client.login(username='chatuser', password='Password123!')
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'choices': [{
                'message': {
                    'content': '### 1. Beginner Level\nLearn basic syntax and variables.'
                }
            }]
        }
        mock_post.return_value = mock_resp

        with patch('ai.services.is_groq_configured', return_value=True):
            res = self.client.post(
                reverse('chatbot:chat'),
                data=json.dumps({'message': 'How to learn Python?'}),
                content_type='application/json'
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data['success'])
            self.assertIn('Beginner Level', data['response'])

    def test_suggest_task_from_tasks_view(self):
        """Verify tasks:task_suggest endpoint operates with the centralized AI service."""
        self.client.login(username='chatuser', password='Password123!')
        with patch('ai.services.is_groq_configured', return_value=True), \
             patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'choices': [{
                    'message': {
                        'content': 'Build a basic Django application with URL routing, function-based views, and HTML templates.'
                    }
                }]
            }
            mock_post.return_value = mock_resp

            res = self.client.post(
                reverse('tasks:task_suggest'),
                data=json.dumps({'topic': 'Django'}),
                content_type='application/json'
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data['success'])
            self.assertIn('Build a basic Django application', data['description'])

