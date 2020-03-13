from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from bs4 import BeautifulSoup as bs
from re import search, compile
from webbot import Browser
from time import sleep, perf_counter
from requests import get, Timeout
from requests.exceptions import ProxyError
from sys import exc_info
from collections import deque

from utils import log, load_data, save_data, save_data_to_csv, save_error
from settings import HEADLESS, USE_BOT, WEBDRIVERPATH, SLEEP_TIME, TIMEOUT, COLUMN_TITLES, SELECTORS


# recent_page_source = ''
USER_SLEEP_TIME = SLEEP_TIME
PROXY_ERROR = False


# global ==========================


def new_global(name: str, value: Any) -> None:
    globals()[name] = value


def get_global(name: str) -> Any:
    value: Any = globals().get(name)
    #log('get', name, value)
    return value


def set_global(name: str, value: Any) -> None:
    #log('set', name, val)
    if name in globals():
        globals()[name] = value


# errors ==========================


class MyProxyError(Exception):
    def __init__(self, message=''):
        id = 'Proxy error: '
        super().__init__(id + message)


class ConnectionError(Exception):
    def __init__(self, message):
        id = 'Connection error: '
        super().__init__(id + message)


def check_connection(url: str = 'https://support.avito.ru/', silent:bool = False) -> bool:
    "check for internet connection"
    log('Проверка подключения к интернету')
    if get_page(url, check_proxy=False, silent=True):
        return True
    else:
        log('Ошибка подключения')
        return False


def check_page_for_errors(page_source: str) -> bool:
    has_errors = False  # no errors
    if not page_source:
        log('Пустая страница')
        has_errors = True
    if '502 Bad Gateway' in page_source:
        log('502 Bad Gateway')
        has_errors - True
    if 'Проверьте настройки прокси' in page_source:
        set_global('SLEEP_TIME', 0)
        set_global('PROXY_ERROR', True)
        log('Ошибка прокси')
        has_errors = True
    if 'Доступ с Вашего IP временно ограничен' in page_source:
        set_global('SLEEP_TIME', 0)
        set_global('PROXY_ERROR', True)
        log('Доступ с Вашего IP временно ограничен. Смените прокси сервер.')
        has_errors = True
    return has_errors


def check_proxy_error():
    "checking if proxy error is up"
    PROXY_ERROR = get_global('PROXY_ERROR')
    if PROXY_ERROR:
        change_proxy()
        acceptable = check_connection()
        if acceptable:
            set_global('PROXY_ERROR', False)
            return False
        else:
            return check_proxy_error()
    else:
        return False


# proxy ==========================

def load_proxies():
    proxy_list = load_data('proxies.txt').split(',')
    proxies = deque(proxy_list)
    return proxies


def change_proxy():
    # proxies must be formatted: 182.52.238.111:30098,103.105.77.22:8181,
    # bad proxies will be updated and skipped next time
    proxies: deque = get_global('PROXIES')
    bad_proxies: str = load_data('bad_proxies.txt')
    while proxies:
        proxy: str = proxies.popleft()
        if proxy in bad_proxies:
            continue
        #log(f'checking proxy {proxy}')
        try:
            old_proxy: str = get_global('PROXY')
            save_data('bad_proxies.txt', old_proxy, end=',')
            set_global('PROXY', proxy)
            set_global('PROXY_ERROR', False)
            # set_global('SLEEP_TIME', USER_SLEEP_TIME)
            if USE_BOT:
                log('Reloading bot')
                get_global('BOT').close()
                set_global('BOT', Browser(headless=HEADLESS,
                                          proxy=proxy, driverpath=WEBDRIVERPATH))
            return
            #acceptable = check_connection()
            #if acceptable:
            #    log(f'using proxy {proxy}')
            #    set_global('PROXIES', proxies)
            #    return
            #else:
            #    save_data('bad_proxies.txt', proxy, end=',')
            #    set_global('PROXY', old_proxy)
            #    set_global('PROXY_ERROR', True)
        except Exception as e:
            log(e)
            change_proxy()
    raise ProxyError('Все прокси использованы.')


# other ==============================


