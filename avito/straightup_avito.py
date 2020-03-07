from bs4 import BeautifulSoup as bs
from re import search, compile
from webbot import Browser
from argparse import Namespace
import datetime as dt
from time import sleep
from requests import get

date = dt.datetime.now()

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
        print('пароль неверный')
        sleep(5)
        exit()
    else:
        with open('password.txt', 'w', encoding='utf-8') as file:
            file.write('123454321')
        print('Добро пожаловать!')

def log(*args, **kwargs):
    print('-'*50)
    print(*args, **kwargs)
    print('-'*50)

#s_user_url = 'https://www.avito.ru/krasnodar/vakansii/administrativnaya_rabota-ASgBAgICAUSOC6aeAQ'
s_user_url = input('Введите url страницы. Url должен начинаться c "https://". Пример: https://www.avito.ru/krasnodar/vakansii/administrativnaya_rabota-ASgBAgICAUSOC6aeAQ\n: ')
# domen extraction
domen = ''
if s_user_url and search('(?:https?:\/\/)?[A-z.-]+\.\w+\/', s_user_url):
    domen = search('(?:https?:\/\/)?[A-z.-]+\.\w+\/', s_user_url)[0]
# params extraction
if '?' in s_user_url and len(s_user_url.split('?')) > 1:
    s_url, s_params = s_user_url.split('?')
else:
    s_url, s_params = s_user_url, ''
# setting up proper filename based on query for extracted info 
banned_filename_symbols = '\/:*?<>|"'
filename = f'{s_url}?{s_params}'
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
        assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Blocked. Change proxy.'
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
        log(f'initial connection: new try({_+1})')

# list for urls extrcted on each page of a paginated topic
l_item_urls = []

def get_item_urls(s_page_url):
    for _ in range(100):
        try:
            bot.go_to(s_page_url)
            # namespace is a monkey patch due to lack of time
            page_response = Namespace(text=bot.get_page_source())
            assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Blocked. Change proxy.'
            page = bs(page_response.text, 'html.parser')
            link_selector = 'div.item-with-contact h3 > a'
            l_links = page.select(link_selector)
            if l_links:
                l_item_urls.extend([link.get('href') for link in l_links if link.get('href','')])
            break
        except Exception as e:
            log(e)
            log(f'get_item_urls: new try({_+1})')

# walk through pages and collecting item urls
for n in range(i_cur_page_num, i_last_page_num + 1):
    log('page:', n, 'of', i_last_page_num)
    s_page_url = f'{s_url}?{s_params}&p={n}'
    get_item_urls(s_page_url)

log('collected', len(l_item_urls), 'urls')

# extraction of information in each item =========================================================
def save_data(data):
    log(f'saving data')
    string = str(data)
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            r_text = file.read()
            with open(filename, 'a', encoding='utf-8') as file:
                if string not in r_text:
                    file.write(string+'\n')
    except Exception as e:
        log(e)
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(string)

# selectors of elements to scrape from each item
field_selectors = {
    'id': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-search-info-redesign > span',
    'header': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-title-info.js-item-view-title-info > div > div.title-info-main > h1 > span',
    'description': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-main.js-item-view-main > div:nth-child(3) > div > div > p',
    'price': '#price-value > span > span.js-item-price',
    'employer': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-seller-info.js-item-view-seller-info > div > div.seller-info-prop.js-seller-info-prop_seller-name.seller-info-prop_layout-two-col > div.seller-info-col > div:nth-child(1) > div > a',
    'img': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-main.js-item-view-main > div.item-view-block.item-view-layout.item-view-layout_type-two-col > div.item-view-gallery.item-view-gallery_type-one-img > div.gallery.gallery_state-clicked.js-gallery.gallery_type-small > div > div > div > div > img'
}

def get_item_data(item_url):
    for _ in range(100):
        try:
            bot.go_to(item_url)
            item_response = Namespace(text=bot.get_page_source())
            assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Blocked. Change proxy.'
            item_page = bs(item_response.text, 'html.parser')
            item_info = {}
            item_info['url'] = item_url
            for key, selector in field_selectors.items():
                selection = item_page.select(selector)
                if selection:
                    item_info[key] = selection[0].text
            save_data(item_info)
            break
        except Exception as e:
            log('Exception:', e)
            log(f'get_item_data: new try({_+1})')

for item_url in l_item_urls:
    item_url = domen + item_url
    log(item_url)
    get_item_data(item_url)
bot.quit()
log('done')