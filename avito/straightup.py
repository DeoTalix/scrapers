from requests import get
from bs4 import BeautifulSoup as bs
from re import search, compile
#import time
#from threading import Thread

field_selectors = {
    'id': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-search-info-redesign > span',
    'header': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-title-info.js-item-view-title-info > div > div.title-info-main > h1 > span',
    'description': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-main.js-item-view-main > div:nth-child(3) > div > div > p',
    'price': '#price-value > span > span.js-item-price',
    'employer': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-seller-info.js-item-view-seller-info > div > div.seller-info-prop.js-seller-info-prop_seller-name.seller-info-prop_layout-two-col > div.seller-info-col > div:nth-child(1) > div > a',
    'img': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-main.js-item-view-main > div.item-view-block.item-view-layout.item-view-layout_type-two-col > div.item-view-gallery.item-view-gallery_type-one-img > div.gallery.gallery_state-clicked.js-gallery.gallery_type-small > div > div > div > div > img'
}


domen = 'https://www.avito.ru/'

s_url = 'https://www.avito.ru/krasnodar/vakansii/administrativnaya_rabota-ASgBAgICAUSOC6aeAQ'
s_params=''
i_cur_page_num = 1
i_last_page_num = i_cur_page_num

if '?' in s_url:
    l_url = s_url.split('?')
    if len(l_url) > 1:
        s_url, s_params = l_url
        if 'p=' in s_params:
            s_cur_page = search('p=\d+', s_params)[0]
            s_cur_page_num = s_cur_page.split('=')[1]
            if s_cur_page_num and s_cur_page_num.isdigit():
                s_params = s_params.replace(s_cur_page, '')
                i_cur_page_num = int(s_cur_page_num)

response = get(s_url)
page = bs(response.text, 'html.parser')

pager = page.find_all(class_=compile('pagination-root'))
is_paginated = bool(pager)

if is_paginated:
    pager_element = pager[0]
    last_page = pager_element.select('span:nth-last-child(2)')[0]
    if last_page and last_page.text.isdigit():
        i_last_page_num = int(last_page.text)

css_selector = 'div.item-with-contact h3 > a'

l_item_urls = []
threads = []

def get_item_urls(s_sub_url): 
    sub_response = get(s_sub_url)
    sub_page = bs(sub_response.text, 'html.parser')
    l_links = sub_page.select(css_selector)
    if l_links:
        l_item_urls.extend([link.get('href') for link in l_links if link.get('href','')])

for n in range(i_cur_page_num, i_last_page_num + 1):
    print(n)
    s_sub_url = f'{s_url}?{s_params}&p={n}'
    get_item_urls(s_sub_url)
    #t = Thread(target=get_item_urls, args=[s_sub_url])
    #t.start()
    #threads.append(t)

#for t in threads:
#    t.join()

print(len(l_item_urls))

def get_item_info(item_url):
    item_response = get(item_url)
    item_page = bs(item_response.text, 'html.parser')
    
    item_info = {}
    item_info['url'] = item_url
    for key, selector in field_selectors.items():
        selection = item_page.select(selector)
        if selection:
            item_info[key] = selection[0].text
    doc.append(item_info)

doc = []
#threads = []

for item_url in l_item_urls:
    item_url = domen + item_url
    print(item_url)
    #t = Thread(target=get_item_info, args=[item_url])
    #t.start()
    #threads.append(t)
    get_item_info(item_url)

#for t in threads:
#    t.join()

with open('test.txt', 'w', encoding='utf-8') as file:
    file.write(str(doc))