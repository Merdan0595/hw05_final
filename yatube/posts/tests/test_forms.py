import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from ..models import Post, Group, Comment


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='auth')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

        cls.comment_form_data = {
            'text': 'Комментарий'
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

        self.post = Post.objects.create(
            author=PostFormTests.user,
            text='Тестовый пост',
            group=PostFormTests.group,
        )

        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

        self.form_data = {
            'text': 'Новый текст',
            'group': PostFormTests.group.id,
            'image': self.uploaded,
        }

    def test_create_post(self):
        "Валидная форма создает новый пост"
        posts_count = Post.objects.count()

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )

        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.post.author}))

        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_guest_cant_create_post(self):
        posts_count = Post.objects.count()

        self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit(self):
        "Проверяет изменение поста с определенным ID в базе данных"
        posts_count = Post.objects.count()

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id
            }),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)

        self.assertTrue(Post.objects.filter(
            text=self.form_data['text'],
            group=self.form_data['group'],
            image=f'posts/{self.uploaded.name}'
        ).exists())

    def test_user_cant_edit_another_post(self):
        another_user = User.objects.create_user(username='kuku')

        another_post = Post.objects.create(
            author=another_user,
            text='Текст, который не изменить',
            group=PostFormTests.group,
        )

        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': another_post.id
            }),
            data=self.form_data,
            follow=True
        )
        another_post.refresh_from_db()
        self.assertTrue(another_post.text != self.form_data['text'])

    def test_authorized_client_create_comment(self):
        comments_count = Comment.objects.count()

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.id
            }),
            data=self.comment_form_data,
            follow=True
        )
        comment = Comment.objects.latest('text').text
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment, self.comment_form_data['text'])

    def test_guest_cant_create_comment(self):
        comments_count = Comment.objects.count()
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.id
            }),
            data=self.comment_form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
