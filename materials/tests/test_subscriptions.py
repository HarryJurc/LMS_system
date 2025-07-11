from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from materials.models import Course, Subscription
from django.urls import reverse

User = get_user_model()

class SubscriptionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@example.com', password='pass')
        self.course = Course.objects.create(title='Django Course', owner=self.user)

    def test_toggle_subscription(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('course-subscribe')
        data = {'course_id': self.course.id}

        response = self.client.post(url, data)
        self.assertEqual(response.data['message'], 'подписка добавлена')

        response = self.client.post(url, data)
        self.assertEqual(response.data['message'], 'подписка удалена')

    def test_unauthenticated_access(self):
        url = reverse('course-subscribe')
        data = {'course_id': self.course.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 401)
