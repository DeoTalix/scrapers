# -*- coding: utf-8 -*-
# python 3.8.1
from utils import log, url_to_filename, load_data, save_data, save_data_to_csv
from core import get_global, set_global, IP_ERROR, get_user_input, check_connection, check_app_status, extract_params, \
    get_current_page, get_last_page, walk_pages_and_do, get_item_urls, get_item_data
from settings import TIMEOUT, USE_BOT, WEBDRIVERPATH, COLUMN_TITLES, SELECTORS
from sys import exc_info

if USE_BOT: from webbot import Browser

def main(proxy, s_user_url, domain):
    s_url, s_params = extract_params(s_user_url)
    i_cur_page_num = get_current_page(s_params)
    i_last_page_num = get_last_page(s_user_url, i_cur_page_num, bot=None)
    s_params = s_params.replace(f'p={i_cur_page_num}', '')
    s_url = f'{s_url}?{s_params}'
    filename = url_to_filename(s_url, substitute='-', ext='.csv')
    data_file = 'data_' + filename
    urls_file = 'urls_' + filename

    bot = None
    if USE_BOT:
        # start browser
        bot = Browser(headless=True, proxy=proxy, driverpath=WEBDRIVERPATH)

    # getting urls extracted on each page of a paginated topic
    page_range = range(i_cur_page_num, i_last_page_num + 1)
    if load_data(urls_file):
        l_item_urls = load_data(urls_file).split('\n')
    else:
        l_item_urls = []
        for l_urls in walk_pages_and_do(s_url, page_range, func=get_item_urls, kwargs={'bot': bot}, bot=bot):
            if get_global('IP_ERROR'):
                break
            save_data(urls_file, '\n'.join(l_urls))
            l_item_urls.extend(l_urls)
            if get_global('IP_ERROR'): 
                break

    assert len(l_item_urls), f'{len(l_item_urls)} ссылок'
    log('Всего', len(l_item_urls), 'ссылок')

    # extraction of information in each item =========================================================    

    csv_data = load_data(data_file)

    # walking through each avito item
    for i, item_url in enumerate(l_item_urls):
        if get_global('IP_ERROR'):
            break
        item_data = get_item_data(i, domain, item_url, SELECTORS, csv_data=csv_data, bot=bot)
        if item_data:
            assert any([item_data[key] for key in item_data if key != 'avito_url'])
            save_data_to_csv(COLUMN_TITLES, item_data, data_file)

    if get_global('IP_ERROR'):
        raise Exception('IP error')

    if bot: bot.quit()
    log('Готово')

if __name__ == '__main__':
    # erase_data('errors.txt')
    s_user_url, domain = get_user_input()

    check_connection(s_user_url, timeout_multiplier=3)
    check_app_status(app_key=1)

    # proxies must be formatted: 182.52.238.111:30098,103.105.77.22:8181,
    proxies = load_data('proxies.txt').split(',')
    bad_proxies = load_data('bad_proxies.txt')

    # on the first iteration app will try to scrape using your ip
    # on next iterations (if exception occures) it will use proxies
    # bad proxies will be updated and skipped next time
    for proxy in [''] + proxies:
        if proxy:
            if proxy in bad_proxies:
                continue
            print(f'using proxy {proxy}') 
        try:
            set_global('IP_ERROR', False)
            set_global('SLEEP_TIME', 5)
            if proxy:
                check_connection(s_user_url, proxy=proxy, timeout_multiplier=3)
            main(proxy, s_user_url, domain)
            break
        except Exception as e:
            log(exc_info())
            save_data('bad_proxies.txt', proxy, end=',')
