import sys
import os
from pyquery import PyQuery as pq
import urllib
import requests
import json
from collections import Counter
import pdb

def save_to_file(resource_data, save_path):
    if not os.path.exists(os.path.dirname(save_path)):
        try:
            os.makedirs(os.path.dirname(save_path))

        except OSError as exc: # Guard against race condition
            print("save exception:", str(exc))
            raise

    with open(save_path, "wb") as f:
        f.write(resource_data)


def download_resource(url):
    # cj = browsercookie.chrome()
    # opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    # ret = opener.open(url)
    # resource_data = ret.read()
    response = requests.get(url)
    return response.content


def find_next_page_url(doc):
    next_page_url = ''

    NEXT_PAGE_STRING = u'\xe4\xb8\x8b\xe4\xb8\x80\xe9\xa1\xb5'
    paging_list = doc('div.paging')('a')
    for page in paging_list.items():
        if page.text() == NEXT_PAGE_STRING:
            next_page_url = 'http://www.adbug.cn' + page.attr('href')
            print("found next page url: %s" % next_page_url)

    return next_page_url


def is_duplicated(detail_res, dup_dict):
    check_list = [u'广告尺寸', u'投放平台', u'广告主', u'营销推广']
    value_list = []
    for key in check_list:
        value_list.append(detail_res[key])

    check_string = "_".join(value_list)
    if check_string in dup_dict:
        return True

    else:
        dup_dict[check_string] = 1
        return False



if __name__ == '__main__':

    url = 'http://www.adbug.cn/'
    #search_url = 'http://www.adbug.cn/Search/all'
    search_url = 'http://www.adbug.cn/home/search/ads'
    session = requests.session()
    ## set key word
    # if len(sys.argv) == 2:
    #     keyword = sys.argv[1]
    # else:
    #     print("usage : python demo.py [keywords]")
    #     sys.exit(-1)
    keyword = "尚德"
    MAX_PAGE_NUM = 10
    #http://www.adbug.cn/home/search/ads?wd=%E5%B0%9A%E5%BE%B7

    params = {'wd': keyword, 'pn': 1}
    #next_url = None
    #res = session.get(search_url, params=params)
    duplicated_dict = {}
    ad_text_list = []

    with open('../data/' + keyword + '.json', 'w') as output:
        while True:
            res = session.get(search_url, params=params)
            doc = pq(res.content)
            all_items = doc('div.item')
            for item in all_items.items():
                #ad_url = item('div.thumb')('a').attr('href')
                thumb_url = item('img').attr('src')
                # ad_text = item('div.meta').text()
                meta = json.loads(item('div.item_meta').text())
                title = meta['title']
                name = meta['a']['name']
                n = meta['n']
                ad_text_list.append(title)
                ad_text_list.append(name)
                ad_text_list.append(n)

            params['pn'] += 1
            if params['pn'] > MAX_PAGE_NUM:
                break

        text_freq_list = [ ad_text_list.count(text) for text in ad_text_list ]
        text_count_dict = dict(zip(ad_text_list, text_freq_list))
        t = [(text_count_dict[k], k) for k in text_count_dict]
        t.sort()
        t.reverse()

        for item in t:
            print(item[1], item[0])

                #ad_url = item('div.thumb')('a.img').attr('href')
                #thumb_url = item('div.thumb')('img').attr('src')
                #ad_text = item('div.meta').text()

                # detail_data_list = json.loads(doc('div.content-left')('script').text().split('\n')[0][11:-1])
                # crawl_res = []

            # except Exception as e:
            #     print("error in get doc, exiting", e)
            #     break

            # for detail_data in detail_data_list:
            #     try:
            #         res = {}

            #         res['url'] = detail_data['d_l']
            #         res['ad_img_url'] = detail_data['r_url']
            #         res['ad_weight'] = detail_data['w']
            #         res['ad_height'] = detail_data['h']
            #         res['ad_id'] = detail_data['id']

            #         ad_meta = detail_data['meta']
            #         res['ad_type'] = detail_data['type']
            #         save_path = '..' + urllib.parse.urlparse(res['ad_img_url']).path

            #         resource_data = download_resource(res['ad_img_url'])
            #         save_to_file(resource_data, save_path)
            #         print("saved img to %s" % save_path)

            #         res['save_path'] = save_path
            #         detail_doc = pq(ad_meta)
            #         detail_item_list = detail_doc('li')
            #         detail_res = {}
            #         for item in detail_item_list.items():
            #             label = item('label').text().strip().replace(':', '')
            #             if label:
            #                 value = item('span').text()
            #                 print(label, value)
            #                 detail_res[label] = value
            #         if is_duplicated(detail_res, duplicated_dict):
            #             print("found duplicated skiped")
            #             continue
            #         res['detail'] = detail_res
            #         crawl_res.append(res)
            #         print("============================================================")
            #         output.write(json.dumps(res, ensure_ascii=False, sort_keys=True).encode('utf8') + '\n')
            #     except Exception as e:
            #         print("error in fetching, skiped", str(e))
            #         continue
            # next_url = find_next_page_url(doc)
            # if not next_url:
            #     print("there is no next page to crawl, exiting")
            #     break

