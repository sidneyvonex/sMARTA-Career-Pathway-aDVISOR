import json
from django.test import SimpleTestCase, Client


class HealthCheckTest(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_health_returns_200(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)

    def test_health_returns_json_with_status_ok(self):
        response = self.client.get('/health/')
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')

    def test_health_returns_version(self):
        response = self.client.get('/health/')
        data = json.loads(response.content)
        self.assertIn('version', data)
        self.assertIsInstance(data['version'], str)

    def test_health_allows_unauthenticated_access(self):
        response = self.client.get('/health/')
        self.assertNotEqual(response.status_code, 401)
        self.assertNotEqual(response.status_code, 403)
