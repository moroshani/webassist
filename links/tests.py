from django.test import TestCase
from .models import Link
from django.urls import reverse

class LinkModelTest(TestCase):
    def setUp(self):
        self.link = Link.objects.create(title="Test", url="https://example.com", description="desc")

    def test_link_str(self):
        self.assertEqual(str(self.link), "Test")

class LinkListViewTest(TestCase):
    def test_link_list_view_status_code(self):
        response = self.client.get(reverse('link_list'))
        self.assertEqual(response.status_code, 200) 