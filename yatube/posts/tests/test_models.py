from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, SIGNS_OF_TEXT


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        group = PostModelTest.group
        expected_post_name = post.text[:SIGNS_OF_TEXT]
        expected_group_name = group.title
        models_names = [
            (expected_post_name, str(post)), (expected_group_name, str(group))
        ]

        for field, expected_value in models_names:
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = [
            ('text', 'Текст поста'),
            ('pub_date', 'Дата публикации'),
            ('author', 'Автор'),
            ('group', 'Группа')
        ]
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        post = PostModelTest.post
        field_help_texts = [
            ('text', 'Введите текст поста'),
            ('pub_date', 'Дата публикации поста'),
            ('author', 'Автор поста'),
            ('group', 'Группа, к которой будет относиться пост')
        ]
        for field, expected_value in field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
