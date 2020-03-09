# -*- coding: utf-8 -*-
# python 3.8.1
from bs4 import BeautifulSoup as bs
from re import search, compile
from webbot import Browser
from argparse import Namespace
from datetime import datetime
from time import sleep, perf_counter
from requests import get
from subprocess import Popen as sp_open
from subprocess import PIPE as sp_PIPE
from subprocess import STDOUT as sp_STDOUT
from os import path

recent_page_source = ''
checkbox = []
sleep_time = 5

def get_recent_page():
    global recent_page_source
    return recent_page_source

def set_recent_page(val):
    global recent_page_source
    recent_page_source = val

def get_checkbox():
    global checkbox
    return checkbox

def set_checkbox(val):
    global checkbox
    checkbox = val

def get_sleep_time():
    global sleep_time
    return sleep_time

def set_sleep_time(n):
    global sleep_time
    sleep_time = n

def log(*args, **kwargs):
    # a custom print function to distinct app's console output from other's 
    print('-'*50)
    print(*args, **kwargs)
    print('-'*50)

def read_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = file.read()
        return data

def write_data(filepath, data, mode='w'):
    with open(filepath, mode, encoding='utf-8') as file:
            file.write(data)

def load_data(filepath):
    data = ''
    try:
        assert path.exists(filepath), f'Не удается найти файл по указанному пути {filepath}'
        return read_data(filepath)
    except Exception as e:
        log(e)
        write_data(filepath, '')
        log('Файл создан.')
        return data

def save_data(filepath, data, end='\n'):
    if data not in load_data(filepath):
        write_data(filepath, data + end, mode='a')

def erase_data(filepath):
    if load_data(filepath):
        write_data(filepath, '')

def save_error(exception=None, max_tries=0, sleep_time=0, funcname='', *args, **kwargs):
    # saving error report after max tries in retry decorator been reached
    recent_page_source = get_recent_page()
    s_date = str(datetime.now())
    report = f"{s_date=}\n{funcname=}; {args=}; {kwargs=}\n{max_tries=}; {sleep_time=}\n{str(exception)=}\n"
    report += f"{recent_page_source=}\n"
    report += f"{'-'*50}"
    save_data('errors.txt', report)

def retry(max_tries=3, sleep_multiplier=0, silent=False, save=True, quit=False):
    # decorator function for handling most web request
    def taker(func):
        def wrapper(*args, **kwargs):
            sleep_time = get_sleep_time()
            exc = None
            for n in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if not silent:
                        log(f'Exception in {func.__name__}: {e}\n {n+1} try of {max_tries}')
                    if sleep_time:
                        log(f'next try in {sleep_time} seconds')
                        sleep(sleep_time * sleep_multiplier)
                    exc = e
            if save:
                save_error(
                    exception=exc, 
                    max_tries=max_tries, 
                    sleep_time=sleep_time, 
                    funcname=func.__name__, 
                    args=args, 
                    kwargs=kwargs   
                )
            if quit:
                exit(1)
        return wrapper
    return taker

@retry(max_tries=2, sleep_multiplier=1)
def get_page(url, proxy='', timeout=300, bot=None):
    # getting page source of given url
    # global recent_page_source
    # global set_sleep_time
    if bot:
        bot.go_to(url)
        page_source = bot.get_page_source()
    else:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        t = perf_counter()
        if proxy:
            response = get(url, headers=headers, timeout=timeout, proxies={'https': 'http://' + proxy})
        else:
            response = get(url, headers=headers, timeout=timeout,)
        assert (perf_counter() - t) < timeout, 'Timeout'
        sleep(1)
        page_source = response.text
    page = bs(page_source, 'html.parser')
    if page.find('body'):
        set_recent_page(page.body.text)
    assert page_source, 'Пустая страница'
    assert '502 Bad Gateway' not in page_source, '502 Bad Gateway'
    if 'Проверьте настройки прокси' in page_source: 
        set_sleep_time(0)
        raise Exception('Ошибка прокси')
    if 'Мы были вынуждены временно заблокировать доступ к сайту' in page_source:
        set_sleep_time(0)
        raise Exception('Ваш IP заблокирован. Смените прокси сервер.' )
    return page

# @retry(max_tries=3, sleep_multiplier=1, quit=True)
def check_connection(url, proxy='', timeout=300):
    # check for internet connection
    log('Проверка подключения к интернету')
    assert get_page(url, proxy=proxy, timeout=timeout), 'Bad connection'

@retry(max_tries=3, sleep_multiplier=1, silent=True, save=False, quit=True)
def check_app_status(app_key=0):
    # check if app is allowed to run
    page = get_page(f'https://denisgladunov.pythonanywhere.com/{app_key}')
    status = 0
    if page and page.text.isdigit():
        status = int(page.text)
    assert status, 'Доступ запрещен, обратитесь к разарботчику приложения. den.brovskiy@gmail.com'

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

