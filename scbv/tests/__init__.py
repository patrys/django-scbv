from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse
from django.test import TestCase
import os.path

from .. import views

class Parrot(models.Model):
    name = models.CharField(max_length=20)

    @models.permalink
    def get_absolute_url(self):
        return 'form-done', ()


class CreateParrot(views.CreateView):
    model = Parrot


class UpdateParrot(views.CreateView):
    model = Parrot


urlpatterns = patterns('',
    url(r'^done/$', lambda request: HttpResponse(''), name='form-done'),
    url(r'^add/$', CreateParrot(), name='create-parrot'),
    url(r'^(?P<pk>\d+)/$', UpdateParrot(), name='update-parrot'),
)


class ClassBasedViewTest(TestCase):
    urls = 'scbv.tests'

    def setUp(self):
        self.ORIGINAL_TEMPLATE_DIRS = settings.TEMPLATE_DIRS
        settings.TEMPLATE_DIRS = [os.path.join(os.path.dirname(__file__),
                                               'templates')]

    def tearDown(self):
        settings.TEMPLATE_DIRS = self.ORIGINAL_TEMPLATE_DIRS

    def test_create_view_get(self):
        result = self.client.get('/add/')
        self.assertEqual(result.status_code, 200)

    def test_create_view_invalid(self):
        data = {
            'name': '',
        }
        result = self.client.post('/add/', data=data)
        self.assertEqual(result.status_code, 200)

    def test_create_view_valid(self):
        data = {
            'name': 'Dead',
        }
        result = self.client.post('/add/', data=data)
        self.assertEqual(result.status_code, 302)
        self.assertRedirects(result, reverse('form-done'))
