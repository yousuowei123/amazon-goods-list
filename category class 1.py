# -*- coding:utf-8 -*-
# -*- author:cto_b -*-

import requests
from bs4 import BeautifulSoup
import re
from random import choice
import pymysql

sequence = 0
f = open("newamason2.txt", 'a+', encoding='utf-8')
headers_pool = [
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
    'Mozilla/5.0(Macintosh;U;IntelMacOSX10_6_8;en-us)AppleWebKit/534.50(KHTML,likeGecko)Version/5.1Safari/534.50',
    'Mozilla/5.0(Windows;U;WindowsNT6.1;en-us)AppleWebKit/534.50(KHTML,likeGecko)Version/5.1Safari/534.50',
    'Mozilla/5.0(compatible;MSIE9.0;WindowsNT6.1;Trident/5.0',
    'Mozilla/5.0(Macintosh;IntelMacOSX10.6;rv:2.0.1)Gecko/20100101Firefox/4.0.1',
    'Opera/9.80(Macintosh;IntelMacOSX10.6.8;U;en)Presto/2.8.131Version/11.11',
    'Mozilla/5.0(iPhone;U;CPUiPhoneOS4_3_3likeMacOSX;en-us)AppleWebKit/533.17.9(KHTML,likeGecko)Version/5.0.2Mobile/8J2Safari/6533.18.5',
    'Mozilla/5.0(Linux;U;Android2.3.7;en-us;NexusOneBuild/FRF91)AppleWebKit/533.1(KHTML,likeGecko)Version/4.0MobileSafari/533.1'
]


def get_page_source(url, num_retries=2):
    '''
    get_page_source(url, num_retries) --> None or str
    :param url: str
    :param num_retries: int
    :return: None or r.text
    '''
    print("\033[32;1mdownload:{}\033[0m".format(url))
    try:
        # params = {'s': 'apparel', 'ie': 'UTF8', 'qid': 1518485586,
        #           'sr': '1 - 10', 'nodeID': 1044990, 'psd': 1
        # }
        headers = {'user-agent': choice(headers_pool)}
        proxies = {
            'http': 'http://139.129.166.68:3128',
            'https:': 'https://114.113.126.82:80'
        }
        r = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        r.raise_for_status()
        r.encoding = "utf-8"

    except Exception as e:
        print(e)
        # if num_retries > 0:
        #     if 500 < r.status_code < 600:
        #         return get_page_source(url, num_retries-1)
        #     if 400 <= r.status_code <= 500:
        #         print("ip被封")
        #         return None

        return None
    else:
        return r.text


def parse_one_page(html):
    '''
    parse_one_page(html) --> dict
    :param html: str
    :return: None or dict
    '''
    if html:
        soup = BeautifulSoup(html, "lxml")
        item_list = soup.find_all(attrs={'id': re.compile("result_\d+")})

        global sequence
        for li in item_list:
            try:
                li = str(li)
                asin = re.findall('data-asin="(.*?)"', li, re.S)[0]

                url = re.findall('href="(.*?)"', li, re.S)[0]

                BRAND1 = re.findall('<span class="a-color-secondary s-overflow-ellipsis s-size-mild">(.*?)</span>', li, re.S)
                BRAND2 = re.findall('<a class="a-link-normal".*?<img alt=.*?title="(.*?)"', li, re.S)
                if BRAND1:
                    brand = BRAND1[0]
                else:
                    brand = BRAND2[0]

                image1 = re.findall('srcset="(.*?) 1x', li, re.S)
                image2 = re.findall('data-search-image-source="(.*?)"', li, re.S)
                if image1 and image2:
                    image2 = image2[0]
                    image = [image1[0], image2]
                elif image1:
                    image = [image1[0]]
                else:
                    image = []

                title = re.findall('data-max-rows="0">(.*?)</h2>', li, re.S)
                if title:
                    title = title[0]
                else:
                    title = ''

                currency_price = re.findall('<sup class="sx-price-currency">(.*?)</sup>', li, re.S)[0]
                whole_price = re.findall('<span class="sx-price-whole">(.*?)</span>', li, re.S)[0]
                fractional_price = re.findall('<sup class="sx-price-fractional">(.*?)</sup>', li, re.S)[0]
                price_range = currency_price + whole_price + '.' + fractional_price

                evaluation_number = re.findall('customerReviews">(.*?)</a></div>', li, re.S)
                if evaluation_number:
                    evaluation_number = evaluation_number[0]
                else:
                    evaluation_number = ''

                grade = re.findall('<span class="a-icon-alt">(.*?)</span></i>', li, re.S)
                if grade:
                    grade = grade[-1]
                else:
                    grade = ''
                service_mode = re.findall('aria-label="(.*?)"', li, re.S)
                if service_mode:
                    service_mode = service_mode[0]
                else:
                    service_mode = ''

            except Exception as e:
                print(e)
                continue
            else:
                yield {
                    'sequence': sequence, 'asin': asin, 'url': url, 'brand': brand, 'image': image,
                    'title': title, 'price_range': price_range, 'evaluation_number': evaluation_number,
                    'grade': grade, 'service_mode': service_mode
                }
            sequence += 1


def save_dict(doc):
    f.write(str(doc) + '\n')


def main(max_error=3):
    page = 1
    num_errors = 0
    while True:
        url = "https://www.amazon.com/s/ref=lp_1044990_pg_2?rh=n%3A7141123011%2Cn%3A7147440011%2Cn%3A1040660%2Cn%3A9522931011%2Cn%3A14333511%2Cn%3A1044960%2Cn%3A1044990&page={}".format(page)
        try:
            html = get_page_source(url)
            results = parse_one_page(html)
            if html is None:
                num_errors += 1
                if num_errors == max_error:
                    print("连续出现错误, 网页出现空值")
                    break
            else:
                num_errors = 0

        except Exception as e:
            print(e)
            break
        else:
            for item in results:
                save_dict(item)
                print('\033[33;1m保存成功\033[0m', item)
        page += 1


if __name__ == "__main__":
    main()
    f.close()