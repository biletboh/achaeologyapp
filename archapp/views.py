from django.views.generic import View, DetailView, TemplateView, ListView
from django.views.generic import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.edit import FormMixin
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import Context, loader
from django.template.defaultfilters import slugify
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ValidationError
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from hvad.utils import get_translation_aware_manager

from archapp.models import Site, Filter, Image, Property, ValueType, Project
from archapp.models import ImageType, UserProfile, Tab
from archapp.forms import NewSiteForm, SignUpForm, UserUpdateForm, ProjectForm
from archapp.forms import ListSearchForm, EditSiteForm, CreateFilterForm
from archapp.forms import TabForm 
from archapp.geo import GeoCoder


# TODO: look for proper django choices implementation
def ValueTypeToString(value):
    return [b.lower() for a, b in ValueType.choices if a == value.oftype][0]


# type conversion
def FixValueType(vt, data, value=None, dicted=False):
    tmp = None

    if vt.oftype == ValueType.integer:
        tmp = int(data)
    elif vt.oftype == ValueType.boolean:
        tmp = bool(data)
    elif vt.oftype == ValueType.double:
        tmp = float(data)
    elif vt.oftype == ValueType.string:
        tmp = data

    if dicted:
        value[ValueTypeToString(vt)] = tmp
    else:
        return tmp


class SiteProcessingView(object):

    # update or create new filter values
    def process_filters_and_pics(self, site, form, editing=False):
        geo = GeoCoder(GeoCoder.Type.google)
        values = form.cleaned_data
        filters = Filter.objects.filter(basic=True)

        for instance in filters:
            prop = None
            args = {'instance': instance}
            name = instance.name.lower()
            data = values[name]

            # usually this means validation fail, but
            # let's override this for missing fields
            if data is None:
                data = False

            # explicit type conversion here
            FixValueType(instance, data, args, True)

            # search for string values first
            if instance.oftype == ValueType.string:
                # let's remember missing translations...
                missing = []

                # we want these values to be explicitly translated
                if name in geo.filters():
                    for lang, etc in settings.LANGUAGES:
                        # try to get geo data in specified language
                        with translation.override(lang):
                            geocoded = geo.reverse(
                                                values['latitude'],
                                                values['longtitude'],
                                                lang, name)
                            # maybe try another provider here?
                            geocoded = geocoded or translation.ugettext('Unknown')

                        # let's search for it
                        try:
                            prop = Property.objects.language(lang).get(
                                                                    instance=instance,
                                                                    string=geocoded)
                        except Property.DoesNotExist:
                            missing.append((lang, geocoded))
                else:
                    # for plain string properties just copy provided
                    # text to all translations
                    missing = [(code, args['string']) for code, full in settings.LANGUAGES]

                # if no translations available, create property
                # without translation
                if prop is None:
                    prop = Property.objects.create(instance=instance)
                    prop.save(update_fields=['instance'])

                # finally fill missing translations
                for lang, translated in missing:
                    prop.translate(lang)
                    prop.string = translated

                    try:
                        prop.save()
                    except:  # translation already exists
                        pass

            # process other property types
            else:
                if editing:
                    site.props.filter(instance=instance).update(**args)
                else:
                    prop = Property.objects.create(**args)

            # add property to site
            if not editing:
                site.props.add(prop)

        # attach images
        for i, choice in ImageType.choices:
            img = choice.lower()
            pic = values[img]

            if pic is not None:
                if i == ImageType.general:
                    # make array from single picture
                    pic = [pic]

                for each in pic:
                    tmp = Image.objects.create(site=site, oftype=i, image=each)
                    tmp.save()

        # delete data from temp_uploads
        form.delete_temporary_files()

        # delete images
        if editing:
            trash = form.cleaned_data['delete_pics'].split(',')
            pics = [int(x) if x.isdigit() else None for x in trash]

            # process only integers
            for img in pics:
                if img is not None:
                    try:
                        # operate directly on queryset, don't
                        # need to fetch the data
                        pic = site.image_set.filter(id=img).delete()
                    except:
                        pass


