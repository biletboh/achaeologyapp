from geopy.geocoders import GoogleV3, Nominatim
from django.utils import translation


class GeoCoder:

    class Type:
        google = 1
        osm = 2

    def __init__(self, coder_type):
        self.coder_type = coder_type
        self.cache = {}

        if coder_type == self.Type.google:
            self.coder = GoogleV3()
        elif coder_type == self.Type.osm:
            self.coder = Nominatim()

        self.mapping = {
                    self.Type.google: {
                                    'country': ['country'],
                                    'region': ['administrative_area_level_1'],
                                    'district': [
                                            'administrative_area_level_2',
                                            'administrative_area_level_3'],
                                    'settlement': ['locality', 'route']
                                    },
                    self.Type.osm: {
                                'country': ['country'],
                                'region': ['state'], 'district': ['county'],
                                'settlement': ['city', 'hamlet', 'village']
                                }
                    }

    def filters(self, name=None):
        return list(self.mapping[self.coder_type].keys())

    def reverse(self, lat=0.0, lng=0.0, lang=None, name='country', raw=False):
        if lang is None:
            lang = translation.get_language()

        key = '{0}{1}{2}'.format(lat, lng, lang)

        if key not in self.cache:
            cached = None
            exceptions = 0

            while not cached and exceptions < 3:
                try:
                    cached = self.coder.reverse((lat, lng), language=lang)
                except:  # timeout, not available
                    exceptions += 1

            self.cache[key] = cached

        if raw:
            return self.cache[key]
        else:
            return self.decode(self.cache[key], name)

    def decode(self, query, name):
        data = None

        if query:
            if self.coder_type == self.Type.google:
                for p in query[0].raw['address_components']:
                    for m in self.mapping[self.coder_type][name]:
                        if m == p['types'][0]:
                            data = p['long_name']

            elif self.coder_type == self.Type.osm:
                for i in query['address']:
                    if i in self.mapping[self.coder_type][name]:
                        data = i

        return data

