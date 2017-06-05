import requests


# takes server list outputs locations (each only once) the servers are in.
def get_unique_locations(list_of_servers):
    unique_locations = []
    resolved_locations = []
    for aServer in list_of_servers:
        latLongDic = {"lat": aServer["location"]["lat"], "long": aServer["location"]["long"]}
        if latLongDic not in unique_locations:
            unique_locations.append(latLongDic)
        # print(unique_locations)
    for eachLocation in unique_locations:
        geo_address_list = get_location_name(eachLocation)
        # geo_address_list = get_location_name(latitude=latitude, longitude=longitude)
        resolved_locations.append(geo_address_list)
        # print(resolved_locations)
    return resolved_locations


def get_location_name(location_dic):
    latitude = location_dic["lat"]
    longitude = location_dic["long"]
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = "latlng={lat},{lon}&sensor={sen}".format(
        lat=latitude,
        lon=longitude,
        sen='false'
    )
    final_url = url + "?" + params
    r = requests.get(final_url)
    geo_address_list = []
    name_list = []
    results = r.json()['results'][0]['address_components']
    # print(results)
    country = town = None
    geo_address_list.append(location_dic)
    for c in results:
        if "administrative_area_level_2" in c['types']:
            city_name1 = c['short_name']
            name_list.append(city_name1.lower())
        if "locality" in c['types']:
            city_name2 = c['long_name']
            name_list.append(city_name2.lower())
        if "administrative_area_level_1" in c['types']:
            area_name = c['long_name']
            name_list.append(area_name.lower())
        if "administrative_area_level_1" in c['types']:
            area_name_short = c['short_name']
            name_list.append(area_name_short.lower())
        if "country" in c['types']:
            country = c['short_name']
            geo_address_list.insert(0, country.lower().split(" "))
    geo_address_list.insert(2, name_list)
    # print(geo_address_list)
    return geo_address_list
