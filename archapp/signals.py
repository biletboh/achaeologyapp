from django.db.models.signals import post_save
from django.dispatch import receiver

from archapp.models import User, Project, Filter, Tab


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.user_profile.save()



@receiver(post_save, sender=Project)
def create_basic_filters(sender, instance, created, **kwargs):

    if created:
        tab = Tab.objects.create(name='main', project=instance)

        default_filters = [
                        {
                        "name": "Country",
                        "oftype": 4,
                        "basic": 1
                        },
                        {
                        "name": "Region",
                        "oftype": 4,
                        "basic": 1
                        },
                        {
                        "name": "District",
                        "oftype": 4,
                        "basic": 1
                        },
                        {
                        "name": "Settlement",
                        "oftype": 4,
                        "basic": 1
                        },
                        {
                        "name": "Latitude",
                        "oftype": 3,
                        "hidden": 1,
                        "basic": 1
                        },
                        {
                        "name": "Longtitude",
                        "oftype": 3,
                        "hidden": 1,
                        "basic": 1
                        }]

        for kw in default_filters:
            Filter.objects.create(project=instance, tab=tab, **kw) 

