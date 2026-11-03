import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class AssistantTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='aiuser', password='Password123!')

    def test_unauthenticated_chat_rejected(self):
        response = self.client.post(
            reverse('assistant:chat'),
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

    def test_empty_chat_message(self):
        self.client.login(username='aiuser', password='Password123!')
        response = self.client.post(
            reverse('assistant:chat'),
            data=json.dumps({'message': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_suggest_title(self):
        self.client.login(username='aiuser', password='Password123!')
        response = self.client.post(
            reverse('assistant:suggest'),
            data=json.dumps({'title': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_suggest_when_groq_not_configured(self):
        """When GROQ_API_KEY is not configured, it should return 503 without crashing."""
        self.client.login(username='aiuser', password='Password123!')
        with patch('assistant.services.is_groq_configured', return_value=False):
            response = self.client.post(
                reverse('assistant:suggest'),
                data=json.dumps({'title': 'Build login page'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertFalse(data['success'])
            self.assertIn('not configured', data['error'])

    @patch('requests.post')
    def test_successful_ai_suggestion(self, mock_post):
        self.client.login(username='aiuser', password='Password123!')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': 'Implement authentication views with CSRF tokens and secure session management.'
                }
            }]
        }
        mock_post.return_value = mock_response

        with patch('assistant.services.is_groq_configured', return_value=True):
            response = self.client.post(
                reverse('assistant:suggest'),
                data=json.dumps({'title': 'Build auth views'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertIn('Implement authentication views', data['description'])

    def test_chat_when_groq_not_configured(self):
        """When GROQ_API_KEY is missing/empty, chat endpoint returns 503 with friendly message."""
        self.client.login(username='aiuser', password='Password123!')
        with patch('assistant.services.is_groq_configured', return_value=False):
            response = self.client.post(
                reverse('assistant:chat'),
                data=json.dumps({'message': 'How can I prioritize my tasks?'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertFalse(data['success'])
            self.assertIn('not configured', data['error'])

    @patch('requests.post')
    def test_successful_ai_chat(self, mock_post):
        """When Groq API succeeds, chat returns 200 with the assistant response."""
        self.client.login(username='aiuser', password='Password123!')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': 'Focus on your highest priority task first.'
                }
            }]
        }
        mock_post.return_value = mock_response

        with patch('assistant.services.is_groq_configured', return_value=True):
            response = self.client.post(
                reverse('assistant:chat'),
                data=json.dumps({'message': 'What should I do first?'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['response'], 'Focus on your highest priority task first.')

    @patch('requests.post')
    def test_groq_api_401_handling(self, mock_post):
        """When Groq returns 401 Unauthorized, returns clear error."""
        self.client.login(username='aiuser', password='Password123!')
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with patch('assistant.services.is_groq_configured', return_value=True):
            response = self.client.post(
                reverse('assistant:chat'),
                data=json.dumps({'message': 'Hello'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertFalse(data['success'])
            self.assertIn('authentication failed', data['error'].lower())


