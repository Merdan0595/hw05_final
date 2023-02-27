from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post


User = get_user_model()


class CoreViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()

    def test_404_gives_custom_template(self):
        non_existent_id = Post.objects.count() + 1
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': non_existent_id})
        )
        self.assertTemplateUsed(response, 'core/404.html')
