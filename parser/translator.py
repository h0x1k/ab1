import time
from unidecode import unidecode
from rapidfuzz.fuzz import ratio
from metaphone import doublemetaphone
import re

def get_time_ru(timestamp):
    months_ru = {
        'Jan': 'янв', 'Feb': 'фев', 'Mar': 'мар',
        'Apr': 'апр', 'May': 'май', 'Jun': 'июн',
        'Jul': 'июл', 'Aug': 'авг', 'Sep': 'сен',
        'Oct': 'окт', 'Nov': 'ноя', 'Dec': 'дек'
    }
    formatted = time.strftime("%d %b %H:%M", time.localtime(timestamp))
    for en, ru in months_ru.items():
        if en in formatted:
            formatted = formatted.replace(en, ru)
            break
    return formatted

def get_sport_ru(key):
    sports = {
        "Soccer": "Футбол",
        "Basketball": "Баскетбол",
        "Tennis": "Теннис",
        "Hockey": "Хоккей",
        "Volleyball": "Волейбол",
        "Dota 2": "Dota 2",
        "Counter-Strike": "Counter-Strike"
    }
    return sports[key]

def get_market_ru(id, val):
    markets = {
        1:  "П1",  2:  "П2",  11: "1",   13: "2",  12: "X",
        19: "Тб",  20: "Тм",  17: "Ф1",  18: "Ф2",
        21: "Тб1", 22: "Тм1", 23: "Тб2", 24: "Тм2"
    }
    market_str = markets[id]
    if id not in (1, 2, 11, 12, 13):
        market_str = market_str + f"({val})"
    return market_str

def is_same_game(orig: str, final: str, threshold: int = 80):
    e_orig = re.sub(r"[,']", "", orig)
    e_orig = re.sub(r"\d+", "", e_orig)

    e_final = re.sub(r"[,']", "", final)
    e_final = re.sub(r"\d+", "", e_final)

    team1_orig, team2_orig = [unidecode(x.strip()).split() for x in e_orig.lower().split(" - ")]
    team1_final, team2_final = [unidecode(x.strip()).split() for x in e_final.lower().split(" - ")]

    def find_matches_in_team_name(team_orig, team_final, threshold):
        match_count = 0
        for t_word in team_final:
            for word in team_orig:
                # Lexic
                similarity = ratio(t_word, word)
                if similarity >= threshold:
                    # Phonetic
                    code1 = set(doublemetaphone(t_word))
                    code2 = set(doublemetaphone(word))
                    if bool(code1 & code2):
                        match_count += 1
                        break
        return match_count
                
    team1_matches = find_matches_in_team_name(team1_orig, team1_final, threshold)
    team2_matches = find_matches_in_team_name(team2_orig, team2_final, threshold)

    if team1_matches/len(team1_orig) > 0.4 and team2_matches/len(team2_orig) > 0.4:
        return True
    return False