# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup as bs
from re import search, compile
from webbot import Browser
from argparse import Namespace
import datetime as dt
from time import sleep
from requests import get
from subprocess import Popen as sp_open
from subprocess import PIPE as sp_PIPE
from subprocess import STDOUT as sp_STDOUT
import csv

date = dt.datetime.now()

def log(*args, **kwargs):
    print('-'*50)
    print(*args, **kwargs)
    print('-'*50)

try:
    # check for internet connection
    log('Проверка подключения к интернету')
    s_connection = sp_open(['ping', '8.8.8.8'], shell=True, stdout=sp_PIPE, stderr=sp_STDOUT).stdout.read()
    assert b'100% loss' not in s_connection, 'Проверьте подключение к интернету.'
except Exception as e:
    print('Exception:', e)
    sleep(10)
    exit(1)
# lasy password protection
response = get('https://time100.ru')
page = bs(response.text, 'html.parser')
selection = page.select('#wrap > div > div:nth-child(2) > div > div.text-center.maindate')
element = selection[0]
if element.text == 'сегодня: 09 марта 2020 года, суббота':
    try:
        with open('password.txt', 'r', encoding='utf-8') as file:
            password = file.read().strip()
    except:
        password = input('Введите пароль чтобы продолжить: ')
    if password != '123454321':
        log('Пароль неверный.')
        sleep(10)
        exit()
    else:
        with open('password.txt', 'w', encoding='utf-8') as file:
            file.write('123454321')
        log('Добро пожаловать!')

def get_user_input():
    for _ in range(10):
        try:
            #s_user_url = 'https://www.avito.ru/krasnodar/vakansii/administrativnaya_rabota-ASgBAgICAUSOC6aeAQ'
            s_user_url = input('Введите url страницы.\n: ').strip()
            # domain extraction
            domain = ''
            assert s_user_url and search('(?:https?:\/\/)?[A-z.-]+\.\w+\/', s_user_url), 'Проверьте правильность ввода url.'
            return s_user_url, search('(?:https?:\/\/)?[A-z.-]+\.\w+\/', s_user_url)[0]
        except Exception as e:
            log(e, 'Url должен начинаться c "https://". Пример: https://www.avito.ru/krasnodar/vakansii/administrativnaya_rabota-ASgBAgICAUSOC6aeAQ')
    print('Превышено максимальное количество попыток ввода.')
    sleep(10)
    exit(1)

s_user_url, domain = get_user_input()
# params extraction
if '?' in s_user_url and len(s_user_url.split('?')) > 1:
    s_url, s_params = s_user_url.split('?')
else:
    s_url, s_params = s_user_url, ''
# setting up proper filename based on query for extracted info 
banned_filename_symbols = '\/:*?<>|"'
filename = f'{s_url}?{s_params}.csv'
for symbol in banned_filename_symbols:
    filename = filename.replace(symbol, '-')
# current page number extraction
if s_params and ('p=' in s_params):
    s_cur_page_num = search('(?!p=)\d+', s_params)[0]
    if s_cur_page_num and s_cur_page_num.isdigit():
        s_params = s_params.replace('p=' + s_cur_page_num, '')
        i_cur_page_num = int(s_cur_page_num)
else:
    i_cur_page_num = 1
# default last page number 
i_last_page_num = i_cur_page_num
# start browser
bot = Browser(showWindow=False)
# initial try to connect to tthe target url. max tries = 100
for _ in range(100):
    try:
        bot.go_to(f'{s_url}?{s_params}')
        # namespace is a monkey patch due to lack of time
        response = Namespace(text=bot.get_page_source())
        assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Ваш IP заблакоирован. Смените прокси сервер.'
        if response and response.text:
            page = bs(response.text, 'html.parser')
            # finding pagination element
            pager_selector = compile('pagination-root') #doesn't work with page.select('')
            pager = page.find_all(class_=pager_selector)
            if pager:
                # getting last page number
                pager_element = pager[0]
                last_page_selector = 'span:nth-last-child(2)'
                last_page = pager_element.select(last_page_selector)[0]
                if last_page and last_page.text.isdigit():
                    i_last_page_num = int(last_page.text)
        break
    except Exception as e:
        log('Exception:', e)
        log(f'Начальна попытка подключения: новая попытка ({_+1})')

# list for urls extrcted on each page of a paginated topic
l_item_urls = []