class SiteCreate(LoginRequiredMixin, FormView, SiteProcessingView):
    template_name = 'archapp/newsite.html'
    form_class = NewSiteForm
    success_url = '/all'
    login_url = '/accounts/login/'
    redirect_field_name = 'redirect_to'

    def form_valid(self, form):
        siteuser = self.request.user
        sitename = form.cleaned_data['name']
        newsite = Site(name=sitename, user=siteuser)
        newsite.save()

        # process all filters and images
        self.process_filters_and_pics(site=newsite, form=form, editing=False)

        newsite.data = {'Bibliography': form.cleaned_data['literature']}
        newsite.save()

        return super(SiteCreate, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(SiteCreate, self).get_context_data(**kwargs)
        context['title'] = "New Site"
        return context

    
class SitePage(LoginRequiredMixin, DetailView):
    manager = get_translation_aware_manager(Site)
    queryset = manager.language()
    template_name = 'archapp/site.html'
    
    def get_context_data(self, **kwargs):
        context = super(SitePage, self).get_context_data(**kwargs)
        context['sview'] = True
        context['title'] = "Site Page"
        return context


class SiteEdit(LoginRequiredMixin, FormMixin, DetailView, SiteProcessingView):
    manager = get_translation_aware_manager(Site)
    queryset = manager.language()
    form_class = EditSiteForm
    model = Site
    template_name = 'archapp/edit.html'
    login_url = '/accounts/login/'
    redirect_field_name = 'redirect_to'

    def get_success_url(self):
        return reverse('archapp:allsites')

    def get_context_data(self, **kwargs):
        context = super(SiteEdit, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['title'] = "Edit Site"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # obtain current site, root can edit all of them
        params = {'pk': form.cleaned_data['site_id']}

        if not self.request.user.is_superuser:
            params['user'] = self.request.user

        try:
            site = Site.objects.get(**params)

            # update its name
            site.name = form.cleaned_data['name']

            # update all filters and images
            self.process_filters_and_pics(site=site, form=form, editing=True)

            # get 'bibliography'
            lit = form.cleaned_data['literature']

            # create new dict or update existing
            if type(site.data) is dict:
                site.data['Bibliography'] = lit
            else:
                site.data = {'Bibliography': lit}

            # save site
            site.save()

        finally:
            # no need to handle other case here. if user is
            # not root he or she shouldn't be able to edit
            # other's precious data.
            return super(SiteEdit, self).form_valid(form)


class SiteDelete(LoginRequiredMixin, DeleteView):
    model = Site
    success_url = '/all/' 
    template_name = 'archapp/delete.html'

    def get_context_data(self, **kwargs):
        context = super(SiteDelete, self).get_context_data(**kwargs)
        context['title'] = "Delete Site"
        return context


class AllSites(LoginRequiredMixin, FormMixin, ListView):
    model = Site
    form_class = ListSearchForm
    template_name = 'archapp/all.html'
    success_url = '/'
    login_url = '/accounts/login/'

    def get_queryset(self):
        queryset = Site.objects
        defaults = {} if self.request.user.is_superuser else {'user': self.request.user}
        filtered = queryset  #.filter()

        if self.request.method == 'POST':
            flts = Filter.objects.filter(basic=True)
            data = self.request.POST.copy()

            # filter name
            name = data.get('name')

            if name:
                defaults.update({'name__contains': name})

            # look for possible filter-data matches
            for instance in flts:

                value = data.get(instance.name.lower())

                if value and len(value):

                    # lets fuck with translations later
                    if instance.oftype != ValueType.string:
                        # we need exact type here
                        value = FixValueType(instance, value)
                        # if not default value
                        if value >= 0:
                            # construct another SQL AND clause
                            variable = ValueTypeToString(instance)
                            fltquery = {
                                    'props__instance': instance.id,
                                    'props__' + variable: value}
                            filtered = filtered.filter(**fltquery)
                    else:
                        pass
                        # get_translation_aware_manager() and friends
                        # manager = get_translation_aware_manager(Site)
                        # queryset = manager.language()
            
            # print(filtered.query)
            # print(filtered)

        return filtered.filter(**defaults)

    def get_context_data(self, **kwargs):
        context = super(AllSites, self).get_context_data(**kwargs)
        context['title'] = "All Sites"
        return context

    def get_success_url(self):
        return reverse('archapp:allsites')

    def post(self, request, *args, **kwargs):
        return super(AllSites, self).get(request, args, kwargs)


class Search(LoginRequiredMixin, ListView):
    model = Site
    template_name = 'archapp/search.html'


class WelcomePage(TemplateView):
    template_name = 'archapp/welcome.html'

    def get_context_data(self, **kwargs):
        context = super(WelcomePage, self).get_context_data(**kwargs)
        context['title'] = "Welcome page"
        return context


class SignUp(FormView):
    form_class = SignUpForm
    template_name = 'archapp/signup.html'

    def form_valid(self, form):
        form.save()
        username = self.request.POST['username']
        password = self.request.POST['password1']
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return super(SignUp, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(SignUp, self).get_context_data(**kwargs)
        context['title'] = 'Register'
        return context

    def get_success_url(self):
        user = self.request.user
        return reverse('archapp:userprofile', 
                kwargs={'slug': slugify(user.username)})


class UserProfile(LoginRequiredMixin, DetailView):
    template_name = 'archapp/userprofile.html'
    model = User
    slug_field = "username"

    def get_context_data(self, **kwargs):
        context = super(UserProfile, self).get_context_data(**kwargs)
        context['title'] = "User Profile"
        context['form'] = ProjectForm()
        return context


class UserDisplay(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'archapp/userupdate.html'
    slug_field = 'username'

    def get_context_data(self, **kwargs):
        context = super(UserDisplay, self).get_context_data(**kwargs)
        context['form'] = UserUpdateForm() 
        context['title'] = "Edit Profile"
        return context


class UserUpdateFormView(LoginRequiredMixin, SingleObjectMixin, FormView):
    form_class = UserUpdateForm
    success_url = '/'
    model = User
    slug_field = 'username'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UserUpdateFormView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        userprofile = user.user_profile 
        user.username = form.cleaned_data['username']
        user.email = form.cleaned_data['email']
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        country = form.cleaned_data['country']
        city = form.cleaned_data['city']
        organization = form.cleaned_data['organization']
        avatar = form.cleaned_data['avatar']

        if avatar: 
            user.user_profile.avatar = avatar
        userprofile.country = country
        userprofile.city = city 
        userprofile.organization = organization

        # password1 = form.cleaned_data["password1"]
        # password2 = form.cleaned_data["password2"]
        # if password1 and password2 and password1 != password2:
        #     msg = "Passwords don't match"
        #     raise form.ValidationError("Password mismatch")

        user.save()
        return super(UserUpdateFormView, self).form_valid(form)

    def get_success_url(self):
        user = self.request.user
        return reverse("archapp:userprofile", kwargs = {'slug': slugify(user.username)})


class UserUpdate(View):

    def get(self, request, *args, **kwargs):
        view = UserDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = UserUpdateFormView.as_view()
        return view(request, *args, **kwargs)


class UserDelete(LoginRequiredMixin, DeleteView):
    model = User
    slug_field = "username"
    success_url = '/signup/'


class CreateProject(LoginRequiredMixin, FormView):
    form_class = ProjectForm 
    model = Project

    def form_valid(self, form):
        user = self.request.user
        project = user.project_set.create(name=form.cleaned_data['name'], description = form.cleaned_data['description'])
        return HttpResponseRedirect(reverse('archapp:manage-project', kwargs={'slug': self.kwargs['slug'], 'pk': project.pk}))


class UserProfileAndCreateProject(View):

    def get(self, request, *args, **kwargs):
        view = UserProfile.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = CreateProject.as_view()
        return view(request, *args, **kwargs)


class CreateTab(LoginRequiredMixin, SingleObjectMixin, FormView):
    form_class = TabForm 
    model = Project

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(CreateTab, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        project = self.object
        new_tab, created = Tab.objects.get_or_create(
            name=form.cleaned_data['name'],
            order=form.cleaned_data['order'],
            project=project
            )

        return super(CreateTab, self).form_valid(form)
    
    def get_success_url(self):
        return reverse(
            'archapp:manage-project',
            kwargs={'slug': self.kwargs['slug'], 
            'pk': self.object.pk})


class ManageProject(LoginRequiredMixin, DetailView):
    model = Project 
    template_name = 'archapp/project.html'
    slug_field = 'name'

    def get_context_data(self, **kwargs):
        context = super(ManageProject, self).get_context_data(**kwargs)
        context['form'] = CreateFilterForm() 
        context['tabform'] = TabForm()
        context['tabs'] = Tab.objects.filter(project=self.object) 
        context['title'] = "Manage a Project"
        return context


class AddFilters(LoginRequiredMixin, SingleObjectMixin, FormView):
    #template_name = 'archapp/project.html'
    form_class = CreateFilterForm
    model = Project

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(AddFilters, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        project = self.object
        new_filter, created = Filter.objects.get_or_create(
            name=form.cleaned_data['name'],
            basic=form.cleaned_data['basic'],
            oftype=form.cleaned_data['oftype'],
            project=project,
            )

        return super(AddFilters, self).form_valid(form)
    
    def get_success_url(self):
        return reverse(
            'archapp:manage-project',
            kwargs={'slug': self.kwargs['slug'], 
            'pk': self.object.pk})


class ManageProjectFilters(View):

    def get(self, request, *args, **kwargs):
        view = ManageProject.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        if 'new-filter' in request.POST:
            view = AddFilters.as_view()
        elif 'new-tab' in request.POST:
            view = CreateTab.as_view() 

        return view(request, *args, **kwargs)

