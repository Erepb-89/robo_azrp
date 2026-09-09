import json
from collections import namedtuple

Action = namedtuple('Action', [
    'name',
    'commands'])

Command = namedtuple('Command', [
    'name',
    'cmd_type'])


def get_actions():
    with open("actions_2.json", 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        actions_dict = {}

        for action in json_data["actions"]:
            actions_dict[action["name"]] = Action(
                action.get("name"),
                [Command(command.get("name"),
                         command.get("cmd_type")) for command in action.get('commands')])

    return actions_dict


actions = get_actions()
# print(actions["aVTOL2_To_VTOL2Battery"].commands)
# print(actions["aVTOL2Battery_To_VTOL2"].commands[0].name)
