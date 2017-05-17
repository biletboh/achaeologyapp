from django.contrib import admin
from django.db.models import Sum, Count, Case, When, IntegerField
from .models import Site, Filter, Property, UserProfile, Project, Tab


class PropertyAdmin(admin.ModelAdmin):
    list_display = ('ofsite', '__str__', 'instance')
    # list_editable = ('oftype', 'instance')
    list_filter = ('instance',)

    def ofsite(self, obj):
        return obj.site_set.get()  # filter(obj)

# class FilterInline(admin.StackedInline):
#    model = Filter
#    fields = ['name', 'parent', 'oftype']


class FilterAdmin(admin.ModelAdmin):
    list_filter = ('parent', )
    #list_display = ('name', 'link_count', 'prop_count')
    #inlines = [ FilterInline, ]
    #def get_queryset(self, request):
    #    return super(FilterAdmin, self).get_queryset(request).annotate(
    #        num_props = Count(Case(When(property__linked = False, then = 1), output_field = IntegerField())),
    #        num_linkd = Count(Case(When(property__linked = True, then = 1), output_field = IntegerField()))
    #        )

   # def onlyparent(self, obj):

    #def prop_count(self, obj):
    #    return obj.num_props

    #def link_count(self, obj):
    #    return obj.num_linkd

    #prop_count.short_description = 'Used by'
    #prop_count.admin_order_field = 'num_links'

    #link_count.short_description = 'Subfilters'
    #link_count.admin_order_field = 'num_props'


admin.site.register(Site)
admin.site.register(Property, PropertyAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(UserProfile)
admin.site.register(Project)
admin.site.register(Tab)

