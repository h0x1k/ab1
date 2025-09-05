import json

def edit_config_info(info, path = "config.json"):
    with open(path, "w", encoding = "utf-8") as file:
        json.dump(info, file, ensure_ascii = False, indent = 4)

def get_config_info(path):
    with open(path, 'r', encoding = 'utf-8') as file:
        return json.load(file)

config = get_config_info("config.json")