def get_item_urls(s_page_url):
    for _ in range(100):
        try:
            bot.go_to(s_page_url)
            # namespace is a monkey patch due to lack of time
            response = Namespace(text=bot.get_page_source())
            assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Ваш IP заблакоирован. Смените прокси сервер.'
            page = bs(response.text, 'html.parser')
            link_selector = 'div.item-with-contact h3 > a'
            l_links = page.select(link_selector)
            if l_links:
                l_item_urls.extend([link.get('href') for link in l_links if link.get('href','')])
            break
        except Exception as e:
            log(e)
            log(f'get_item_urls: новая попытка ({_+1})')

# walk through pages and collecting item urls
for n in range(i_cur_page_num, i_last_page_num + 1):
    log('страница:', n, 'из', i_last_page_num)
    s_page_url = f'{s_url}?{s_params}&p={n}'
    get_item_urls(s_page_url)

log('Всего', len(l_item_urls), 'ссылок')

# extraction of information in each item =========================================================
def save_data(data):
    log(f'сохранение данных')
    string = ''
    column_names = ['id', 'header', 'description', 'price', 'employer', 'employer_address', 'img_url', 'avito_url']
    for key in column_names:
        s = f'{data.get(key, "").strip()}'
        if ';' in s:
            s = s.replace(';', ' ')
        if '\n' in s:
            s = s.replace('\n', '  ')
        if key != column_names[-1]:
            string += (s + ';')
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            r_text = file.read()
            with open(filename, 'a', encoding='utf-8') as file:
                if string not in r_text:
                    file.write(string + '\n')
    except Exception as e:
        log(e)
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(string + '\n')

# selectors of elements to scrape from each item
field_selectors = {
    'id': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-search-info-redesign > span',
    'header': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-title-info.js-item-view-title-info > div > div.title-info-main > h1 > span',
    'description': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-main.js-item-view-main > div:nth-child(3) > div > div > p',
    'price': '#price-value > span > span.js-item-price',
    'employer': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-seller-info.js-item-view-seller-info > div > div.seller-info-prop.js-seller-info-prop_seller-name.seller-info-prop_layout-two-col > div.seller-info-col > div:nth-child(1) > div > a',
    'employer_url': 'div.item-view-content div.seller-info-name > a',
    'employer_address': 'body > div.item-view-page-layout > div.l-content.clearfix > div > div > span > div > div.styles-side-2pjZi > div > div.styles-summary-info-1YdLU > div:nth-child(3)',
    'img_url': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-main.js-item-view-main > div.item-view-block.item-view-layout.item-view-layout_type-two-col > div.item-view-gallery.item-view-gallery_type-one-img > div.gallery.gallery_state-clicked.js-gallery.gallery_type-small > div > div > div > div > img'
}

item_info = {}

def get_employer_address(url):
    if url:
        url = domain + url
        log(url)
        for _ in range (100):
            try:
                # going to employer page
                bot.go_to(url)
                response = Namespace(text=bot.get_page_source())
                assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Ваш IP заблакоирован. Смените прокси сервер.'
                employer_page = bs(response.text, 'html.parser')
                # scraping fields
                selection = employer_page.select(field_selectors['employer_address'])
                if selection:
                    item_info['employer_address'] = selection[0].text
                else:
                    item_info['employer_address'] = ''
                return
            except Exception as e:
                log('Exception:', e)
                log(f'get_employer_address: новая попытка ({_ + 1})')

def get_item_data(item_url):
    for _ in range(100):
        try:
            # going to item page
            bot.go_to(item_url)
            response = Namespace(text=bot.get_page_source())
            assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Ваш IP заблакоирован. Смените прокси сервер.'
            item_page = bs(response.text, 'html.parser')
            # scraping fields
            item_info['avito_url'] = item_url
            for key, selector in field_selectors.items():
                if key == 'employer_address':
                    get_employer_address(item_info.get('employer_url',''))
                    continue
                selection = item_page.select(selector)                
                if selection:
                    if key == 'img_url':
                        img = selection[0]
                        item_info['img_url'] = img.get('src','')
                    elif key == 'employer_url':
                        employer_link = selection[0]
                        item_info['employer_url'] = employer_link.get('href','')
                    else:
                        item_info[key] = selection[0].text
                else:
                    item_info[key] = ''
            save_data(item_info)
            break
        except Exception as e:
            log('Exception:', e)
            log(f'get_item_data: новая попытка ({_+1})')

for item_url in l_item_urls:
    item_url = domain + item_url
    log(item_url)
    get_item_data(item_url)
bot.quit()
log('Готово')