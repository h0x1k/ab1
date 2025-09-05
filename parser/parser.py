import json
import parser.translator as translator
from playwright.async_api import async_playwright
from logger import logger

class JSONfile():
    path = "parser/login.json"
    info = {
        "allbestbets": "",
        "line4bet": ""
    }

    @classmethod
    def edit_login_info(self, upd_info):
        self.info.update(upd_info)
        with open(self.path, "w", encoding = "utf-8") as file:
            json.dump(self.info, file, ensure_ascii = False, indent = 4)

    @classmethod
    def get_login_info(self):
        with open(self.path, 'r', encoding = 'utf-8') as file:
            self.info = json.load(file)
            return self.info

async def save_cookie_file(context, path):
    cookies = await context.cookies()
    with open(path, 'w', encoding = 'utf-8') as file:
        json.dump(cookies, file, ensure_ascii = False, indent = 4)

async def load_cookie_file(context, path):
    with open(path, 'r', encoding = 'utf-8') as file:
        cookies = json.load(file)
    await context.add_cookies(cookies)

async def login_allbestbets_using_cookie(context, page) -> bool:
    try: 
        await load_cookie_file(context, "parser/cookies/allbestbets_login.json")
    except:
        return False
    await page.goto("https://www.allbestbets.com/users/sign_in")
    await page.wait_for_timeout(1000)
    if page.url != "https://www.allbestbets.com/profile":
        return False
    return True
    
async def login_allbestbets_if_cookies_die(context, page) -> bool:
    try:
        info = JSONfile.get_login_info()
    except:
        return False
    login, password = info["allbestbets"].split(":")
    await page.goto("https://www.allbestbets.com/users/sign_in")
    await page.wait_for_timeout(2000)
    email_input = page.locator("#allbestbets_user_email")
    passwor_input = page.locator("#allbestbets_user_password")
    remember_me_input = page.locator("#allbestbets_user_remember_me")
    await email_input.fill(login)
    await passwor_input.fill(password)
    await remember_me_input.click()
    await page.keyboard.press("Enter")
    # await page.locator('button.sign_in').click()
    await page.wait_for_timeout(1000)
    if page.url != "https://www.allbestbets.com/profile":
        return False
    await save_cookie_file(context, "parser/cookies/allbestbets_login.json")
    return True

async def login_allbestbets(login_info: str) -> bool:
    login, password = login_info.split(':')
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless = False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.allbestbets.com/users/sign_in")
        await page.wait_for_timeout(2000)
        email_input = page.locator("#allbestbets_user_email")
        passwor_input = page.locator("#allbestbets_user_password")
        remember_me_input = page.locator("#allbestbets_user_remember_me")
        await email_input.fill(login)
        await passwor_input.fill(password)
        await remember_me_input.click()
        await page.keyboard.press("Enter")
        # await page.locator('button.sign_in').click()
        await page.wait_for_timeout(1000)
        if page.url != "https://www.allbestbets.com/profile":
            return False
        else:
            await page.locator(".lang-popup_btn-ru").click()
            await save_cookie_file(context, "parser/cookies/allbestbets_login.json")
            JSONfile.get_login_info()
            JSONfile.edit_login_info({"allbestbets": login_info})
            return True

async def get_sub_status_allbestbets() -> bool | None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless = False)
        context = await browser.new_context()
        page = await context.new_page()
        if not await login_allbestbets_using_cookie(context, page):
            if not await login_allbestbets_if_cookies_die(context, page):
                return None
        await page.wait_for_timeout(1000)
        elem = await page.query_selector(".prematchArbsPaidTill span")
        if elem:
            if await elem.get_attribute("class") == "":
                return True
        return False

