from django.test import SimpleTestCase
from rest_framework.exceptions import NotFound
from config.exceptions import custom_exception_handler


class ExceptionHandlerTest(SimpleTestCase):
    def test_drf_exception_returns_envelope(self):
        exc = NotFound("Resource not found")
        context = {}
        response = custom_exception_handler(exc, context)
        self.assertIsNotNone(response)
        self.assertIn('data', response.data)
        self.assertIn('error', response.data)
        self.assertIn('message', response.data)
        self.assertIsNone(response.data['data'])
        self.assertTrue(response.data['error'])

    def test_non_drf_exception_returns_none(self):
        exc = ValueError("Not a DRF exception")
        context = {}
        response = custom_exception_handler(exc, context)
        self.assertIsNone(response)
