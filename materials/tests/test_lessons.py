from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from materials.models import Course, Lesson, Subscription
from rest_framework import status
from django.urls import reverse

User = get_user_model()

class LessonCRUDTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(email='author@example.com', password='pass')
        self.other_user = User.objects.create_user(email='user2@example.com', password='pass')

        self.course = Course.objects.create(title='Test Course', owner=self.author)
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            course=self.course,
            video_url='https://youtube.com/video1',
            owner=self.author
        )

    def test_create_lesson_authorized(self):
        self.client.force_authenticate(user=self.author)
        url = reverse('lesson-create')
        data = {
            'title': 'New Lesson',
            'course': self.course.id,
            'video_url': 'https://youtube.com/video2',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_lesson_not_authorized(self):
        url = reverse('lesson-create')
        data = {
            'title': 'New Lesson',
            'course': self.course.id,
            'video_url': 'https://youtube.com/video2',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_lesson_owner(self):
        self.client.force_authenticate(user=self.author)
        url = reverse('lesson-update', args=[self.lesson.id])
        data = {'title': 'Updated Lesson'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_lesson_other_user(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse('lesson-update', args=[self.lesson.id])
        data = {'title': 'Hacked'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_lesson_owner(self):
        self.client.force_authenticate(user=self.author)
        url = reverse('lesson-delete', args=[self.lesson.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_lesson_other_user(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse('lesson-delete', args=[self.lesson.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