async def parse_allbestbets(context, matches_in_db, diff, pint = "", cint = "") -> list:
    matches = []
    pro_search = []
    directories = []
    value_bet_filters = []

    page = await context.new_page()
    try:
        if not await login_allbestbets_using_cookie(context, page):
            if not await login_allbestbets_if_cookies_die(context, page):
                raise Exception("/allbestbets/ Ошибка авторизации, проблема с конфиг файлами или куки")
    except Exception as e:
        if "/allbestbets/" in e:
            raise e
        raise Exception("/allbestbets/ Ошибка авторизации, превишен лимит ожидания или проблемы с соединением")
    
    async def response_handler(response):
        nonlocal directories, pro_search, value_bet_filters
        if "directories?" in response.url:
            directories = await response.json()
        if "pro_search?" in response.url:
            pro_search = await response.json()
        if "value_bet_filters?" in response.url:
            for filter in await response.json():
                if filter['active'] == True:
                    value_bet_filters = filter
                    break

    page.on("response", response_handler)
    await page.goto("https://www.allbestbets.com/valuebets")
    await page.wait_for_timeout(3000)
    
    if pro_search == [] or directories == [] or value_bet_filters == []:
        raise Exception("/allbestbets/ Длительное время ожидания, проблемы с подключением.")

    if pro_search['arbs'] == []:
        logger.info("/allbestbets/ Список прогнозов пуст в данный момент")
        return []
    
    page_compare = await context.new_page()

    for arb in pro_search['arbs']:
        if arb['event_id'] in matches_in_db:
            continue
        bets = []
        for bet in pro_search['bets']:
            if bet['event_id'] == arb['event_id'] and str(bet['bookmaker_id']) in value_bet_filters['bookmakers2'] and bet['period_identifier'] in (0, 3, 4) and bet['market_and_bet_type'] in (1, 2, 11, 13, 17, 18, 19, 20, 21, 22, 23, 24):
                bets.append(bet)
        bet_diffs = []
        for bet in bets:
            bet_market = list(filter(lambda x: x['id'] == bet['market_and_bet_type'] , directories['market_variations']))[0]['market_id']
            url_for_bets_compare = f"https://www.allbestbets.com/compare#sports/{arb['sport_id']}/countries/{arb['country_id']}/leagues/{arb['league_id']}/events/{arb['event_id']}?market_id={bet_market}&period={bet['period_identifier']}"
            await page_compare.goto(url_for_bets_compare)
            await page.wait_for_timeout(3000)

            if bet['market_and_bet_type'] not in (1, 2, 11, 12, 13):
                if bet['market_and_bet_type'] == 18:
                    param_value = -bet['market_and_bet_type_param']
                else:
                    param_value = bet['market_and_bet_type_param']
                market_value = format(param_value, ".2f")
                select_menu = await page_compare.query_selector(f'.triggerBookmakers[data-value="{market_value}"]')
                if not select_menu:
                    logger.warning("/allbestbets/ Попытка найти несуществующий селектор")
                    continue
                try:
                    await select_menu.scroll_into_view_if_needed()
                    await page.wait_for_timeout(3000)
                    await select_menu.click()
                except Exception as e:
                    if "ElementHandle" in str(e):
                        logger.error("/allbestbets/ Элемента нет в структуре страницы!")
                        continue
                    else:
                        raise e

            await page.wait_for_timeout(1000)
            
            p_row = None
            c_row = None
            c_name = next((x['name'] for x in directories['bookmakers']['valuebets'] if x['id'] == bet['bookmaker_id']), None)

            bk_list = await page_compare.locator(".loaded.selected tr").all()
            for bk in bk_list:
                row = await bk.locator("td").all_inner_texts()
                row = list(map(lambda x: x.strip(), row))
                if row[0] == "Pinnacle":
                    p_row = row
                if row[0] == c_name:
                    c_row = row
                if p_row and c_row:
                    break
            
            # #П1 П2  1   X   2
            # (1, 2, 11, 12, 13)

            # #Ф1  Тб Тб1 Тб2
            # (17, 19, 21, 23)

            # #Ф2  Тм Тм1 Тм2
            # (18, 20, 22, 24)

            if p_row is None or c_row is None:
                logger.info("/allbestbets/ Букмекеры не найдены в таблице сравнения")
                continue
            
            if "-" in p_row or "-" in c_row:
                logger.info("/allbestbets/ Знак '-' в таблице сравнения")
                continue
            
            for i in range(1, len(p_row)):
                p_row[i] = float(p_row[i])
                c_row[i] = float(c_row[i])

            pinnacle_pay = p_row[-1]
            if bet['market_and_bet_type'] in (1, 17, 19, 21, 23, 11):
                pinnacle_value = p_row[1]
                currentb_value = c_row[1]
            if bet['market_and_bet_type'] in (2, 18, 20, 22, 24):
                pinnacle_value = p_row[2]
                currentb_value = c_row[2]
            if bet['market_and_bet_type'] == 13:
                pinnacle_value = p_row[3]
                currentb_value = c_row[3]

            # if pinnacle_pay > currentb_value:
            #     logger.info("/allbestbets/ КФ Pinnacle выше КФ сравниваемого бк")
            #     continue

            if pint != "" and cint != "":
                p_low, p_high = [float(x) for x in pint.split(":")]
                c_low, c_high = [float(x) for x in cint.split(":")]
                if p_low > pinnacle_value or p_high < pinnacle_value:
                    logger.info("/allbestbets/ КФ Pinnacle вне заданого диапазона")
                    continue
                if c_low > currentb_value or c_high < currentb_value:
                    logger.info("/allbestbets/ КФ сравниваемого бк вне заданого диапазона")
                    continue

            margin = 100 - pinnacle_pay
            fair = pinnacle_value*(1 + margin/100)
            a = pinnacle_value
            b = currentb_value
            difference = abs((a - b)/((a + b)/2))
            
            match = {
                "id":           arb['event_id'],
                "bookmaker":    c_name,
                "sport":        translator.get_sport_ru(next((x['name'] for x in directories['sports'] if x['id'] == bet['sport_id']), None)),
                "date":         translator.get_time_ru(bet['started_at']),
                "team1":        arb['team1_name'],
                "team2":        arb['team2_name'],
                "team1_ru":     arb['team1_name_ru'],
                "team2_ru":     arb['team2_name_ru'],
                "name":         arb['event_name'],
                "name_ru":      arb['event_name_ru'],
                "league":       arb['league'],
                "league_ru":    arb['league_ru'],
                "market":       bet["market_and_bet_type"],
                "market_val":   bet['market_and_bet_type_param'],
                "market_name":  translator.get_market_ru(bet["market_and_bet_type"], bet['market_and_bet_type_param']),
                "coefficient":  currentb_value,
                "difference":   difference,
                "fair":         format(fair, ".2f"),
                "pinnacle_pay": pinnacle_pay,
                "pinnacle_val": pinnacle_value,
                "p_row":        p_row,
                "c_row":        c_row,
                "url":          url_for_bets_compare
            }

            bet_diffs.append(match)
        
        if bet_diffs == []:
            logger.info(f"/allbestbets/ Матчи на событие {arb['event_id']} не прошли проверку")
            continue

        bet_max_diff = max(bet_diffs, key = lambda x: x['difference'])
        if bet_max_diff['difference'] > diff:
            matches.append(bet_max_diff)

    await page_compare.close()
    page.remove_listener("response", response_handler)
    return matches

