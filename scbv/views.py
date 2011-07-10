from django.conf.urls.defaults import patterns, url
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import modelform_factory
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

class View(object):
    template_name = None
    
    def __call__(self, request):
        return self.respond(self.get_context_data(request))

    def get_template_names(self, **kwargs):
        return [self.template_name]

    def get_context_data(self, request, **kwargs):
        return kwargs

    def respond(self, request, context, **kwargs):
        return TemplateResponse(request, self.get_template_names(**kwargs),
                                context)

class BaseFormView(View):
    form_class = None
    success_url = None

    def __call__(self, request):
        return self.handle(request)

    def handle(self, request, **kwargs):
        forms = self.create_forms(request.POST or None,
                                  request.FILES or None,
                                  **kwargs)
        if self.is_valid(forms, **kwargs):
            return self.done(forms, **kwargs)
        return self.respond(request,
                            self.get_context_data(request,
                                                  forms=forms,
                                                  **kwargs),
                            **kwargs)

    def get_form_class(self, **kwargs):
        return self.form_class, {}

    def get_success_redirect(self, **kwargs):
        if not self.success_url:
            raise ImproperlyConfigured('No URL to redirect to.'
                                       ' Provide a success_url.')
        return self.success_url

    def create_form(self, form_class, data, files, **kwargs):
        form_class, extra_args = self.get_form_class(**kwargs)
        return form_class(data, files, **extra_args)

    def create_forms(self, data, files, **kwargs):
        return [self.create_form(data, files, **kwargs)]

    def is_valid(self, forms, **kwargs):
        return all(f.is_valid() for f in forms)

    def process(self, forms, **kwargs):
        raise NotImplementedError()

    def done(self, forms, **kwargs):
        results = self.process(forms, **kwargs)
        return self.get_success_redirect(results, **kwargs)


class ModelFormView(BaseFormView):
    model = None
    fields = None
    exclude = None
    template_name_suffix = ''

    def handle(self, request, instance=None, **kwargs):
        instance = instance or self.create_instance()
        return super(ModelFormView, self).handle(request, instance=instance,
                                                 **kwargs)

    def get_template_names(self, **kwargs):
        if self.template_name:
            return [self.template_name]
        return ['%s/%s%s.html' % (self.model._meta.app_label,
                                  self.model._meta.object_name.lower(),
                                  self.template_name_suffix)]

    def get_form_class(self, instance, **kwargs):
        if self.form_class:
            return self.form_class, {}
        return modelform_factory(self.model, fields=self.fields,
                                 exclude=self.exclude), {}

    def create_instance(self):
        return self.model()

    def create_form(self, data, files, instance=None, **kwargs):
        form_class, extra_args = self.get_form_class(instance=instance,
                                                     **kwargs)
        return form_class(data, files, instance=instance, **extra_args)

    def process(self, forms, **kwargs):
        return [f.save() for f in forms]


class ModelHandler(ModelFormView):
    '''
    A basic CRUD handler
    '''
    queryset = None
    success_url_create = None
    success_url_update = None
    success_url_delete = None
    template_name_suffix_create = '_form'
    template_name_suffix_read = ''
    template_name_suffix_update = '_form'

    def __call__(self, *args, **kwargs):
        raise NotImplementedError('Do not call a ModelHandler directly.')

    def create(self, request):
        return self.handle(request, instance=None, intent='create')

    def read(self, request, **kwargs):
        instance = self.get_object(**kwargs)
        return self.respond(request,
                            self.get_context_data(request,
                                                  instance=instance),
                            intent='read')

    def update(self, request, **kwargs):
        instance = self.get_object(**kwargs)
        return self.handle(request, instance=instance, intent='update')

    def delete(self, request, **kwargs):
        if request.method != 'POST':
            return HttpResponseForbidden('Only POST is allowed in delete().')
        instance = self.get_object(**kwargs)
        instance.delete()
        return self.get_success_redirect(results=None, instance=None,
                                         intent='delete')

    def get_urls(self, prefix=None):
        prefix = prefix or '%s-%s' % (self.model._meta.app_label,
                                      self.model._meta.object_name.lower())
        return patterns('',
            url(r'^create/$', self.create, name='%s-create' % prefix),
            url(r'^(?P<pk>\d+)/$', self.read, name='%s-read' % prefix),
            url(r'^(?P<pk>\d+)/update/$', self.update, name='%s-update' % prefix),
            url(r'^(?P<pk>\d+)/delete/$', self.delete, name='%s-delete' % prefix),
        )

    def get_object(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)

    def get_queryset(self):
        return self.queryset or self.model._default_manager.all()

    def get_template_names(self, intent, **kwargs):
        if self.template_name:
            return [self.template_name]
        if intent == 'create':
            suffix = self.template_name_suffix_create
        elif intent == 'read':
            suffix = self.template_name_suffix_read
        elif intent == 'update':
            suffix = self.template_name_suffix_update
        else:
            suffix = ''
        return ['%s/%s%s.html' % (self.model._meta.app_label,
                                  self.model._meta.object_name.lower(),
                                  suffix)]

    def get_success_redirect(self, results, intent, **kwargs):
        if intent == 'create':
            return redirect(self.success_url_create or results[0])
        elif intent == 'update':
            return redirect(self.success_url_update or results[0])
        elif intent == 'delete':
            if not self.success_url_delete:
                raise ImproperlyConfigured('No URL to redirect to.'
                                           ' Provide a success_url_delete.')
            return redirect(self.success_url_delete)
