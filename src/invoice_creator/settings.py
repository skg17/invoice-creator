import json
import os

USER_SETTINGS_FILE = 'user_settings.json'

# Fetch user settings
def get_user_settings() -> dict:
    """Fetches the user settings from the 'user_settings.json' file.
    If the user settings file does not exist, prompts the user to enter the relevant data and creates it.

    :return: a dictionary containing the user settings.
    :rtype: dict
    """
    if os.path.isfile(USER_SETTINGS_FILE):
        with open(USER_SETTINGS_FILE, 'r') as file:
            user_settings = json.load(file)

    else:
        required_settings = ["full_name", "email", "address", "town", "postcode",
                             "control_str", "hourly_rate", "account_no", "sort_code"]
        
        user_settings = {key: input(f"Please enter {' '.join(key.split('_'))}: ") for key in required_settings}

        with open(USER_SETTINGS_FILE, 'w') as outfile:
            json.dump(user_settings, outfile)

    return user_settings