# async def parse_line4bet(context, prev_matches):
#     page = await context.new_page()
#     if not await login_line4bet_using_cookies(context, page):
#         if not await login_line4bet_if_cookies_die(context, page):
#             raise Exception("/line4bet/ Ошибка авторизации")
    
#     needed_matches = []
#     for info in prev_matches:
#         bookmaker = "BetCity" if info['bookmaker'] == "Betcity" else info["bookmaker"]
#         match_name = info['name']
#         sport = "Киберспорт" if info['sport'] in ("Dota 2", "Counter-Strike") else info['sport']
        
#         await page.wait_for_load_state("domcontentloaded")
#         await page.wait_for_timeout(2000)
#         await page.locator(".tabs").locator(f"text=\"{bookmaker}\"").click()
#         await page.wait_for_timeout(2000)
#         await page.locator('.sport_menu').locator(f"text=\"{sport}\"").click()
#         await page.wait_for_timeout(2000)
#         # await page.wait_for_selector("#primary .box.visible .pages_pag")
#         pages = await page.locator("#primary .box:visible .pages_pag").first.locator('.pages').all()

#         if pages == []:
#             pages.append(None)

#         found_match = False
#         for page_ in pages:
#             if page_ != pages[0] and page_ != None:
#                 await page_.click()
#                 await page.wait_for_timeout(3000)
#             match_names_list = await page.locator(".event").all_inner_texts()
#             match_table_list = await page.locator(".event + *").all()
#             matches = [{'name': name, 'table': table} for name, table in zip(match_names_list, match_table_list)]
#             for match in matches:
#                 lin4bet_match_name: str = match['name'][17:].split(";")[0].strip()
#                 if translator.is_same_game(match_name, lin4bet_match_name, 75):
#                     found_match = True
#                     needed_matches.append(match)
#                     break
#             if found_match:
#                 break
#         if not found_match:
#             print("[Информация]: /line4bet/ Прогноз не найден")
#             needed_matches.append(None)
#     return needed_matches


