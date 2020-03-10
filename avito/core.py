from bs4 import BeautifulSoup as bs
from re import search, compile
from webbot import Browser
from time import sleep, perf_counter
from requests import get, Timeout
from sys import exc_info

from utils import log, save_error
from settings import SLEEP_TIME, TIMEOUT

# recentrecent_page_source = ''
IP_ERROR = False

def get_global(name):
    value = globals().get(name)
    #log('get', name, value)
    return value

def set_global(name, val):
    #log('set', name, val)
    if name in globals():
        globals()[name] = val

def retry(max_tries=3, sleep_multiplier=0, silent=False, save=True, quit=False):
    # decorator function for handling most web request
    def taker(func):
        def wrapper(*args, **kwargs):
            sleep_time = get_global('SLEEP_TIME') * sleep_multiplier
            message = []
            for n in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    message = [f'Exception in {func.__name__}:', str(e), exc_info(), f'{n+1} try of {max_tries}']
                    if not silent:
                        if sleep_time:
                            message += [f'next try in {sleep_time} seconds']
                        log(*message, sep='\n')
                    if sleep_time:
                        sleep(sleep_time)
                if get_global('IP_ERROR'): 
                    break
            if save and message:
                save_error(*message, sep='\n')
            if quit:
                exit(1)
        return wrapper
    return taker

@retry(max_tries=2, sleep_multiplier=1)
def get_page(url, proxy='', timeout_multiplier=3, bot=None):
    if bot:
        bot.set_page_load_timeout(TIMEOUT*timeout_multiplier)
        bot.go_to(url)
        page_source = bot.get_page_source()
    else:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        t = perf_counter()
        if proxy:
            response = get(url, headers=headers, timeout=TIMEOUT * timeout_multiplier, proxies={'https': 'http://' + proxy})
        else:
            response = get(url, headers=headers, timeout=TIMEOUT * timeout_multiplier,)
        assert (perf_counter() - t - 1) < TIMEOUT * timeout_multiplier, 'Timeout'
        sleep(1)
        page_source = response.text
    page = bs(page_source, 'html.parser')
    #if page.find('body'):
    #    set_global('recent_page_source', page.body.text)
    assert page_source, 'Пустая страница'
    assert '502 Bad Gateway' not in page_source, '502 Bad Gateway'
    if 'Проверьте настройки прокси' in page_source: 
        set_global('SLEEP_TIME', 0)
        set_global('IP_ERROR', True)
        raise Exception('Ошибка прокси')
    if 'Мы были вынуждены временно заблокировать доступ к сайту' in page_source:
        set_global('SLEEP_TIME', 0)
        set_global('IP_ERROR', True)
        raise Exception('Ваш IP заблокирован. Смените прокси сервер.' )
    return page

def check_connection(url, proxy='', timeout_multiplier=3):
    # check for internet connection
    log('Проверка подключения к интернету')
    assert get_page(url, proxy=proxy, timeout_multiplier=timeout_multiplier), 'Bad connection'

# @retry(max_tries=1, sleep_multiplier=1, silent=False, save=False, quit=True)
def check_app_status(app_key=0):
    # check if app is allowed to run
    page = get_page(f'https://denisgladunov.pythonanywhere.com/{app_key}')
    status = 0
    if page and page.text.isdigit():
        status = int(page.text)
    if not status:
        log('Доступ запрещен, обратитесь к разарботчику приложения. den.brovskiy@gmail.com')
        sleep(5)
        exit(1)

@retry(max_tries=3, quit=True)
def get_user_input():
    s_user_url = input('Введите url страницы.\n: ').strip()
    assert s_user_url and search('(?:https?:\/\/)?[A-z.-]+\.\w+\/', s_user_url), 'Проверьте правильность ввода url.\nUrl должен начинаться c "https://".\nПример: https://www.avito.ru/krasnodar/vakansii/administrativnaya_rabota-ASgBAgICAUSOC6aeAQ'
    return s_user_url, search('(?:https?:\/\/)?[A-z.-]+\.\w+\/', s_user_url)[0]

def extract_params(s_user_url):
    # params extraction
    if '?' in s_user_url and len(s_user_url.split('?')) > 1:
        s_url, s_params = s_user_url.split('?')
    else:
        s_url, s_params = s_user_url, ''
    return s_url, s_params

def get_current_page(s_params):
    # current page number extraction
    i_cur_page_num = 1
    if s_params and ('p=' in s_params):
        s_cur_page_num = search('(?!p=)\d+', s_params)[0]
        if s_cur_page_num and s_cur_page_num.isdigit():
            i_cur_page_num = int(s_cur_page_num)
    return i_cur_page_num

def get_last_page(s_url, i_cur_page_num, bot=None):
    # finding pagination element
    i_last_page_num = i_cur_page_num
    page = get_page(s_url, bot=bot)
    pager_selector = compile('pagination-root') #doesn't work with page.select('')
    pager = page.find_all(class_=pager_selector)
    if pager:
        # getting last page number
        pager_element = pager[0]
        last_page_selector = 'span:nth-last-child(2)'
        last_page = pager_element.select(last_page_selector)[0]
        if last_page and last_page.text.isdigit():
            i_last_page_num = int(last_page.text)
    return i_last_page_num

@retry(max_tries=2, sleep_multiplier=1)
def get_item_urls(s_page_url, bot=None):
    # getting urls of avito items on each page
    l_item_urls = []
    page = get_page(s_page_url, bot=bot)
    link_selector = 'div.item-with-contact h3 > a'
    l_links = page.select(link_selector)
    if l_links:
        l_item_urls = [link.get('href') for link in l_links if link.get('href','')]
    return l_item_urls

@retry(max_tries=2, sleep_multiplier=10)
def walk_pages_and_do(s_url, page_range, func=None, args=[], kwargs={}, bot=None):
    # walking through pages and calling func
    for n in page_range:
        log('страница:', n, 'из', len(page_range))
        if get_global('IP_ERROR'): 
            return
        s_page_url = f'{s_url}&p={n}'
        kwargs['s_page_url'] = s_page_url
        yield func(*args, **kwargs)

# extraction of information in each item =========================================================

@retry(max_tries=2, sleep_multiplier=1)
def get_employer_address(url, field_selectors, bot=None):
    assert url, f'Invalid url: {url}'
    log(url)
    employer_page = get_page(url, bot=bot)
    # scraping fields
    employer_address = ''
    selection = employer_page.select(field_selectors['employer_address'])
    if selection:
        employer_address = selection[0].text
    return employer_address

@retry(max_tries=2, sleep_multiplier=1)
def get_item_data(i, domain, item_url, selectors, csv_data = '', bot=None):
    # scraping fields from each item and saving them in csv file
    page_url = domain + item_url
    if page_url in csv_data:
        return
    log(f'{i}: {page_url}')
    item_data = {}
    item_page = get_page(page_url, bot=bot)
    item_data['avito_url'] = page_url
    for key, selector in selectors.items():
        if get_global('IP_ERROR'):
            return
        if key =='employer_address':
            continue
        selection = item_page.select(selector)                
        if selection:
            if key == 'img_url':
                img = selection[0]
                item_data['img_url'] = img.get('src','')
            elif key == 'employer_url':
                employer_link = selection[0]
                employer_url = employer_link.get('href','')
                item_data['employer_address'] = ''
                if employer_url:
                    item_data['employer_address'] = get_employer_address(domain + employer_url, selectors, bot=bot)
            else:
                item_data[key] = selection[0].text
    return item_data