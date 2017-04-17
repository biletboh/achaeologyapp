from django.db import models
from picklefield import fields
from djchoices import DjangoChoices, ChoiceItem
from django.contrib.auth.models import User
from hvad.models import TranslatableModel, TranslatedFields
from django.utils.translation import ugettext as _
from easy_thumbnails.fields import ThumbnailerImageField
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# archaeology Project
class Project(models.Model):
    name = models.CharField(max_length = 128)
    description = models.CharField(max_length = 256)
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    
    def __str__(self):
        return self.name


# all possible Property value types
class ValueType(DjangoChoices):
    integer = ChoiceItem(1, "Integer")
    boolean = ChoiceItem(2, "Boolean")
    double = ChoiceItem(3, "Double")
    string = ChoiceItem(4, "String")


class ImageType(DjangoChoices):
    general = ChoiceItem(1, "General")
    plane = ChoiceItem(2, "Plane")
    photo = ChoiceItem(3, "Photo")
    found = ChoiceItem(4, "Found")


# generic Filter for Property referencing
class Filter(models.Model):

    class Meta:
        ordering = ['pk']

    name = models.CharField(max_length=128)
    basic = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    parent = models.ForeignKey('self', null=True,
                            blank=True, related_name='subfilters')
    oftype = models.IntegerField(
                            default=1, verbose_name="Value type",
                            choices=ValueType.choices)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# User-defined Filter
class UserFilter(Filter):
    title = models.TextField(max_length=128, default="User-defined filter")
    query = fields.PickledObjectField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)


# Property of a Site
class Property(TranslatableModel):

    class Meta:
        verbose_name_plural = "properties"

    instance = models.ForeignKey(
                            Filter, verbose_name="Related filter",
                            on_delete=models.CASCADE)
    boolean = models.BooleanField(default=False, verbose_name="Boolean value")
    integer = models.IntegerField(default=0, verbose_name="Integer value")
    double = models.FloatField(default=0.0, verbose_name="Float value")

    translations = TranslatedFields(
                                string=models.TextField(
                                                    max_length=128,
                                                    blank=True,
                                                    verbose_name="String value"
                                                    )
                                )

    def __str__(self):
        if self.instance.parent is not None:
            # return parent filter name for use in select
            try:
                return str(Filter.objects.get(pk=self.integer))
            except Filter.DoesNotExist:
                return 'Broken parent link'
        if self.instance.oftype == ValueType.integer:
            return str(self.integer)
        elif self.instance.oftype == ValueType.boolean:
            return str(self.boolean)
        elif self.instance.oftype == ValueType.double:
            return str(self.double)
        elif self.instance.oftype == ValueType.string:
            return self.lazy_translation_getter(
                                            'string',
                                            _('No translation available'))


# archaeology Site
class Site(models.Model):
    name = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    props = models.ManyToManyField(Property)
    data = fields.PickledObjectField()

    def __str__(self):
        return self.name


# Site photos
class Image(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    image = ThumbnailerImageField(upload_to='uploads', blank=True)
    oftype = models.IntegerField(
                            default=ImageType.general,
                            verbose_name="Image type",
                            choices=ImageType.choices)

    def __str__(self):
        return "type '{}', file '{}'".format(
                                        ImageType.values[self.oftype],
                                        self.image)


class UserProfile(models.Model):
    user = models.OneToOneField(
                            settings.AUTH_USER_MODEL, unique=True,
                            primary_key=True, on_delete=models.CASCADE,
                            related_name='user_profile')
    avatar = ThumbnailerImageField(upload_to='profile_images', blank=True)
    country = models.CharField(max_length=128)
    city = models.CharField(max_length=128)
    organization = models.CharField(max_length=256)

    def __unicode__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.user_profile.save()
