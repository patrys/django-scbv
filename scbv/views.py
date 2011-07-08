from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.forms.models import modelform_factory
from django.shortcuts import redirect
from django.template.response import TemplateResponse

class View(object):
    template_name = None
    
    def __call__(self, request):
        return self.respond(self.get_context_data(request))

    def get_template_names(self):
        return [self.template_name]

    def get_context_data(self, request, **kwargs):
        return kwargs

    def respond(self, request, context):
        return TemplateResponse(request, self.get_template_names(), context)

class BaseFormView(View):
    form_class = None

    def get_form_classes(self):
        return [self.form_class]

    def get_success_redirect(self, **kwargs):
        if not self.success_url:
            raise ImproperlyConfigured('No URL to redirect to.'
                                       ' Provide a success_url.')
        return self.success_url

    def create_form(self, form_class, data, files, **kwargs):
        return form_class(data, files, **kwargs)

    def create_forms(self, data, files, **kwargs):
        form_classes = self.get_form_classes()
        return [self.create_form(form_class, data, files, **kwargs)
                for form_class in form_classes]

    def is_valid(self, forms):
        return all(f.is_valid() for f in forms)

    def process(self, forms):
        raise NotImplementedError()

    def done(self, forms):
        results = self.process(forms)
        return self.get_success_redirect(results)


class ModelFormView(BaseFormView):
    model = None
    fields = None
    exclude = None
    template_name_suffix = ''

    def __call__(self, request):
        forms = self.create_forms(request.POST or None,
                                  request.FILES or None)
        if self.is_valid(forms):
            return self.done(forms)
        return self.respond(request, self.get_context_data(request,
                                                           forms=forms))

    def get_template_names(self):
        if self.template_name:
            return [self.template_name]
        return ['%s/%s%s.html' % (self.model._meta.app_label,
                                  self.model._meta.object_name.lower(),
                                  self.template_name_suffix)]

    def get_form_classes(self):
        if self.form_class:
            return [self.form_class]
        return [modelform_factory(self.model, fields=self.fields,
                                  exclude=self.exclude)]

    def create_instance(self, form_class):
        return self.model()

    def create_form(self, form_class, data, files, instance=None, **kwargs):
        instance = instance or self.create_instance(form_class)
        return form_class(data, files, **kwargs)

    def process(self, forms):
        return [f.save() for f in forms]


class CreateView(ModelFormView):
    template_name_suffix = '_form'

    def get_success_redirect(self, results):
        return redirect(results[0])


class UpdateView(ModelFormView):
    kwarg_mapping = (
        ('pk', 'pk', int),
    )
    queryset = None
    template_name_suffix = '_form'

    def get_success_redirect(self, results):
        return redirect(results[0])

    def get_queryset(self, **kwargs):
        queryset = self.queryset or self.model._default_manager.all()
        query = Q()
        for arg_name, field_name, adapter in self.kwarg_mapping:
            arg = kwargs.pop(arg_name)
            query &= Q(**{field_name: adapter(arg)})
        if kwargs:
            raise ValueError('Unknown params passed to UpdateView: %s' %
                             kwargs.keys())
        return queryset.filter(query)

    def get_object(self, **kwargs):
        return self.get_queryset(**kwargs).get()

    def __call__(self, request, **kwargs):
        instance = self.get_object(**kwargs)
        forms = self.create_forms(request.POST or None,
                                  request.FILES or None,
                                  instance=instance)
        if self.is_valid(forms):
            return self.done(forms)
        return self.respond(request, self.get_context_data(request,
                                                           forms=forms,
                                                           object=instance))
