import shutil
import tempfile
from random import randint

from django import forms
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, Group, Follow
from ..utils import POSTS_ON_PAGE

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class YatubePagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=YatubePagesTests.user,
            text='Тестовый пост',
            group=YatubePagesTests.group,
            image=uploaded)

        cls.form_fields = [
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
            ('image', forms.fields.ImageField),
        ]

        cls.object_list_and_page_names = [
            (reverse('posts:index'), 'page_obj'),
            (reverse('posts:group_list', kwargs={
                'slug': YatubePagesTests.group.slug}), 'page_obj'),
            (reverse('posts:profile', kwargs={
                'username': YatubePagesTests.user.username}), 'page_obj'),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_posts_pages_uses_correct_template(self):
        """Проверяем, что вызывается соответствующий шаблон"""
        template_pages_names = [
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:group_list', kwargs={
                'slug': YatubePagesTests.group.slug}),
                'posts/group_list.html'),
            (reverse('posts:profile', kwargs={
                'username': YatubePagesTests.user.username}),
                'posts/profile.html'),
            (reverse('posts:post_detail', kwargs={
                'post_id': YatubePagesTests.post.pk}),
                'posts/post_detail.html'),
            (reverse('posts:post_create'),
                'posts/create_post.html'),
            (reverse('posts:post_edit', kwargs={
                'post_id': YatubePagesTests.post.pk}),
                'posts/create_post.html'),
        ]
        for reverse_name, template in template_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def first_objects_of_page_obj(value, self):
        first_object = value.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, YatubePagesTests.post.author)
        self.assertEqual(post_text_0, YatubePagesTests.post.text)
        self.assertEqual(post_group_0, YatubePagesTests.post.group)
        self.assertEqual(post_image_0, YatubePagesTests.post.image)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('posts:index'))
        YatubePagesTests.first_objects_of_page_obj(response, self)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('posts:group_list', kwargs={
            'slug': YatubePagesTests.group.slug
        }))
        YatubePagesTests.first_objects_of_page_obj(response, self)
        self.assertEqual(response.context.get('group').title,
                         YatubePagesTests.group.title)
        self.assertEqual(response.context.get('group').slug,
                         YatubePagesTests.group.slug)
        self.assertEqual(response.context.get('group').description,
                         YatubePagesTests.group.description)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('posts:profile', kwargs={
            'username': YatubePagesTests.user.username
        }))
        YatubePagesTests.first_objects_of_page_obj(response, self)
        self.assertEqual(response.context.get('author').username,
                         str(YatubePagesTests.user.username))

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('posts:post_detail', kwargs={
            'post_id': YatubePagesTests.post.pk
        }))
        self.assertEqual(response.context.get('post').image,
                         YatubePagesTests.post.image)
        self.assertEqual(response.context.get('post').pk,
                         YatubePagesTests.post.pk)

    def test_post_create_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in self.form_fields:
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': YatubePagesTests.post.pk}))
        for value, expected in self.form_fields:
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context.get('post').pk,
                         YatubePagesTests.post.pk)
        self.assertEqual(response.context.get('is_edit'), True)

    def test_post_group_not_in_another_group(self):
        """Проверка, что пост не попал не в ту группу"""
        another_group = Group.objects.create(
            title='TMNT',
            slug='turtles',
            description='Черепашки ниндзя'
        )
        response = self.guest_client.get(reverse('posts:group_list', kwargs={
            'slug': another_group.slug
        }))
        self.assertNotIn(YatubePagesTests.post.group,
                         response.context['page_obj'])

    def test_cache_page_index(self):
        post_for_testing_cache = Post.objects.create(
            author=YatubePagesTests.user,
            text='Кеш или кэш?',
        )
        response = self.guest_client.get(
            reverse('posts:index')
        )
        post_for_testing_cache.delete()
        response_after_delete = self.guest_client.get(
            reverse('posts:index')
        )
        self.assertEqual(response.content, response_after_delete.content)
        cache.clear()
        response_after_delete = self.guest_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(response.content, response_after_delete.content)

    def test_profile_follow(self):
        another_user = User.objects.create_user(username='kuku')
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': another_user.username}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_profile_unfollow(self):
        another_user = User.objects.create_user(username='kuku')
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': another_user.username}))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_index(self):
        another_user = User.objects.create_user(username='kuku')
        another_post = Post.objects.create(
            author=another_user,
            text='Эназер текст',
            group=self.group
        )
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': another_user.username}))
        response = self.authorized_client.get(reverse(
            'posts:follow_index'
        ))
        self.assertEqual(response.context.get('post').text, another_post.text)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.posts_on_second_page = randint(1, POSTS_ON_PAGE)
        cls.number_of_posts = (
            PaginatorTests.posts_on_second_page + POSTS_ON_PAGE
        )
        cls.posts = [
            Post(
                author=PaginatorTests.user,
                text='Тестовый пост',
                group=PaginatorTests.group
            )
            for i in range(PaginatorTests.number_of_posts)
        ]
        Post.objects.bulk_create(PaginatorTests.posts)

        cls.object_list_and_page_names = [
            (reverse('posts:index'), 'page_obj'),
            (reverse('posts:group_list', kwargs={
                'slug': PaginatorTests.group.slug}), 'page_obj'),
            (reverse('posts:profile', kwargs={
                'username': PaginatorTests.user.username}), 'page_obj'),
        ]

    def setUp(self):
        self.guest_client = Client()

    def test_first_page(self):
        for page_name, object_list in self.object_list_and_page_names:
            with self.subTest(page_name=page_name):
                response = self.guest_client.get(page_name)
                self.assertEqual(len(response.context[(object_list)]),
                                 POSTS_ON_PAGE)

    def test_second_page(self):
        for page_name, object_list in self.object_list_and_page_names:
            with self.subTest(page_name=page_name):
                response = self.guest_client.get((page_name) + '?page=2')
                self.assertEqual(len(response.context[object_list]),
                                 PaginatorTests.posts_on_second_page)
