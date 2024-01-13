from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING
from pytils.translit import slugify

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Читатель')
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }

    # Проверяем, что если зарегистрированный пользователь пытается создать
    # заметку, то он перенаправляется на страницу успешного создания заметки, в
    # БД добавляется 1 заметка, значения полей которой соответствуют ожиданиям:
    def test_user_can_create_note(self):
        url = reverse('notes:add')
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    # Проверяем, что если анонимный пользователь пытается создать заметку, то
    # он перенаправляется на страницу логина, а в БД добавляется 0 заметок:
    def test_anonymous_user_cant_create_note(self):
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)

    # Проверяем, что если при создании заметки оставить поле slug пустым — то
    # содержимое этого поля будет сформировано автоматически, из содержимого
    # поля title:
    def test_empty_slug(self):
        url = reverse('notes:add')
        self.form_data.pop('slug')
        self.client.force_login(self.author)
        expected_url = reverse('notes:success')
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    # Проверяем, что при попытке создание заметки с существующим уже значением
    # slug выводится ошибка с WARNING
    def test_not_unique_slug(self):
        url = reverse('notes:add')
        self.client.force_login(self.author)
        note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=self.author,
        )
        self.form_data['slug'] = note.slug
        response = self.client.post(url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(note.slug + WARNING)
        )
        note_counts = Note.objects.count()
        self.assertEqual(note_counts, 1)

    # Проверяем, что автор может редактировать свою заметку:
    def test_author_can_edit_note(self):
        note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=self.author,
        )
        url = reverse('notes:edit', args=(note.slug,))
        self.client.force_login(self.author)
        response = self.client.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note.refresh_from_db()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])

    # Проверяем, что другой пользователь не может редактировать чужую заметку
    # и возвращается ошибка 404:
    def test_author_can_edit_note(self):
        note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=self.author,
        )
        url = reverse('notes:edit', args=(note.slug,))
        self.client.force_login(self.reader)
        response = self.client.post(url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=note.id)
        self.assertEqual(note.title, note_from_db.title)
        self.assertEqual(note.text, note_from_db.text)
        self.assertEqual(note.slug, note_from_db.slug)

    # Проверяем, что автор может удалить свою заметку:
    def test_author_can_delete_note(self):
        self.client.force_login(self.author)
        note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=self.author,
        )
        url = reverse('notes:delete', args=(note.slug,))
        response = self.client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    # Проверяем, что другой пользователь не может удалить чужую заметку
    # и возвращается ошибка 404:
    def test_other_user_cant_delete_note(self):
        self.client.force_login(self.reader)
        note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=self.author,
        )
        url = reverse('notes:delete', args=(note.slug,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
