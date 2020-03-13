from typing import Dict, List


VERBOSE_LOG = False

# proxy must be formatted: 182.52.238.111:30098
PROXY = ''

# global sleep time during retry
SLEEP_TIME = 1.0

# global page load timeout
TIMEOUT = 30

# webbot settings
USE_BOT = True

HEADLESS = False

WEBDRIVERPATH = '.'

# column names to save in csv
COLUMN_TITLES = ['id', 'header', 'description', 'price',
                            'employer', 'employer_address', 'img_url', 'avito_url']

# selectors of elements to scrape from each item (copied straight from chrome dev tools :D)
SELECTORS = {
    'id': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-search-info-redesign > span',

    'header': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-title-info.js-item-view-title-info > div > div.title-info-main > h1 > span',
    'description': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-left > div.item-view-main.js-item-view-main > div:nth-child(3) > div > div > p',

    'price': '#price-value > span > span.js-item-price',

    'employer': 'body > div.item-view-page-layout.item-view-page-layout_content.item-view-page-layout_responsive > div.l-content.clearfix > div.item-view.js-item-view > div.item-view-content > div.item-view-content-right > div.item-view-info.js-item-view-info.js-sticky-fallback > div > div.item-view-seller-info.js-item-view-seller-info > div > div.seller-info-prop.js-seller-info-prop_seller-name.seller-info-prop_layout-two-col > div.seller-info-col > div:nth-child(1) > div > a',

    'employer_url': 'div.item-view-content div.seller-info-name > a',

    'employer_address': 'body > div.item-view-page-layout > div.l-content.clearfix > div > div > span > div > div.styles-side-2pjZi > div > div.styles-summary-info-1YdLU > div:nth-child(3)',

    'img_url': 'div.gallery-img-frame > img'
}
