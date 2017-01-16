import sys
import os
from pyquery import PyQuery as pq
import urllib
import requests
import json
from collections import Counter
from time import sleep
import jieba
import re
import pandas as pd
import numpy as np
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


def crawl_by_keyword(keyword):

    MAX_PAGE_NUM = 10
    url = 'http://www.adbug.cn/'
    search_url = 'http://www.adbug.cn/home/search/ads'
    session = requests.session()
    ## set key word
    # if len(sys.argv) == 2:
    #     keyword = sys.argv[1]
    # else:
    #     print("usage : python demo.py [keywords]")
    #     sys.exit(-1)

    params = {'wd': keyword, 'pn': 1}
    #next_url = None
    #res = session.get(search_url, params=params)
    duplicated_dict = {}
    ad_text_list = []

    while True:
        res = session.get(search_url, params=params)
        doc = pq(res.content)
        all_items = doc('div.item')
        for item in all_items.items():
            try:
                #ad_url = item('div.thumb')('a').attr('href')
                thumb_url = item('img').attr('src')
                # ad_text = item('div.meta').text()
                meta = json.loads(item('div.item_meta').text())
                title = meta.get('title')
                name = None
                if 'a' in meta:
                    name = meta.get('a').get('name')
                n = meta.get('n')
                ad_text_list.append(title)
                ad_text_list.append(name)
                ad_text_list.append(n)
                print('crawled  title {} from {}'.format(title, meta.get('tg')))

            except Exception as e:
                print(e)
                continue

        params['pn'] += 1
        sleep(5)

        if params['pn'] > MAX_PAGE_NUM:
            break

    text_freq_list = [ ad_text_list.count(text) for text in ad_text_list ]
    text_count_dict = dict(zip(ad_text_list, text_freq_list))
    t = [(text_count_dict[k], k) for k in text_count_dict]
    return t


def analytics(text_list):
    
    text_len_list = []
    for text in text_list:
        text_len = len(text)
        text_len_list.append(text_len)

    count_list = [ text_len_list.count(text_len) for text_len in text_len_list]
    analytics = dict(zip(text_len_list, count_list))
    t = [(analytics[k], k) for k in analytics]
    t.sort()
    t.reverse()
    for i in t:
        print(i)


def tokenize_zh_line(zh_line, method='jieba'):
    """
    zh_line:
    Chinese string line

    method:
    tokenize method , default using jieba

    Returns:
    token Chinese word list
    """
    try:
        zh_line = zh_line.strip()
        zh_line = " ".join(re.findall(r'[\u4e00-\u9fff\w\_]+', zh_line))

        tokenized_list = jieba.cut(zh_line, cut_all=False)
        res = [ word for word in tokenized_list if word != ' ' ]
        return res

    except AttributeError as attr:
        print(zh_line)
        return []


def filter_and_ranking(res_list):

    MAX_TEXT_LEN = 28
    MIN_TEXT_LEN = 7
    big_word_list = ["如何","怎样","怎么","何以","知道","揭秘","爆料","劲爆","内幕","真相","隐情","惊","紧急","十万火急","吓一跳","围观","竟然","原来","不可思议","疯转","疯了","落伍","亏大了","甩几条街","不是","［","｛","[","{","？","！","?","!","盘点","合集","都在这里","大全","总览","赚大了","赠送","红包","惊呼","给力","快抢","疯抢","免费","便宜","包邮","折扣","降价","优惠","送礼","返现","好消息","大消息","今日消息","最新消息","新政出台","HOT","关注","热点","重磅消息","美女","美色","偷窥","私密","占便宜"]

    good_text = []
    normal_text = []

    for freq,text in res_list:
        if len(text) > MAX_TEXT_LEN or len(text) < MIN_TEXT_LEN:
            continue
        text_seg = tokenize_zh_line(text)

        if any(t in big_word_list for t in text_seg):
            good_text.append((text, freq))

        else:
            normal_text.append((text, freq))

    good_text.sort(key=lambda tup: tup[1])
    good_text.reverse()
    normal_text.sort(key=lambda tup: tup[1])
    normal_text.reverse()
    # remove duplicated
    total_list = good_text + normal_text
    text_dict = {}
    for item in total_list:
        text = item[0].strip()
        if text in text_dict:
            total_list.remove(item)
        else:
            text_dict[text] = 0

    return total_list


def rewrite_name(name):
    
    name = name.replace('（', " ")
    name = name.replace('）', " ")
    name = name.replace('(', " ")
    name = name.replace(')', " ")

    if name.endswith('有限公司'):
        return re.sub('有限公司$',"", name)

    if name.endswith('公司'):
        return re.sub('公司$',"", name)

    return name


def rewrite_category(category):
    if category.endswith('类'):
        return re.sub('类$', "", category)

    return category



def get_all_advertiser_name_with_category():
    import MySQLdb
    conn = MySQLdb.connect(host='192.168.144.237',
                       user='data',
                       passwd='PIN239!@#$%^&8',
                       charset='utf8')
    conn.select_db('category')
    sql = """select * from advertiser_industry"""
    d = pd.read_sql(sql=sql, con=conn)
    name_list = [ rewrite_name(name)
                  for name in list(np.unique(d['name']))]

    industry_list = [ rewrite_category(category)
                      for category in list(np.unique(d['industry_1'].append(d['industry_2'])))]

    return name_list


if __name__ == '__main__':

    #keyword_list = ["尚德", "自考", "职业培训", "教育", "学历教育", "成人自考", "学历培训"]
    keyword_list = get_all_advertiser_name_with_category()
    res_list = []
    for keyword in keyword_list:
        res_list += crawl_by_keyword(keyword)

    #res_list.sort()
    #res_list.reverse()
    res_list = filter_and_ranking(res_list)

    with open('../data/name.sorted', 'w') as wfd:
        for keyword, res in zip(keyword_list, res_list):
            wfd.write("{}\t{}\t{}\n".format(res[1], res[0], keyword))



    # r = []
    # with open('../data/res.sorted', 'r') as rfd:
    #     for res in rfd:
    #         res = res.strip().split('\t')
    #         if len(res) != 2:
    #             continue
    #         else:
    #             r.append(res[0])


    
    # res_list = []
    # with open('../data/res.sorted', 'r') as rfd:
    #     for res in rfd:
    #         res = res.strip().split()
    #         if len(res) != 2:
    #             continue
    #         res_list.append((int(res[0]), res[1]))

    # filtered_list = filter_and_ranking(res_list)




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

