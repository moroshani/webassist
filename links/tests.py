from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Link


class LinkModelTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.link = Link.objects.create(
            user=self.user, title="Test", url="https://example.com", description="desc"
        )

    def test_link_str(self):
        self.assertEqual(str(self.link), "Test")


class LinkListViewTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser2", password="testpass2")
        self.link = Link.objects.create(
            user=self.user,
            title="Test2",
            url="https://example2.com",
            description="desc2",
        )

    def test_link_list_view_status_code(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"), follow=True)
        self.assertEqual(response.status_code, 200)
