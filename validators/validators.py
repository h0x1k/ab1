def validate_time_interval(interval: str) -> bool:
    """ Проверка времени в формате HH:MM-HH:MM """
    import re
    pattern = r"^([0-1][0-9]|2[0-3]):([0-5][0-9])-([0-1][0-9]|2[0-3]):([0-5][0-9])$"
    match = re.match(pattern, interval)
    if not match:
        return False
    return True

def validate_secounds(time: str) -> bool:
    try:
        int(time)
        return True
    except ValueError:
        return False

def validate_float(num: str) -> bool:
    try: 
        tmp = int(num)
        return True if 0 <= tmp <= 100 else False
    except ValueError:
        return False

def validate_login(info: str) -> bool:
    try:
        login, password = info.split(":")
    except ValueError:
        return False
    if login == "" or password == "":
        return False
    return True

def validate_timezone(timezone: str) -> bool:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        ZoneInfo(timezone)
        return True
    except ZoneInfoNotFoundError:
        return False

def validate_koef_interval(interval: str) -> bool:
    try:
        num_1, num_2 = interval.split(":")
        if num_1 == num_2:
            return False
        if float(num_1) > float(num_2):
            return False
        return True
    except:
        return False
