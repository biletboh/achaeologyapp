from .models import Filter, UserFilter, Property, ValueType
from .models import Image, Site, ImageType, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from form_utils import forms as betterforms
from django.forms import formset_factory
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_file_form.forms import FileFormMixin
from django_file_form.forms import UploadedFileField, MultipleUploadedFileField

class FilterForm(betterforms.BetterForm):

    # define fieldsets
    def create_fieldsets():
        return [
                ('1', {
                    'description': _('Basic data'), 'legend': 'maintab',
                    'fields': [
                            'name', 'country', 'region', 'district',
                            'settlement', 'latitude', 'longtitude',
                            'placeid']
                        }),
                ('2', {
                    'description': _('Description'), 'legend': 'desctab',
                    'fields': [
                            'riversystem', 'area', 'areawidth',
                            'areaheight', 'topography', 'geomorphology',
                            'altitude', 'valleyaltitude', 'datingfrom',
                            'datingto', 'dating', 'undefined']
                        }),
                ('3', {
                    'description': _('Attachments'), 'legend': 'mediatab',
                    'fields': [
                            'general', 'plane', 'photo',
                            'found'] + ['form_id', 'upload_url', 'delete_url']
                        }),
                ('4', {
                    'description': _('References'), 'legend': 'refstab',
                    'fields': ['literature']
                    })
                ]

    # creates fields for basic filters
    def create_filter_fields(self, query={'basic': True}):
        filters = Filter.objects.filter(**query)
        mapping = {
                ValueType.integer: forms.IntegerField(),
                ValueType.string: forms.CharField(),
                ValueType.double: forms.FloatField(),
                ValueType.boolean: forms.BooleanField()
                }

        for flt in filters:
            field = None
            subs = self.getsubdata(flt)
            args = {'required': False, 'label': _(flt.name)}

            # if this filter have children, use select for them
            if subs.count():
                args['widget'] = forms.Select()
                args['choices'] = [(-1, _('Select value'))]
                + [(s.id, _(s.name)) for s in subs]

                field = forms.ChoiceField()

            # render plain field otherwise
            else:
                if flt.hidden:
                    args['widget'] = forms.widgets.HiddenInput()

                field = mapping[flt.oftype]

            # implicit reconstruction with needed params
            self.fields[flt.name.lower()] = type(field)(**args)

    # get child filters
    def getsubdata(self, obj):
        return obj.subfilters.all().exclude(pk=models.F('parent'))



class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class UserUpdateForm(FileFormMixin, betterforms.BetterForm):
    username = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    old_password = forms.CharField(
                                required=False, label="Old Password",
                                widget=forms.PasswordInput())
    password1 = forms.CharField(
                            required=False, label="New Password",
                            widget=forms.PasswordInput())
    password2 = forms.CharField(
                            required=False, label="Confirm New Password",
                            widget=forms.PasswordInput())
    country = forms.CharField(required=False) 
    city = forms.CharField(required=False)
    organization = forms.CharField(
                                required=False,
                                label="Research oragnization (University)")
    avatar = UploadedFileField(label=_("Profile image"), required=False)
    form_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    upload_url = forms.CharField(widget=forms.HiddenInput(), required=False)
    delete_url = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        fieldsets = [
                ('1', {
                    'description': _('Main Info'), 'legend': 'main_info',
                    'fields': ['username', 'email', 'first_name', 'last_name'],
                    }),
                ('2', {
                    'description': _('Password management'), 
                    'legend': 'update_password',
                    'fields': ['old_password', 'password1', 'password2'],
                    }),
                ('3', {
                    'description': _('User Profile'),
                    'legend': 'user_profile',
                    'fields': [
                            'country', 'city', 'organization', 'avatar',
                            'form_id', 'upload_url', 'delete_url'],
                    })
                ]

class ListSearchForm(FilterForm):

    class Meta:
        fieldsets = [
                ('0', {'description': _('Filters'), 'fields': ['name']}),
                ('1', {
                    'description': _('Location'),
                    'fields': ['country', 'region', 'district']
                    }),
                ('2', {
                    'description': _('Basic data'),
                    'fields': [
                            'areawidth', 'areaheight', 'topography',
                            'geomorphology', 'altitude', 'datingfrom',
                            'datingto']
                    })
                ]

    def __init__(self, *args, **kwargs):
        super(ListSearchForm, self).__init__(*args, **kwargs)

        self.fields['name'] = forms.CharField(
                                            max_length=128,
                                            label=_('Name'))
        self.create_filter_fields()


class SearchForm(FilterForm):

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        self.create_filter_fields()


class NewSiteForm(FileFormMixin, FilterForm):

    class Meta:
        fieldsets = FilterForm.create_fieldsets()

    def __init__(self, *args, **kwargs):
        super(NewSiteForm, self).__init__(*args, **kwargs)

        self.fields['name'] = forms.CharField(max_length=128, label=_('Name'))
        self.fields['undefined'] = forms.BooleanField(
                                                    required=False, 
                                                    label=_(
                                                        'Dating is undefined'))
        self.fields['literature'] = forms.CharField(
                                                required=False,
                                                widget=forms.Textarea,
                                                max_length=2048,
                                                label=_('Literature'))
        self.create_filter_fields()

        # create image fields
        for i, choice in ImageType.choices:
            field = None

            # limit site profile picture to one
            if i == ImageType.general:
                field = UploadedFileField(required=False, label=_(choice))
            else:
                field = MultipleUploadedFileField(
                                                required=False,
                                                label=_(choice))
            self.fields[choice.lower()] = field


class EditSiteForm(NewSiteForm):

    def __init__(self, *args, **kwargs):
        super(EditSiteForm, self).__init__(*args, **kwargs)
        self.fields['site_id'] = forms.IntegerField()
        self.fields['delete_pics'] = forms.CharField(required=False)


class ProjectForm(forms.Form):
    name = forms.CharField(label=_('Project name'), max_length=128)
    description = forms.CharField(label=_('Description'), max_length=256)


class CreateFilterForm(betterforms.BetterForm):
    
    name = forms.CharField(required=True) 
    oftype = forms.IntegerField(
            widget=forms.Select(choices=ValueType.choices))
    basic = forms.BooleanField(
        widget=forms.widgets.HiddenInput(),
        required=False)

    class Meta:
        fieldsets = [('1', {'description': _('Create Filters'), 'legend': 'create_filters', 'fields': ['name', 'oftype', 'basic'], })]


#CreateFilterFormSet = formset_factory(CreateFilterForm, extra=2,)
