import requests
from bs4 import BeautifulSoup
import re

from classes import Flat


def check_parameter(param, param_type, func=None):
    if not isinstance(param, param_type):
        raise TypeError
    elif func and not func(param):
        raise ValueError
    else:
        return 1 if isinstance(param, bool) else param


def make_parameters(sort=None, page=None, rooms=None, price_from=None, price_to=None, photo=None, novostroy=None,
                    owner=None, krisha_agent=None, floor_from=None, floor_to=None, floor_not_first=None,
                    floor_not_last=None, area_from=None, area_to=None, kitchen_area_from=None, kitchen_area_to=None,
                    living_area_from=None, living_area_to=None):
    parameters = {}

    if sort:
        parameters['sort_by'] = check_parameter(sort, str, lambda x: x in ['price-asc', 'price-desc'])

    if page:
        parameters['page'] = check_parameter(page, int, lambda x: x > 0)

    if rooms:
        parameters['das[live.rooms]'] = check_parameter(rooms, int, lambda x: x > 0)

    if price_from:
        parameters['das[price][from]'] = check_parameter(price_from, int, lambda x: x >= 0)

    if price_to:
        parameters['das[price][to]'] = check_parameter(price_to, int, lambda x: x >= 0)

    if photo:
        parameters['das[_sys.hasphoto]'] = check_parameter(photo, bool)

    if novostroy:
        parameters['das[novostroiki]'] = check_parameter(novostroy, bool)

    if owner:
        parameters['das[who]'] = check_parameter(owner, bool)
    if krisha_agent:
        parameters['das[_sys.fromAgent]'] = check_parameter(krisha_agent, bool)

    if floor_from:
        parameters['das[flat.floor][from]'] = check_parameter(floor_from, int)
    if floor_to:
        parameters['das[flat.floor][to]'] = check_parameter(floor_to, int)
    if floor_not_first:
        parameters['das[floor_not_first]'] = check_parameter(floor_not_first, bool)
    if floor_not_last:
        parameters['das[floor_not_last]'] = check_parameter(floor_not_first, bool)

    if area_from:
        parameters['das[live.square][from]'] = check_parameter(area_from, (int, float), lambda x: x >= 0)
    if area_to:
        parameters['das[live.square][to]'] = check_parameter(area_to, (int, float), lambda x: x >= 0)
    if kitchen_area_from:
        parameters['das[live.square_k][from]'] = check_parameter(kitchen_area_from, (int, float), lambda x: x >= 0)
    if kitchen_area_to:
        parameters['das[live.square_k][to]'] = check_parameter(kitchen_area_to, (int, float), lambda x: x >= 0)
    if living_area_from:
        parameters['das[live.square_l][from]'] = check_parameter(living_area_from, (int, float), lambda x: x >= 0)
    if living_area_to:
        parameters['das[live.square_l][to]'] = check_parameter(living_area_to, (int, float), lambda x: x >= 0)

    return parameters


def search(real_estate_type, offer_type, limit=10, **kwargs) -> list[Flat]:
    url = 'https://krisha.kz/'

    type_dict = {
        'flat': 'kvartiry',
        'house': 'doma',
        'room': 'komnaty',
        'dacha': 'dachi'
    }
    city = 'astana'

    match offer_type:
        case 'buy':
            url += f'prodazha/{type_dict[real_estate_type]}/'
        case 'monthly':
            url += f'arenda/{type_dict[real_estate_type]}/'
        case 'daily':
            if real_estate_type == 'flat':
                url += f'arenda/kvartiry-posutochno/'
            else:
                raise ValueError
        case 'hourly':
            if real_estate_type == 'flat':
                url += f'arenda/kvartiry-po-chasam/'
            else:
                raise ValueError
        case _:
            raise ValueError

    url += city + '/'
    params = make_parameters(**kwargs)

    result = []
    page = 1
    global_limit = limit
    while len(result) < min(limit, global_limit):
        response = requests.get(url, params)

        soup = BeautifulSoup(response.text, 'html.parser')

        if page == 1:
            global_limit = int(
                ''.join(re.findall(r'[0-9]+', soup.find('div', attrs={'class': 'search-results-nb'}).text))
            )

        flats_raw = soup.find_all('div', attrs={'class': 'a-card'})
        flats = [div for div in flats_raw if not div.find_parent('section', attrs={'class': 'highlighted-section'})]

        ad_ids = [flat['data-id'] for flat in flats]

        prices = [
            int(
                ''.join(re.findall(r'[0-9]+', flat.find('div', attrs={'class': 'a-card__price'}).text))
            ) for flat in flats
        ]

        titles = [flat.find('a', attrs={'class': 'a-card__title'}).text.strip() for flat in flats]
        numbers = [re.findall(r'[0-9]+(?:\.[0-9]+)?', title) for title in titles]
        room_numbers = [int(number[0]) for number in numbers]
        areas = [float(number[1]) for number in numbers]
        floors = [int(number[2]) if len(number) > 2 else None for number in numbers]
        building_heights = [int(number[3]) if len(number) > 3 else None for number in numbers]

        addresses = [flat.find('div', attrs={'class': 'a-card__subtitle'}).text.strip() for flat in flats]

        result += [
            Flat(*flat) for flat in zip(ad_ids, addresses, areas, prices, room_numbers, floors, building_heights)
        ]

        print('\r', end='')
        print(f'Page {page:3} | {min(len(result), limit, global_limit):4} ads', end='')
        page += 1
        params['page'] = page

    return result[:min(limit, global_limit)]


if __name__ == '__main__':
    ads = search('flat', 'monthly', limit=3000, sort='price-asc', rooms=1, price_to=100000)
    for ad in ads:
        print(ad.url())
        print('Адрес:', ad.address)
        print('Комнаты:', ad.rooms)
        print('Площадь:', ad.area, 'м²')
        print('Цена:', ad.price, 'тенге')
        print('Этаж: ', ad.floor, '/', ad.building_height, sep='')
        print()