def set_proper_filename(string):
    # setting up proper filename based on user url
    banned_filename_symbols = '\/:*?<>|"' # windows
    filename = f'{string}.csv'
    for symbol in banned_filename_symbols:
        filename = filename.replace(symbol, '-')
    return filename

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

@retry(max_tries=3, sleep_multiplier=1)
def get_item_urls(s_page_url, bot=None):
    # getting urls of avito items on each page
    l_item_urls = []
    page = get_page(s_page_url, bot=bot)
    link_selector = 'div.item-with-contact h3 > a'
    l_links = page.select(link_selector)
    if l_links:
        l_item_urls = [link.get('href') for link in l_links if link.get('href','')]
    return l_item_urls

@retry(max_tries=3, sleep_multiplier=10)
def walk_pages_and_do(s_url, page_range, func=None, args=[], kwargs={}, bot=None):
    # walking through pages and calling func
    for n in page_range:
        log('страница:', n, 'из', len(page_range))
        s_page_url = f'{s_url}&p={n}'
        kwargs['s_page_url'] = s_page_url
        yield func(*args, **kwargs)

# extraction of information in each item =========================================================

def save_data_to_csv(columns, data, filename):
    # saving to csv (a;b;c\nd;e;f)
    log(f'сохранение данных')
    string = ''  
    for key in columns:
        s = f'{data.get(key, "").strip()}'
        if ';' in s:
            s = s.replace(';', ' ')
        if '\n' in s:
            s = s.replace('\n', '  ')
        string += (s + (';' if key != columns[-1] else ''))
    save_data(filename, string)

@retry(max_tries=3, sleep_multiplier=1)
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

@retry(max_tries=3, sleep_multiplier=1)
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

def main(proxy, s_user_url, domain, session=0):

    s_url, s_params = extract_params(s_user_url)
    i_cur_page_num = get_current_page(s_params)
    i_last_page_num = get_last_page(s_user_url, i_cur_page_num, bot=None)
    s_params = s_params.replace(f'p={i_cur_page_num}', '')
    s_url = f'{s_url}?{s_params}'
    filename = set_proper_filename(s_url)

    # start browser
    bot = Browser(showWindow=False, proxy=proxy)

    # getting urls extracted on each page of a paginated topic
    page_range = range(i_cur_page_num, i_last_page_num + 1)
    if session and load_data('urls_'+filename):
        l_item_urls = load_data('urls_'+filename).split('\n')
    else:
        l_item_urls = []
        for l_urls in walk_pages_and_do(s_url, page_range, func=get_item_urls, kwargs={'bot': bot}, bot=bot):
            save_data('urls_'+filename, '\n'.join(l_urls))
            l_item_urls.extend(l_urls)

    assert len(l_item_urls), f'{len(l_item_urls)} ссылок'
    log('Всего', len(l_item_urls), 'ссылок')

    # extraction of information in each item =========================================================

    # selectors of elements to scrape from each item (copied straight from chrome dev tools :D)
    selectors = {
        'id': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-search-info-redesign > span',

        'header': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-title-info.js-item-view-title-info > div > div.title-info-main > h1 > span',
        'description': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-main.js-item-view-main > div:nth-child(3) > div > div > p',

        'price': '#price-value > span > span.js-item-price',

        'employer': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-seller-info.js-item-view-seller-info > div > div.seller-info-prop.js-seller-info-prop_seller-name.seller-info-prop_layout-two-col > div.seller-info-col > div:nth-child(1) > div > a',

        'employer_url': 'div.item-view-content div.seller-info-name > a',

        'employer_address': 'body > div.item-view-page-layout > div.l-content.clearfix > div > div > span > div > div.styles-side-2pjZi > div > div.styles-summary-info-1YdLU > div:nth-child(3)',

        'img_url': 'div.gallery-img-frame > img'
    }

    # column names to save in csv
    column_names = ['id', 'header', 'description', 'price', 'employer', 'employer_address', 'img_url', 'avito_url']

    csv_data = load_data(filename)

    # walking through each avito item
    for i, item_url in enumerate(l_item_urls):
        item_data = get_item_data(i, domain, item_url, selectors, csv_data=csv_data, bot=bot)
        if item_data:
            assert any([item_data[key] for key in item_data if key != 'avito_url'])
            save_data_to_csv(column_names, item_data, filename)

    if bot: bot.quit()
    log('Готово')

if __name__ == '__main__':
    # erase_data('errors.txt')
    s_user_url, domain = get_user_input()

    check_connection(s_user_url, timeout=30)
    check_app_status(app_key=1)

    proxies = load_data('proxies.txt').split(',')
    bad_proxies = load_data('bad_proxies.txt')

    for i in range(len(proxies) + 1):
        proxy = ''
        if i:
            proxy = proxies[i-1]
            if proxy in bad_proxies:
                continue
            print(f'using proxy {proxy}')
        try:
            check_connection(s_user_url, proxy=proxy, timeout=30)
            main(proxy, s_user_url, domain, session=i)
            break
        except Exception as e:
            log(e)
            save_data('bad_proxies.txt', proxy, end=',')