def retry(max_tries: int = 3, sleep_multiplier: int = 0, silent: bool = False, save: bool = True, quit: bool = False) -> Callable:
    'decorator function for handling most web request'
    def taker(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            sleep_time = get_global('SLEEP_TIME') * sleep_multiplier
            message: List[Union[str, Tuple]] = []
            for n in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except (MyProxyError, ProxyError, ConnectionError, OSError, Timeout) as e:
                    # message = [f'Exception in {func.__name__}:', 
                    #               str(e), exc_info(), f'{n+1} try of {max_tries}']
                    message = [str(e)]
                    if not silent:
                        if sleep_time:
                            message += [f'next try in {sleep_time} seconds']
                        log(*message, sep='\n')
                    if sleep_time:
                        sleep(sleep_time)
            if save and message:
                save_error(*message, sep='\n')
            if quit:
                exit(1)
        return wrapper
    return taker


@retry(max_tries=1, sleep_multiplier=1, silent=False, save=False, quit=True)
def check_app_status(app_key: int = 0) -> None:
    "checking if app is allowed to run"
    acceptable = check_connection(f'https://denisgladunov.pythonanywhere.com/appkey/{app_key}', silent= True)
    if acceptable:
        page = get_page(
            f'https://denisgladunov.pythonanywhere.com/appkey/{app_key}', silent = True)
        status: int = 0
        if page and page.text.isdigit():
            status = int(page.text)
        if not status:
            log('Доступ запрещен, обратитесь к разарботчику приложения. den.brovskiy@gmail.com')
            sleep(5)
            exit(1)
    else:
        raise ConnectionError("Connection error ")


# extracting info from user input =======================================


@retry(max_tries=3, quit=True)
def get_user_input() -> Tuple[str, str]:
    "getting url and domain from user input"
    user_url: str = input('Введите url страницы.\n: ').strip()
    assert user_url and search(
        r'(?:https?:\/\/)?[A-z.-]+\.\w+\/', user_url), 'Проверьте правильность ввода url.\nUrl должен начинаться c "https://".\nПример: https://www.avito.ru/krasnodar/vakansii/administrativnaya_rabota-ASgBAgICAUSOC6aeAQ'
    domain: str = search(r'(?:https?:\/\/)?[A-z.-]+\.\w+\/', user_url)[0]
    log(domain)
    return user_url, domain


def extract_params(user_url: str) -> Tuple[str, str]:
    "params extraction from url"
    if '?' in user_url and len(user_url.split('?')) > 1:
        url, params = user_url.split('?')
    else:
        url, params = user_url, ''
    return url, params


def get_current_page(params: str) -> int:
    "current page number extraction"
    i__cur_page_num: int = 1
    if params and ('p=' in params):
        s__cur_page_num: str = search(r'(?!p=)\d+', params)[0]
        if s__cur_page_num and s__cur_page_num.isdigit():
            i__cur_page_num = int(s__cur_page_num)
    return i__cur_page_num


def get_last_page(url: str, cur_page_num: int) -> int:
    "getting last page number for further iteration through pages"
    # finding pagination element
    i__last_page_num = cur_page_num
    page = get_page(url)
    # doesn't work with page.select('')
    pager_selector = compile('pagination-root')
    pager: List[bs] = page.find_all(class_=pager_selector)
    if pager:
        # getting last page number
        pager_element: bs = pager[0]
        last_page_selector = 'span:nth-last-child(2)'
        last_page: bs = pager_element.select(last_page_selector)[0]
        if last_page and last_page.text.isdigit():
            i__last_page_num = int(last_page.text)
    return i__last_page_num


# scraping ======================================


@retry(max_tries=2, sleep_multiplier=1)
def get_page(url: str, timeout_multiplier: int = 3, check_proxy:bool=True, silent:bool=False) -> bs:
    "requesting url, if timeouts ok getting it's page source, returning BeautifulSoup object"
    proxy_has_error = False
    if check_proxy:
        proxy_has_error = check_proxy_error()
    if not proxy_has_error:
        bot = get_global('BOT')
        PROXY = get_global('PROXY')
        # TODO: prepend proxy to url when url is logged
        if not silent:
            log('proxy:', PROXY, 'url:', url)
        # PROXY_ERROR quickfix, TODO: set new proxy to bot on the fly
        page_source = ''
        if bot:
            bot.set_timeout(TIMEOUT*timeout_multiplier)
            bot.go_to(url)
            page_source = bot.get_page_source()
        else:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
            response = None
            t = perf_counter()
            try:
                if PROXY:
                    response = get(url, headers=headers, timeout=TIMEOUT *
                                timeout_multiplier, proxies={'https': 'http://' + PROXY})
                else:
                    response = get(url, headers=headers,
                                timeout=TIMEOUT * timeout_multiplier)
            except (OSError, Timeout) as e:
                log(e)
                change_proxy()
                return get_page(url, timeout_multiplier=timeout_multiplier, check_proxy=check_proxy)
            # this assertion is for cases when timeout doesn't break the connection for some reason
            # in this case connection will be considered bad if specified timeout was exceeded
            if (t_ := perf_counter() - t - 1) > TIMEOUT * timeout_multiplier:
                log(f'Время ожидания превышено. {int(t_)}')
                change_proxy()
                return get_page(url, timeout_multiplier=timeout_multiplier, check_proxy=check_proxy)
            if response:
                page_source = response.text
            else:
                log(f'Нет ответа от сервера.')
                change_proxy()
                return get_page(url, timeout_multiplier=timeout_multiplier, check_proxy=check_proxy)
        has_errors = check_page_for_errors(page_source)
        if has_errors:
            change_proxy()
            return get_page(url, timeout_multiplier=timeout_multiplier, check_proxy=check_proxy)
        page = bs(page_source, 'html.parser')
        return page
    else:
        raise ProxyError('Unresolved proxy error')


# url extraction from each page =====================================


def get_urls_from_page(page: bs = None) -> List[str]:
    "getting urls of avito items from given page"
    item_urls: List[str] = []
    link_selector = 'div.item-with-contact h3 > a'
    links: List[bs] = page.select(link_selector)
    if links:
        item_urls = [link.get('href', '')
                     for link in links if link.get('href', '')]
        DOMAIN = get_global('DOMAIN')
        item_urls = [DOMAIN + url for url in item_urls]
    return item_urls


@retry(max_tries=2, sleep_multiplier=10)
def walk_pages_and_do(url: str, page_range: range, func: Callable = None, args=[], kwargs={}) -> Any:
    "walking through pages and calling func"
    for n in page_range:
        log('страница:', n, 'из', len(page_range))
        page_url = f'{url}&p={n}'
        page: bs = get_page(page_url)
        yield func(*args, page=page, **kwargs)
        sleep(SLEEP_TIME)


def collect_item_urls(new_url: str, page_range: range = range(1), item_urls=[]) -> List[str]:
    "getting urls extracted on each page if topic is paginated. Otherwise from current page"
    URLS_FILENAME = get_global('URLS_FILENAME')
    for ls__urls in walk_pages_and_do(new_url, page_range, func=get_urls_from_page):
        save_data(URLS_FILENAME, '\n'.join(ls__urls))
        item_urls.extend(ls__urls)
    assert len(item_urls), f'{len(item_urls)} ссылок'
    log('Всего', len(item_urls), 'ссылок')
    return item_urls


# extraction of information in each item =========================================================


@retry(max_tries=2, sleep_multiplier=1)
def get_employer_address(url: str, selectors: Dict[str, str], bot: Optional[Browser] = None) -> str:
    assert url, f'Invalid url: {url}'
    log(url)
    # scraping fields
    employer_address = ''
    if employer_page := get_page(url):
        if selection := employer_page.select(selectors['employer_address']):
            employer_address = selection[0].text
    return employer_address


@retry(max_tries=2, sleep_multiplier=1)
def get_item_data(item_page: bs, selectors: Dict[str, str]) -> Optional[Dict[str, str]]:
    "scraping fields by selectors from each item and saving them in csv file"
    item_data: Dict[str, str] = {}
    if item_page:
        if link := item_page.find('link', rel='canonical'):
            item_data['avito_url'] = link.get('href', '')
        for key, selector in selectors.items():
            if key == 'employer_address':
                continue
            selection: List = item_page.select(selector)
            if selection:
                if key == 'img_url':
                    img: bs = selection[0]
                    item_data['img_url'] = img.get('src', '')
                elif key == 'employer_url':
                    employer_link: bs = selection[0]
                    employer_url: str = employer_link.get('href', '')
                    item_data['employer_address'] = ''
                    if employer_url:
                        item_data['employer_address'] = get_employer_address(
                            get_global('DOMAIN') + employer_url, selectors)
                else:
                    item_data[key] = selection[0].text
    return item_data


@retry(max_tries=3, sleep_multiplier=1)
def fetch_data(item_urls: List[str]):
    # walking through each avito item
    DATA_FILENAME = get_global('DATA_FILENAME')
    csv_data = load_data(DATA_FILENAME)
    for i, item_url in enumerate(item_urls):
        if item_url in csv_data:
            continue
        log(f'{i}: {item_url}')
        item_page = get_page(item_url)
        item_data = get_item_data(item_page, SELECTORS)
        if item_data:
            [print(f'{key}: {val}') for key, val in item_data.items()]
            if any([item_data.get(key, '')
                    for key in item_data if key != 'avito_url']):
                save_data_to_csv(COLUMN_TITLES, item_data, DATA_FILENAME)
