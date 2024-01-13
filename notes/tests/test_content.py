from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,)

    # Проверяем, что отдельная заметка передаётся на страницу со списком
    # заметок в списке object_list в словаре context и не попадает в список
    # заметок другого пользователя:
    def test_note_in_list_for_author(self):
        tuple = (
            (self.author, True),
            (self.reader, False)
        )
        url = reverse('notes:list')
        for name, note_in_list in tuple:
            with self.subTest(name=name):
                self.client.force_login(name)
                response = self.client.get(url)
                object_list = response.context['object_list']
                self.assertIs(self.note in object_list, note_in_list)

    # Проверяем, что на страницы создания и редактирования заметки
    # передается форма:
    def test_create_note_page_contains_form(self):
        names_url_and_args = (
            ('notes:add', None),
            ('notes:edit', self.note.slug)
        )
        for name, args in names_url_and_args:
            with self.subTest(name=name, args=args):
                if args is not None:
                    url = reverse(name, args=(self.note.slug,))
                else:
                    url = reverse(name)
                self.client.force_login(self.author)
                response = self.client.get(url)
                self.assertIn('form', response.context)
