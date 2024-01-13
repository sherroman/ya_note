from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,)

    # Проверка доступности для анонимного пользователя главной страницы,
    # страниц входа в учётную запись и выхода из неё, страницы регистрации
    # пользователей:
    def test_pages_availability_for_anonymous_user(self):
        urls = ('notes:home', 'users:login', 'users:logout', 'users:signup')
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверка доступности для зарегистрированного пользователя главной
    # страницы, страницы со списком заметок, страница успешного добавления
    # заметки, страница добавления новой заметки:
    def test_pages_availability_for_auth_user(self):
        urls = ('notes:home', 'notes:list', 'notes:success', 'notes:add')
        self.client.force_login(self.reader)
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверка доступа к страницам отдельной заметки, удаления и редактирования
    # заметки только автору заметки. Если на эти страницы попытается зайти
    # другой пользователь — вернётся ошибка 404:
    def test_test_pages_availability_for_different_users(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        pages = ('notes:detail', 'notes:edit', 'notes:delete')
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in pages:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    # Проверка перенаправления анонимного пользователя на страницу логина при
    # попытке перейти на страницу списка заметок, страницу успешного добавления
    # записи, страницу добавления заметки, отдельной заметки, редактирования
    # или удаления заметки:
    def test_redirect_for_anonymous_client(self):
        login_url = reverse('users:login')
        names_and_args = (
            ('notes:detail', self.note.slug),
            ('notes:edit', self.note.slug),
            ('notes:delete', self.note.slug),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None)
        )
        for name, args in names_and_args:
            with self.subTest(name=name, args=args):
                if args is not None:
                    url = reverse(name, args=(self.note.slug,))
                else:
                    url = reverse(name)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
