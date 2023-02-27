from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostURLTests.user,
            text='Тестовый пост',
            group=PostURLTests.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_response_guest(self):
        exists_at_desired_location = [
            ('/', HTTPStatus.OK),
            (f'/group/{PostURLTests.group.slug}/', HTTPStatus.OK),
            (f'/profile/{PostURLTests.user.username}/', HTTPStatus.OK),
            (f'/posts/{PostURLTests.post.pk}/', HTTPStatus.OK),
            ('/unexisting_page/', HTTPStatus.NOT_FOUND)
        ]
        for adress, code in exists_at_desired_location:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_urls_response_authorized_client_without_edit(self):
        exists_at_desired_location = [
            ('/', HTTPStatus.OK),
            (f'/group/{PostURLTests.group.slug}/', HTTPStatus.OK),
            (f'/profile/{PostURLTests.user.username}/', HTTPStatus.OK),
            (f'/posts/{PostURLTests.post.pk}/', HTTPStatus.OK),
            ('/create/', HTTPStatus.OK),
            ('/unexisting_page/', HTTPStatus.NOT_FOUND)
        ]
        for adress, code in exists_at_desired_location:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_urls_response_authorized_client_with_edit(self):
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        template_url_names = [
            ('/', 'posts/index.html'),
            (f'/group/{PostURLTests.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{PostURLTests.user.username}/', 'posts/profile.html'),
            (f'/posts/{PostURLTests.post.pk}/', 'posts/post_detail.html'),
            (f'/posts/{PostURLTests.post.pk}/edit/', 'posts/create_post.html'),
            ('/create/', 'posts/create_post.html')
        ]
        for adress, template in template_url_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