async def parse(matches_in_db, diff=0.2, pint="", cint=""):
    # #П1 П2  1   X   2
    # (1, 2, 11, 12, 13)

    # #Ф1  Тб Тб1 Тб2
    # (17, 19, 21, 23)

    # #Ф2  Тм Тм1 Тм2
    # (18, 20, 22, 24)
    # import math
    # market = {
    #     1: 2,   # П1
    #     2: 3,   # П2
    #     11: 4,  # 1x
    #     13: 5,  # 2x
    #     12: 6,  # X
    #     19: 9,  # Тб
    #     20: 10, # Тм
    #     17: 12, # Ф1
    #     18: 14, # Ф2
    #     21: 16, # Тб1
    #     22: 17, # Тм1
    #     23: 19, # Тб2
    #     24: 20  # Тм2
    # }
    
    matches = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless = False)
        context = await browser.new_context()
        try:
            prev_matches = await parse_allbestbets(context, matches_in_db, diff, pint, cint)
            if prev_matches == []:
                return []
            
            matches = prev_matches
            
            # found_matches = await parse_line4bet(context, prev_matches)
            # if found_matches == []:
            #     return []
            
            # for f_match, p_match in zip(found_matches, prev_matches):
            #     if f_match is None:
            #         continue

            #     print("Найден:")
            #     print(p_match["date"], p_match["name"])
            #     print(f_match["name"])

            #     rows = (await f_match['table'].locator('tr').all())[1:]
            #     row = rows[-3]
            #     col = market[p_match['market']]
            #     coeff: str = await row.locator(f'td:nth-child({col})').inner_text()
            #     f_coeff = float(coeff.strip().replace(',', '.'))
                
            #     print(f"{p_match['coefficient']} vs {f_coeff}")
            #     if math.isclose(p_match['coefficient'], f_coeff, rel_tol=1e-9, abs_tol=0.0):
            #         matches.append(p_match)
            #     elif p_match['coefficient'] < f_coeff:
            #         p_match['coefficient'] = f_coeff
            #         matches.append(p_match)
            #     else:
            #         print("Скипнули")

        except Exception as e:
            logger.error(e)
    return matches

# async def get_sub_status_line4bet() -> bool | None:
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless = False)
#         context = await browser.new_context()
#         page = await context.new_page()

#         if not await login_line4bet_using_cookies(context, page):
#             if not await login_line4bet_if_cookies_die(context, page):
#                 return None
        
#         await page.goto("https://line4bet.ru/account/")
#         await page.wait_for_timeout(1000)
#         text = await page.locator(".cab_bttn_lite").inner_text()
#         if "Доступ активен" in text:
#             return True
#         return False

# async def login_line4bet_using_cookies(context, page) -> bool:
#     try:
#         await load_cookie_file(context, "parser/cookies/line4bet_login.json")
#     except:
#         return False
#     await page.goto("https://line4bet.ru/lines-5days/")
#     await page.wait_for_timeout(1000)
#     return True

# async def login_line4bet_if_cookies_die(context, page) -> bool:
#     try: 
#         info = JSONfile.get_login_info()
#     except:
#         return False
#     login, password = info["line4bet"].split(":")
#     await page.goto("https://line4bet.ru/lines-5days/")
#     await page.locator('.rcl-login').first.click()
#     await page.wait_for_timeout(5000)

#     await page.fill('input[placeholder="Логин"]', login)
#     await page.fill('input[placeholder="Пароль"]', password)
#     await page.locator(".rcl-checkbox-box").click()
#     await page.locator('#login-form-rcl').locator("text=\"Вход\"").click()
#     await page.wait_for_timeout(5000)

#     if "https://line4bet.ru/account/?user=" in await page.url:
#         await save_cookie_file(context, "parser/cookies/line4bet_login.json")
#         await page.locator("text=\"+5 дней\"").click()
#         return True
#     return False

# async def login_line4bet(login_info: str):
#     login, password = login_info.split(':')
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless = False)
#         context = await browser.new_context()
#         page = await context.new_page()

#         await page.goto("https://line4bet.ru/lines-5days/")
#         await page.locator('.rcl-login').first.click()
#         await page.wait_for_timeout(5000)
        
#         await page.fill('input[placeholder="Логин"]', login)
#         await page.fill('input[placeholder="Пароль"]', password)
#         await page.locator(".rcl-checkbox-box").click()
#         await page.locator('#login-form-rcl').locator("text=\"Вход\"").click()
#         await page.wait_for_timeout(5000)

#         if "https://line4bet.ru/account/?user=" in await page.url:
#             await save_cookie_file(context, "parser/cookies/line4bet_login.json")
#             JSONfile.get_login_info()
#             JSONfile.edit_login_info({"line4bet": login_info})
#             return True
#         return False

