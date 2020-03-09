from requests import get
from bs4 import BeautifulSoup as bs
from re import search, compile
import time
from threading import Thread

parallel = False

def get_proxies(url, ip_selector, port_selector):
    print(f'getting proxies from {url}')
    response = get(url)
    page = bs(response.text, 'html.parser')
    ip_adresses = [element.text for element in page.select(ip_selector)]
    ports = [element.text for element in page.select(port_selector)]
    proxies = list(zip(ip_adresses, ports))
    return proxies

def load_proxies():
    with open('proxies.txt', 'r', encoding='utf-8') as file:
        text = file.read()
        proxies = [proxy.split(':') for proxy in text.split(',') if proxy]
        return proxies
    
proxy_url ='https://www.sslproxies.org/'
ip_selector = '#proxylisttable > tbody > tr > td:nth-child(1)'
port_selector = '#proxylisttable > tbody > tr > td:nth-child(2)'

#proxy_url ='https://hidemy.name/ru/proxy-list/?__cf_chl_jschl_tk__=ce9d4c2c337972892b237ae753b032597ed282a4-1583536622-0-AaRwO9gUMpdJamX1OOlOTeyF7v4h3IoCDgy3pH67C7YcwZKSOiT00ADjj4mJXJIipjVWfPaIsAEluruNu9Hs53G5kNA8CMJL31osAB022V_dCS7eMPOjhN-1SCJxsxqkLSt9J_myROYZQP7BS3lJHx8cJXHmVnjxh8prAI0U2TMJJtnuY-jFdl-zDFCngPPJoj005d9pdzk2ymjdEaAVnh-N8Q9MpzQZwMTy3CaSKOVGKB8ppmcoNo-pdo4L_0hcwZRtFVIlqQriqNwcQsy3rKe02nzzS6I-tSAt7eOKl9yj'
#ip_selector = 'div.tableblock > table > tbody > tr > td:nth-child(1)'
#port_selector = 'div.tableblock > table > tbody > tr > td:nth-child(2)'

l_proxies = load_proxies()#get_proxies(proxy_url, ip_selector, port_selector)
#print(l_proxies)

def load_bad_proxies():
    with open('bad_proxies.txt', 'r', encoding='utf-8') as file:
        return file.read()

s_bad_proxies = load_bad_proxies()

def add_bad_proxy(proxy):
    assert type(proxy) == str, 'proxy should be string'
    global s_bad_proxies
    with open('bad_proxies.txt', 'a', encoding='utf-8') as file:
        if proxy not in load_bad_proxies():
            return file.write(proxy+'\n')
    s_bad_proxies = load_bad_proxies()

def form_proxy(proxy):
    return {'https': 'http://' + (':'.join(proxy))}

def find_new_proxy(url):
    print('finding new proxy')
    response = None
    for n in range(len(l_proxies)):
        if str(l_proxies[n]) not in s_bad_proxies:
            try:
                response = get(url, timeout=5, proxies=form_proxy(l_proxies[n]))
                if response.status_code == 200:
                    assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Blocked. Change proxy.'
                    print(f'found {l_proxies[n]}')
                    return l_proxies[n]
                else:
                    raise Exception('Unexpected status code:', response.status_code)
            except Exception as e:
                print('Exception:', e)
                add_bad_proxy(str(l_proxies[n]))
        else:
            print('Bad proxy')

# if __name__ == '__main__':

domen = 'https://www.avito.ru/'

current_proxy = find_new_proxy(domen)

s_url = 'https://www.avito.ru/krasnodar?q=%D0%B0%D1%80%D0%B5%D0%BD%D0%B4%D0%B0+%D0%B0%D0%B2%D1%82%D0%BE'
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

