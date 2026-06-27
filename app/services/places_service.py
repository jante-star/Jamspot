import requests
import os

PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
PLACES_BASE = 'https://maps.googleapis.com/maps/api/place'


class PlacesService:

    @staticmethod
    def search_accommodations(query='hotels', location_text=''):
        if not PLACES_API_KEY:
            return []

        search_query = f"{query} {location_text}".strip()
        params = {
            'query': search_query,
            'type': 'lodging',
            'key': PLACES_API_KEY,
        }
        try:
            r = requests.get(f'{PLACES_BASE}/textsearch/json', params=params, timeout=10)
            data = r.json()
            if data.get('status') not in ('OK', 'ZERO_RESULTS'):
                print(f'Places search error: {data.get("status")} — {data.get("error_message", "")}')
                return []
            results = []
            for place in data.get('results', []):
                results.append({
                    'place_id': place.get('place_id'),
                    'name': place.get('name'),
                    'formatted_address': place.get('formatted_address', ''),
                    'rating': place.get('rating', 0),
                    'user_ratings_total': place.get('user_ratings_total', 0),
                    'price_level': place.get('price_level'),
                    'photo_ref': (place.get('photos', [{}])[0] or {}).get('photo_reference'),
                    'types': place.get('types', []),
                })
            return results
        except Exception as e:
            print(f'Places search exception: {e}')
            return []

    @staticmethod
    def get_place_details(place_id):
        if not PLACES_API_KEY or not place_id:
            return None

        fields = (
            'place_id,name,formatted_address,geometry,rating,user_ratings_total,'
            'editorial_summary,photos,price_level,address_components,website'
        )
        params = {'place_id': place_id, 'fields': fields, 'key': PLACES_API_KEY}
        try:
            r = requests.get(f'{PLACES_BASE}/details/json', params=params, timeout=10)
            data = r.json()
            if data.get('status') != 'OK':
                print(f'Places details error: {data.get("status")}')
                return None

            result = data.get('result', {})
            geometry = result.get('geometry', {}).get('location', {})
            city, country = PlacesService._extract_address_parts(result.get('address_components', []))

            photos = []
            for photo in result.get('photos', [])[:6]:
                ref = photo.get('photo_reference')
                if ref:
                    photos.append(PlacesService.get_photo_url(ref, max_width=800))

            price_level = result.get('price_level', 1)
            price_map = {0: 50, 1: 100, 2: 180, 3: 280, 4: 450}
            price_per_night = price_map.get(price_level, 150)

            editorial = result.get('editorial_summary', {})
            description = editorial.get('overview', result.get('formatted_address', ''))

            return {
                'place_id': place_id,
                'name': result.get('name'),
                'formatted_address': result.get('formatted_address', ''),
                'editorial_summary': description,
                'rating': result.get('rating', 0),
                'user_ratings_total': result.get('user_ratings_total', 0),
                'photos': photos,
                'price_per_night': price_per_night,
                'location': {
                    'lat': geometry.get('lat', 0),
                    'lng': geometry.get('lng', 0),
                    'city': city,
                    'country': country,
                },
                'amenities': PlacesService._infer_amenities(result),
            }
        except Exception as e:
            print(f'Places details exception: {e}')
            return None

    @staticmethod
    def get_photo_url(photo_reference, max_width=400):
        return (
            f'{PLACES_BASE}/photo'
            f'?maxwidth={max_width}&photo_reference={photo_reference}&key={PLACES_API_KEY}'
        )

    @staticmethod
    def _extract_address_parts(components):
        city, country = '', ''
        for comp in components:
            types = comp.get('types', [])
            if 'locality' in types:
                city = comp.get('long_name', '')
            if 'country' in types:
                country = comp.get('long_name', '')
        return city, country

    @staticmethod
    def _infer_amenities(place_result):
        amenities = []
        types = place_result.get('types', [])
        if 'lodging' in types:
            amenities.append('Accommodation')
        if place_result.get('rating', 0) >= 4.5:
            amenities.append('Highly Rated')
        if place_result.get('website'):
            amenities.append('Official Website')
        return amenities
