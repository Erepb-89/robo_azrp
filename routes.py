import json
from collections import namedtuple

Route = namedtuple('Route', [
    'name',
    'trajectories'])


def get_routes():
    with open("routes.json", 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        routes_dict = {}

        for route in json_data["routes"]:
            routes_dict[route["name"]] = Route(route.get("name"), route.get('trajectories'))

    return routes_dict


routes = get_routes()
# print(routes["rHomePosition_To_Helicopter1"].trajectories)
# print(routes["rHelicopter2Payload_To_HomePosition"].trajectories)
