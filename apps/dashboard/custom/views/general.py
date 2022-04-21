from django.contrib import messages
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, UpdateView, DeleteView

from apps.dashboard.custom.forms import BrochureForm, GalleryForm, AlbumForm, AlbumFormset
from apps.dashboard.custom.models import OfferBanner, models_list, Brochure, Gallery


class ModelSelectorMixin(object):

    fields = '__all__'

    @property
    def selector(self) -> list:
        return [{
            'model': model,
            'slug': model.referrer,
            'title': " ".join([name[0].upper() + name[1:] for name in model._meta.verbose_name.split(' ')]),
            'title_plural': " ".join([name[0].upper() + name[1:] for name in model._meta.verbose_name_plural.split(' ')]),
        } for model in models_list]

    selected = None

    def __initialize(self):
        urlname = self.request.resolver_match.url_name
        for item in self.selector:
            if item['slug'] in urlname:
                self.selected = item
                return
        raise Http404()

    def get_queryset(self) -> QuerySet:
        self.__initialize()
        return self.selected['model'].objects.all()

    def get_success_url(self):
        self.__initialize()
        return reverse(f'dashboard-custom:dashboard-{self.selected["slug"]}-list')

    def get_context_data(self, **kwargs):
        self.__initialize()
        return super(ModelSelectorMixin, self).get_context_data(
            title=self.selected['title'],
            title_plural=self.selected['title_plural'],
            list_url=reverse('dashboard-custom:dashboard-' + self.selected['slug'] + '-list'),
            create_new_url=reverse('dashboard-custom:dashboard-' + self.selected['slug'] + '-create'),
            update_url_name='dashboard-custom:dashboard-' + self.selected['slug'] + '-update',
            delete_url_name='dashboard-custom:dashboard-' + self.selected['slug'] + '-delete',
            **kwargs)


class DashboardBlockList(ModelSelectorMixin, ListView):
    template_name = 'dashboard/custom/general/block-list.html'
    context_object_name = "banner_list"
    ordering = ['position', ]


class DashboardCustomCreate(ModelSelectorMixin, CreateView):
    template_name = 'dashboard/custom/general/form.html'
    context_object_name = "banner_list"


class DashboardCustomDetail(ModelSelectorMixin, UpdateView):
    template_name = 'dashboard/custom/general/form.html'
    context_object_name = "banner_object"


class DashboardCustomDelete(ModelSelectorMixin, DeleteView):
    template_name = 'dashboard/custom/general/delete-form.html'
    context_object_name = "banner_object"


# class DashboardCustomCreate(ModelSelectorMixin, CreateView):
#     template_name = 'dashboard/custom/general/form.html'
#     context_object_name = "banner_list"
#
#
# class DashboardCustomDetail(ModelSelectorMixin, UpdateView):
#     template_name = 'dashboard/custom/general/form.html'
#     context_object_name = "banner_object"


def resolve_enquiry(request, pk):
    enq = ContactUsEnquiry.objects.filter(pk=pk).last()
    if enq is None:
        messages.warning(request, f"No Enquiry Found With id: #{pk}")
    else:
        enq.resolved = not enq.resolved
        enq.save()
        if not enq.resolved:
            messages.info(request, f"Enquiry #{pk} Marked as Unresolved")
        else:
            messages.success(request, f"Enquiry #{pk} Marked as Resolved")
    return redirect(to='dashboard-custom:dashboard-enquiries-list')


class BrochureCreateView(CreateView):
    template_name = 'oscar/dashboard/catalogue/brochure_add.html'
    model = Brochure
    form_class = BrochureForm
    # success_url = 'dashboard-custom:dashboard-brochure-create'

    def get_context_data(self):
        cxt = super().get_context_data()
        cxt['brochure'] = Brochure.objects.all().order_by('-id')
        return cxt

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            form.save()
            return redirect('dashboard-custom:dashboard-brochure-create')
        return super().post(request, *args, **kwargs)


class BrochureUpdateView(UpdateView):
    template_name = 'oscar/dashboard/catalogue/brochure_update.html'
    model = Brochure
    form_class = BrochureForm

    def form_valid(self, form):
        print(self.get_object())

        form = BrochureForm(instance=self.get_object())
        return super().form_valid(form)


def delete_brochure(request, id):
    try:
        Brochure.objects.get(id=id).delete()
    except Exception as e:
        print(e)
    return redirect('dashboard-custom:dashboard-brochure-create')


class GalleryCreateView(CreateView):
    template_name = 'oscar/dashboard/catalogue/gallery_add.html'
    model = Gallery
    form_class = GalleryForm
    # success_url = 'dashboard-custom:dashboard-gallery-create'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['title'].widget.attrs.update({'class': 'form-control'})
        form.fields['description'].widget.attrs.update({'class': 'form-control'})
        form.fields['image'].widget.attrs.update({'class': 'form-control'})
        return form

    def get_context_data(self, **kwargs):
        cxt = super().get_context_data()
        cxt['gallery'] = Gallery.objects.all().order_by('-id')
        cxt['form'] = GalleryForm()
        cxt['formset'] = AlbumFormset()
        return cxt

    def post(self, request, *args, **kwargs):
        form = GalleryForm(self.request.POST, self.request.FILES)
        formset = AlbumFormset(self.request.POST, self.request.FILES)
        if form.is_valid():
            instance = form.save()
            for f in formset:
                import pdb;pdb.set_trace()
                f.gallery = instance
                f.save()
        return super().post(request, *args, **kwargs)


class GalleryUpdateView(UpdateView):
    template_name = 'oscar/dashboard/catalogue/gallery_update.html'
    model = Gallery
    form_class = GalleryForm

    def form_valid(self, form):
        print(self.get_object())

        form = GalleryForm(instance=self.get_object())
        return super().form_valid(form)


def delete_gallery(request, id):
    try:
        Gallery.objects.get(id=id).delete()
    except Exception as e:
        print(e)
    return redirect('dashboard-custom:dashboard-gallery-create')


def get_album_form(request):
    inlines = ''
    context = {'request': request}
    if request.method == 'GET':
        inlines = AlbumForm(context)
    return render(request, 'oscar/dashboard/catalogue/albumform.html', context={'inlines': inlines})
