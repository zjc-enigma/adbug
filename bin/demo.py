# -*- coding: utf-8 -*-
import sys
import os
from pyquery import PyQuery as pq
import urllib
import urllib2
import requests
import json
from urlparse import urlparse, parse_qs
import browsercookie

def save_to_file(resource_data, save_path):
    if not os.path.exists(os.path.dirname(save_path)):
        try:
            os.makedirs(os.path.dirname(save_path))

        except OSError as exc: # Guard against race condition
            print "save exception:", str(exc)
            raise
            #if exc.errno != errno.EEXIST:
            #    raise

    with open(save_path, "wb") as f:
        f.write(resource_data)


def download_resource(url):
    cj = browsercookie.chrome()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    ret = opener.open(url)
    resource_data = ret.read()
    return resource_data



url = 'http://www.adbug.cn/'
search_url = 'http://www.adbug.cn/Search/all'
session = requests.session()

## set key word
if len(sys.argv) == 2:
    keyword = sys.argv[1]
else:
    keyword = '采购'
params = {'wd': keyword}
res = session.get(search_url, params=params)

doc = pq(res.content)
all_items = doc('div.ads')('div.item')
item = all_items.eq(0)
ad_url = item('div.thumb')('a.img').attr('href')
thumb_url = item('div.thumb')('img').attr('src')
ad_text = item('div.meta').text()

#detail_data = json.loads(doc('div.content-left')('script').text()[11:-8])
detail_data_list = json.loads(doc('div.content-left')('script').text().split('\n')[0][11:-1])
# with open("detail", 'w') as f:
#     f.write(detail_data)
# detail_data = detail_data_list[0]

crawl_res = []

for detail_data in detail_data_list:
    res = {}

    res['url'] = detail_data['d_l']
    res['ad_img_url'] = detail_data['r_url']
    res['ad_weight'] = detail_data['w']
    res['ad_height'] = detail_data['h']
    res['ad_id'] = detail_data['id']
    res['ad_meta'] = detail_data['meta']
    res['ad_type'] = detail_data['type']

    save_path = '..' + urlparse(res['ad_img_url']).path
    resource_data = download_resource(res['ad_img_url'])
    save_to_file(resource_data, save_path)
    print "saved img to %s" % save_path

    detail_doc = pq(res['ad_meta'])
    detail_item_list = detail_doc('li')
    detail_res = {}
    for item in detail_item_list.items():
        label = item('label').text().strip().replace(':', '')
        if label:
            value = item('span').text()
            print label, value
            detail_res[label] = value

    res['detail'] = detail_res
    crawl_res.append(res)
    print "============================================================"