t = time.perf_counter()
for _ in range(100):
    try:
        response = get(f'{s_url}?{s_params}', proxies=form_proxy(current_proxy))
        if response.status_code == 200:
            assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Blocked. Change proxy.'
        if response and response.text:
            page = bs(response.text, 'html.parser')

            pager_selector = compile('pagination-root') #doesn't work with page.select('')
            last_page_selector = 'span:nth-last-child(2)'

            pager = page.find_all(class_=pager_selector)
            is_paginated = bool(pager)

            if is_paginated:
                pager_element = pager[0]
                last_page = pager_element.select(last_page_selector)[0]
                if last_page and last_page.text.isdigit():
                    i_last_page_num = int(last_page.text)
        break
    except Exception as e:
        print('Exception:', e)
        add_bad_proxy(str(current_proxy))
        current_proxy = find_new_proxy(s_url)

link_selector = 'div.item-with-contact h3 > a'

l_item_urls = []
threads = []

def get_item_urls(s_sub_url):
    global current_proxy
    for _ in range(100):
        try:
            sub_response = get(s_sub_url, proxies=form_proxy(current_proxy))
            if sub_response.status_code == 200:
                assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Blocked. Change proxy.'
            sub_page = bs(sub_response.text, 'html.parser')
            l_links = sub_page.select(link_selector)
            if l_links:
                l_item_urls.extend([link.get('href') for link in l_links if link.get('href','')])
            break
        except Exception as e:
            print(e)
            add_bad_proxy(str(current_proxy))
            current_proxy = find_new_proxy(s_sub_url)


for n in range(i_cur_page_num, i_last_page_num + 1):
    print(n)
    s_sub_url = f'{s_url}?{s_params}&p={n}'
    if parallel:
        t = Thread(target=get_item_urls, args=[s_sub_url])
        t.start()
        threads.append(t)
    else:
        get_item_urls(s_sub_url)
if parallel:
    for t in threads: t.join()

print(len(l_item_urls))

#==================================================================================================

field_selectors = {
    'id': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-search-info-redesign > span',
    'header': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-title-info.js-item-view-title-info > div > div.title-info-main > h1 > span',
    'description': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-main.js-item-view-main > div:nth-child(3) > div > div > p',
    'price': '#price-value > span > span.js-item-price',
    'employer': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-seller-info.js-item-view-seller-info > div > div.seller-info-prop.js-seller-info-prop_seller-name.seller-info-prop_layout-two-col > div.seller-info-col > div:nth-child(1) > div > a',
    'img': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-main.js-item-view-main > div.item-view-block.item-view-layout.item-view-layout_type-two-col > div.item-view-gallery.item-view-gallery_type-one-img > div.gallery.gallery_state-clicked.js-gallery.gallery_type-small > div > div > div > div > img'
}

doc = []

def get_item_info(item_url):
    global current_proxy
    for _ in range(100):
        try:
            item_response = get(item_url, proxies=form_proxy(str(current_proxy)))
            if item_response.status_code == 200:
                assert 'Мы были вынуждены временно заблокировать доступ к сайту' not in response.text, 'Blocked. Change proxy.'
            item_page = bs(item_response.text, 'html.parser')
            item_info = {}
            item_info['url'] = item_url
            for key, selector in field_selectors.items():
                selection = item_page.select(selector)
                if selection:
                    item_info[key] = selection[0].text
            doc.append(item_info)
            break
        except Exception as e:
            print('Exception:', e)
            current_proxy = find_new_proxy(item_url)

threads = []

for item_url in l_item_urls:
    item_url = domen + item_url
    print(item_url)
    if parallel:
        t = Thread(target=get_item_info, args=[item_url])
        t.start()
        threads.append(t)
    else:
        get_item_info(item_url)
if parallel:
    for t in threads: t.join()

banned_filename_symbols = '\/:*?<>|"'
filename = f'{s_url}?{s_params}'
for symbol in banned_filename_symbols:
    filename = filename.replace(symbol, '-')
print(filename)

with open(filename, 'w', encoding='utf-8') as file:
    file.write(str(doc))