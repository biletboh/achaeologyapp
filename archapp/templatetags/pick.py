from django import template
from archapp.models import ImageType
from django.conf import settings
from easy_thumbnails.files import get_thumbnailer


register = template.Library()


# filter particular image types from all images
@register.filter
def pick_type(objs, oftype):
    result = []

    for i in objs:
        if i.oftype == getattr(ImageType, oftype.lower()):
            result.append(i)

    return result


# filter multiple image types from all images
@register.filter
def pick_mult_types(objs, oftypes):
    result = []
    oftypes = oftypes.split(',')
    for oftype in oftypes:
        for i in objs:
            if i.oftype == getattr(ImageType, oftype.lower()):
                result.append(i)
    return result


# get specific size of a single image
@register.filter
def pick_size(obj, size):
    return get_thumbnailer(obj.image)[size].url


# get first image of a list with specific size
@register.filter
def pick(objs, args):
    oftype, size = args.split(',')

    o = pick_type(objs, oftype)

    if len(o) == 0:
        return settings.THUMBNAIL_DEFAULT
    else:
        return pick_size(o[0], size)
