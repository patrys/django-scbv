from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse
from django.test import TestCase
import os.path

from .. import views

class Parrot(models.Model):
    name = models.CharField(max_length=20)


class ParrotHandler(views.ModelHandler):
    model = Parrot
    success_url_create = 'form-done'
    success_url_update = 'form-done'
    success_url_delete = 'form-done'


urlpatterns = patterns('',
    url(r'^done/$', lambda request: HttpResponse(''), name='form-done'),
    url(r'^parrot/', include(ParrotHandler().get_urls(prefix='parrot'))),
)


class ClassBasedViewTest(TestCase):
    urls = 'scbv.tests'

    def setUp(self):
        self.ORIGINAL_TEMPLATE_DIRS = settings.TEMPLATE_DIRS
        settings.TEMPLATE_DIRS = [os.path.join(os.path.dirname(__file__),
                                               'templates')]
        self.test_parrot = Parrot.objects.create(name='test')

    def tearDown(self):
        settings.TEMPLATE_DIRS = self.ORIGINAL_TEMPLATE_DIRS
        self.test_parrot.delete()

    def test_create_view_get_valid(self):
        create_uri = reverse('parrot-create')
        result = self.client.get(create_uri)
        self.assertEqual(result.status_code, 200)

    def test_create_view_post_invalid(self):
        data = {
            'name': '',
        }
        create_uri = reverse('parrot-create')
        result = self.client.post(create_uri, data=data)
        self.assertEqual(result.status_code, 200)

    def test_create_view_post_valid(self):
        data = {
            'name': 'Dead',
        }
        initial_count = Parrot.objects.all().count()
        create_uri = reverse('parrot-create')
        result = self.client.post(create_uri, data=data)
        final_count = Parrot.objects.all().count()
        self.assertEqual(result.status_code, 302)
        self.assertRedirects(result, reverse('form-done'))
        self.assertEqual(final_count, initial_count+1)

    def test_read_view_get_valid(self):
        read_uri = reverse('parrot-read', args=[self.test_parrot.pk])
        result = self.client.get(read_uri)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context['instance'].pk, self.test_parrot.pk)

    def test_read_view_get_invalid(self):
        read_uri = reverse('parrot-read', args=[999])
        result = self.client.get(read_uri)
        self.assertEqual(result.status_code, 404)

    def test_update_view_get_valid(self):
        update_uri = reverse('parrot-update', args=[self.test_parrot.pk])
        result = self.client.get(update_uri)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.context['instance'].pk, self.test_parrot.pk)

    def test_update_view_post_invalid(self):
        data = {
            'name': '',
        }
        update_uri = reverse('parrot-update', args=[self.test_parrot.pk])
        result = self.client.post(update_uri, data=data)
        self.assertEqual(result.status_code, 200)

    def test_update_view_post_valid(self):
        data = {
            'name': 'Dead',
        }
        update_uri = reverse('parrot-update', args=[self.test_parrot.pk])
        result = self.client.post(update_uri, data=data)
        self.assertEqual(result.status_code, 302)
        self.assertRedirects(result, reverse('form-done'))
        updated_parrot = Parrot.objects.get(pk=self.test_parrot.pk)
        self.assertEqual(updated_parrot.name, data['name'])

    def test_delete_view_get_invalid(self):
        delete_uri = reverse('parrot-delete', args=[self.test_parrot.pk])
        result = self.client.get(delete_uri)
        self.assertEqual(result.status_code, 403)

    def test_delete_view_post_valid(self):
        delete_uri = reverse('parrot-delete', args=[self.test_parrot.pk])
        initial_count = Parrot.objects.all().count()
        result = self.client.post(delete_uri, data={})
        final_count = Parrot.objects.all().count()
        self.assertEqual(result.status_code, 302)
        self.assertRedirects(result, reverse('form-done'))
        self.assertEqual(final_count, initial_count-1)
