# -*- coding: utf-8 -*-
# python 3.8.1
from typing import List
from utils import log, url_to_filename, load_data
from core import load_proxies, new_global, get_global, get_user_input, \
    check_app_status, extract_params, get_current_page, \
    get_last_page, collect_item_urls, fetch_data
from settings import PROXY, USE_BOT, HEADLESS, WEBDRIVERPATH


if USE_BOT:
    from webbot import Browser


def main(user_url: str) -> None:
    url, params = extract_params(user_url)
    cur_page_num = get_current_page(params)
    last_page_num = get_last_page(user_url, cur_page_num)
    params = params.replace(f'p={cur_page_num}', '')
    # new_url is url without p=123 parmeter
    new_url = f'{url}?{params}'

    filename = url_to_filename(new_url, substitute='-', ext='.csv', _os='win')
    DATA_FILENAME = 'data_' + filename
    URLS_FILENAME = 'urls_' + filename
    new_global('DATA_FILENAME', DATA_FILENAME)
    new_global('URLS_FILENAME', URLS_FILENAME)

    bot = None
    if USE_BOT:
        # start browser
        bot = Browser(headless=HEADLESS, proxy=get_global('PROXY'), driverpath=WEBDRIVERPATH)
    new_global('BOT', bot)

    item_urls = []
    if urls_data := load_data(URLS_FILENAME):
        item_urls: List[str] = urls_data.split('\n')
    else:
        page_range = range(cur_page_num, last_page_num + 1)
        item_urls = collect_item_urls(new_url, page_range, item_urls)

    # extraction of data in each item =========================================================

    fetch_data(item_urls)

    if get_global('PROXY_ERROR'):
        raise Exception('Proxy error')

    if bot:
        bot.close()
    log('Готово')


if __name__ == '__main__':
    # erase_data('errors.txt')
    user_url, DOMAIN = get_user_input()

    new_global('DOMAIN', DOMAIN)

    check_app_status(app_key=1)

    new_global('PROXIES', load_proxies())
    new_global('PROXY', PROXY)

    main(user_url)