# -*- coding: UTF-8 -*-
# 2021-05-15
# created by Rex
import sys
import collections
import random
import requests
import re
import pandas as pd
import json
import numpy as np
import os
import time
from time import sleep
import jieba
import jieba.analyse
from snownlp import SnowNLP
# define the class Taobao


class Taobao():
    def __init__(self, product_name,  ifsave=False):
        # self.searchcookie = cookies['search_cookie']
        # self.ajaxcookie = cookies['ajax_cookie']
        try:
            self.searchcookie = open(
                './Files/searchcookie.txt', encoding='utf-8').read().strip()
            self.ajaxcookie = open(
                './Files/ajaxcookie.txt', encoding='utf-8').read().strip()
        except Exception as e:
            print('初始化出错：', e)
            sys.exit(0)  # 终止程序
        self.name = product_name
        self.path = './{}'.format(product_name)
        self.search = self.SearchPage()
        if ifsave:  # 保存html
            if not os.path.exists(self.path):
                os.mkdir(self.path)
            with open(self.path+'/html.txt', 'w', encoding='utf-8') as f:
                f.write(self.search)
                print("the product {}'s html has been saved!".format(self.name))
            f.close()

    # 抓取页面内容，返回HTML
    def getHTML(self, url,  params, headers):
        try:
            r = requests.get(url,  params=params, headers=headers, timeout=30)
            # r.encoding = r.apparent_encoding
            if r.status_code == 200:
                return r.text
            else:
                return 'Request failed!'
        except:
            print('Fail to get html text')
            sys.exit(0)  # 终止程序

    # 重定向直通车链接
    def reget(self, url):
        headers = {
            'authority': 's.taobao.com',
            "Connection": "keep-alive",
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'referer': 'https://s.taobao.com',
            'cookie': self.searchcookie
        }
        response = requests.get(url, headers=headers, timeout=15)
        return response.url

    # 淘宝搜索页面html
    def SearchPage(self):
        params = {'q': self.name,
                  'imgfile': '',
                  'js': 1,
                  'stats_click': 'search_radio_all:1',
                  'initiative_id': 'staobaoz_20210516',
                  'ie': 'utf8'
                  }  # 淘宝搜索的一些参数
        headers = {
            'authority': 's.taobao.com',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            "Connection": "keep-alive",
            'referer': 'https://s.taobao.com',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cookie': self.searchcookie,
        }
        url = 'https://s.taobao.com/search'
        return self.getHTML(url, params, headers)

    # 根据搜索商品名，保存搜索页面48条商品详情
    def SaveItems(self):
        txtfile = open(self.path+'/html.txt', encoding='utf-8')
        # 正则表达式匹配字符串，识别需要的信息
        items = re.findall(
            '"nid":"(.*?)".*?"category":"(.*?)".*?"pid":"(.*?)".*?"title":"(.*?)".*?"raw_title":"(.*?)".*?".*?detail_url":"(.*?)".*?view_price":"(.*?)".*?"item_loc":"(.*?)".*?"view_sales":"(.*?)".*?"comment_count":"(.*?)".*?"user_id":"(.*?)".*?"nick":"(.*?)".*?"comment_url":"(.*?)"', txtfile.read(), re.S)
        if items == []:
            print('商品页面错误，未能保存商品详情，需要手动登录PC端淘宝网并更新login-cookie')
            return
        productsInfo = []
        tmp = {}
        for i, item in enumerate(items):
            tmp['index'] = i+1
            tmp['nid'] = item[0]
            tmp['category'] = item[1]
            tmp['pid'] = item[2]
            tmp['banner'] = item[3]
            tmp['title'] = item[4]
            tmp['price'] = item[6]
            tmp['location'] = item[7]
            tmp['pay_num'] = item[8]
            tmp['comment_num'] = item[9]
            tmp['user_id'] = item[10]
            tmp['store_name'] = item[11]

            url = item[5].encode('utf-8').decode('unicode_escape')
            if 'simba.taobao' in url:  # 如果是直通车， 把直通车链接通过get方法，转为淘宝/天猫直链
                print('\r转链中......', end='\t')
                try:
                    tmp['detail_url'] = self.reget(url=item[5].encode(
                        'utf-8').decode('unicode_escape'))
                    tmp['comment_url'] = self.reget(url=item[12].encode(
                        'utf-8').decode('unicode_escape'))
                except Exception as e:
                    print(e)
                    print("\r连接超时，尝试重连", end='\t')
                    self.SaveItems()

            else:  # 如果是淘宝/天猫直链，需要加上https:
                tmp['detail_url'] = 'https:'+item[5].encode(
                    'utf-8').decode('unicode_escape')
                tmp['comment_url'] = 'https:'+item[12].encode(
                    'utf-8').decode('unicode_escape')

            if 'tmall' in tmp['detail_url']:
                tmp['platform'] = 'tmall'
            if 'taobao' in tmp['detail_url']:
                tmp['platform'] = 'taobao'
            tmp['product'] = self.name
            productsInfo.append(tmp.copy())
        with open(self.path+'/productsInfo.json', "w", encoding='utf-8') as f:
            f.write(json.dumps(productsInfo,
                               ensure_ascii=False,
                               indent=4,
                               separators=(',', ':')))

        f.close()
        print('productInfo has been saved!')

    # 抓取单个商品的一页评论
    # 注意区分淘宝和天猫评论界面
    def CommentPage(self, productInfo, page=1):
        platform = productInfo['platform']
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                   'referer': productInfo['detail_url'],
                   'cookie': self.ajaxcookie
                   }

        if platform == 'taobao':
            params = {'auctionNumId': productInfo['nid'],  # 对应item里的nid
                      'userNumId': productInfo['user_id'],  # 对应item里的user_id
                      'currentPageNum': page,
                      'pageSize': 20,
                      'rateType': '',  # 2是好评，#0是中评，#-1是差评
                      'orderType': 'sort_weight',
                      'attribute': '',
                      'sku': '',
                      'hasSku': 'false',
                      'folded': 0,
                      'ua': '098#E1hv69vRvPpvUvCkvvvvvjiWPFzhsjimn2F9Qj1VPmPOgjiRPssylj3WP2LptjtWRvhvCvvvvvvVvpvjzn147rGIZuQCvvyvh2ImFIgvhjuevpvhvvmv9F9CvvpvvvvvvvhvC9vhvvCvpb9Cvm9vvvvUS6vvipvv3jDvpvsovvvHvhCvHUUvvvZvphvZgpvvCOCvpCmQuvhvmvvv9bQAs/Z9kvhvC99vvOCtop9CvhQWti6vCAeiS47tHCHkoqmxfwmK5FaJKXVYz40AVA3lafmxdXyaUneYiXhpVVQEfa1lYb8rwm0QiNoxdX+aUr2yAWpaejnVgRmQ0fJ629hvCvvvMM/VvpvhvvpvvUvCvvswPh35GnMwznQN5DIgvpvhvvvvvv==',
                      '_ksTS': 1621131891625_1239,
                      'callback': 'jsonp_tbcrate_reviews_list'
                      }
            url = 'https://rate.taobao.com/feedRateList.htm'
        if platform == 'tmall':
            params = {'itemId': productInfo['nid'],  # 对应item里的nid
                      'sellerId': productInfo['user_id'],  # 对应item里的user_id
                      'order': 3,  # 排序方式：1-按照时间排序  3-默认排序
                      'currentPage': page,
                      'content': 1  # 有内容
                      }
            url = 'https://rate.tmall.com/list_detail_rate.htm'

        # --------请求url,天猫返回的是保存评论的json，需要从jsonp1195(.*)中提取-------------------
        compiler = re.compile(r"[(](.*)[)]", re.S)  # 贪婪匹配
        r = self.getHTML(url, params, headers)
        comments = re.findall(compiler, r)
        try:
            return json.loads(comments[0])  # 返回商品评论的json文件
        except Exception as e:
            # print('CommentPage 评论为空:', e)
            return {}
            # sys.exit(0)  # 终止程序

        # --------请求url,天猫返回的是保存评论的json，需要从jsonp1195(.*)中提取-------------------

    # 抓取单个商品的所有评论
    def SaveComments(self, productInfo, index=''):
        '''
        productInfo: type(json)
        index: the rank-order of product
        return: comments of this product.(type json)
        '''
        wait = 2  # 评论翻页的停顿时间(建议>5s)，请求太频繁会触发反爬虫机制
        name = productInfo['product']
        Comments = self.CommentPage(productInfo)  # get the first-page comments
        if Comments == {}:
            print('SaveComments 未能抓取{}(rank={})第一页评论，重试一次......'.format(name, index))
            sleep(2)
        Comments['productInfo'] = productInfo
        platform = productInfo['platform']
        sleep(random.uniform(wait, wait+3))
        if platform == 'taobao':
            taotmp = Comments.copy()
            page = 1
            try:
                curPage = taotmp['currentPageNum']
                nextPage = taotmp['maxPage']
                while nextPage > curPage:
                    page += 1
                    # 手动实现进度
                    print('\rdownloading {}(rank={}) 第 {} 页淘宝评论'.format(
                        name, index, page), end="\t")
                    taotmp = self.CommentPage(productInfo, page)
                    comments = taotmp['comments']
                    Comments['comments'] += comments.copy()
                    curPage = taotmp['currentPageNum']
                    nextPage = taotmp['maxPage']
                    sleep(random.uniform(wait, wait+3))
                print('\n')  # 换行
            except:
                print(
                    '抓取淘宝评论出错，可能触发阿里反爬虫机制，当前为{}(rank={})-第{}页，需要更新ajax-cookie'.format(name, index, page))
            Comments['total_num'] = len(Comments['comments'])

        if platform == 'tmall':
            # 获取天猫评论的最大页数
            maxPage = Comments['rateDetail']['paginator']['lastPage']
            try:
                for page in range(2, maxPage+1):
                    # 手动实现进度
                    print('\rdownloading {}(rank={}) 第 {:^2}/{:^2} 页天猫评论，当前进度 {:.2f}%'.format(name, index, page,
                                                                                              maxPage, 100*page/maxPage), end="\t")

                    tmp = self.CommentPage(productInfo, page)
                    ratelist = tmp['rateDetail']['rateList']
                    Comments['rateDetail']['rateList'] += ratelist.copy()
                    sleep(random.uniform(wait, wait+3))
                print('\n')  # 换行
            except:
                print(
                    '抓取天猫评论出错，可能触发阿里反爬虫机制，当前为{}(rank={})-第{}页，需要更新ajax-cookie'.format(name, index, page))
            Comments['rateDetail']['total_num'] = len(
                Comments['rateDetail']['rateList'])
        # # 保存评论
        # for i, com in enumerate(Comments['rateDetail']['rateList']):
        #     print('第%s条' % str(i+1), com['rateContent'])
        with open(self.path+'/comments/comments%s.json' % index, "w", encoding='utf-8') as f:
            f.write(
                json.dumps(Comments,
                           ensure_ascii=False,
                           indent=4,
                           separators=(',', ':')))
        f.close()

    # 保存前30个商品的所有评论
    def SaveAllComments(self, rank=30):
        '''
        retrun: 保存前30商品的全部评论
        '''

        if not os.path.exists(self.path+'/comments'):
            os.mkdir(self.path+'/comments')
        try:
            with open('./{}/productsInfo.json'.format(self.name), 'r', encoding='utf-8') as f:
                args = json.load(f)
            f.close()
        except Exception as e:
            print('SaveAllComments 出错:', e)
            sys.exit(0)  # 终止程序
        for index in range(1, rank+1):
            productInfo = args[index-1]

            self.SaveComments(productInfo, index)

    # json格式的评论按需保存为csv
    def comments2csv(self, rank=30):
        for index in range(1, rank+1):
            tmp = {}
            comments = []
            try:
                with open('./{}/comments/comments{}.json'.format(self.name, index), 'r', encoding='utf-8') as f:
                    args = json.load(f)
                f.close()
                if args['productInfo']['platform'] == 'tmall':
                    for i, arg in enumerate(args['rateDetail']['rateList']):
                        # 应该加入rowfor row in list:
                        tmp['index'] = i+1
                        tmp['用户昵称'] = arg['displayUserNick']
                        tmp['初评'] = arg['rateContent']
                        tmp['初评日期'] = arg['rateDate']
                        if arg['appendComment'] != None:
                            tmp['追评'] = arg['appendComment']['content']
                            tmp['追评日期'] = arg['appendComment']['commentTime']
                            tmp['追评天数'] = arg['appendComment']['days']
                        else:
                            tmp['追评'] = 'Null'
                            tmp['追评日期'] = 'Null'
                            tmp['追评天数'] = 'Null'
                        tmp['是否有用'] = arg['useful']
                        tmp['用户id'] = arg['id']
                        tmp['超级会员'] = arg['goldUser']
                        tmp['产品'] = args['productInfo']['product']
                        tmp['类别'] = arg['auctionSku']
                        tmp['标题'] = args['productInfo']['title']
                        tmp['平台'] = args['productInfo']['platform']
                        tmp['商品链接'] = args['productInfo']['detail_url']
                        comments.append(tmp.copy())
                if args['productInfo']['platform'] == 'taobao':
                    for i, arg in enumerate(args['comments']):
                        tmp['index'] = i+1
                        tmp['用户昵称'] = arg['user']['nick']
                        tmp['初评'] = arg['content']
                        tmp['初评日期'] = arg['date']
                        tmp['评价'] = arg['rate']  # 1是好评，0是中评，-1是差评
                        if arg['append'] != None:
                            tmp['追评'] = arg['append']['content']
                            tmp['追评天数'] = arg['append']['dayAfterConfirm']
                        else:
                            # raterType？全部评论，中评
                            # validscore赞与踩
                            # rateId
                            tmp['追评'] = 'Null'
                            tmp['追评日期'] = 'Null'
                            tmp['追评天数'] = 'Null'
                        tmp['是否有用'] = arg['useful']
                        tmp['赞'] = arg['validscore']
                        tmp['Rateid'] = arg['rateId']
                        level = arg['user']['displayRatePic']
                        vip = re.findall('.*?_(.*?).gif', level, re.S)
                        try:
                            tmp['用户等级'] = vip[0]
                        except:
                            tmp['用户等级'] = 'Null'

                        tmp['产品'] = args['productInfo']['product']
                        tmp['类别'] = arg['auction']['sku']
                        tmp['标题'] = args['productInfo']['title']
                        tmp['平台'] = args['productInfo']['platform']
                        tmp['商品链接'] = args['productInfo']['detail_url']
                        comments.append(tmp.copy())

                data = pd.DataFrame(comments)
                data.to_csv(
                    './{}/comments/comments{}.csv'.format(self.name, index), encoding="utf_8_sig", index=False)
                print('\r{}(rank={})评论另存为csv表格'.format(
                    self.name, index), end='\t')
            except Exception as e:
                print('comments2csv 异常：', e)
                sys.exit(0)  # 终止程序
                # 抛出异常
    # -------------------------------------------数据分析模块--------------------------------

    def Analyze(self, userkeys=[], order=30):
        file = open('./Files/functional.txt', encoding='utf-8').read()
        file = file.strip().split('\n')
        default_keys = [line for line in file if line != '']
        userkeys.reverse()
        keys = list(set(default_keys+userkeys))  # 合并去重
        RankList = []
        for index in range(1, order+1):
            try:
                df = pd.read_csv(
                    './{}/comments/comments{}.csv'.format(self.name, index))
                tmp = {}
                tmp['产品'] = df['产品'][0]
                tmp['平台'] = df['平台'][0]
                tmp['标题'] = df['标题'][0]
                tmp['类别'] = df['类别'][0]
                for key in keys:
                    criteria2 = df.loc[(df['追评'].str.contains(key))
                                       | (df['初评'].str.contains(key))]
                    score = []
                    for i, comments in enumerate(criteria2['初评']):
                        s = SnowNLP(comments)
                        score.append(s.sentiments)
                    for j, com in enumerate(criteria2['追评']):
                        if com != 'Null':
                            s = SnowNLP(com)
                            score.append(s.sentiments)
                    if score == []:
                        tmp[key] = 0
                        tmp[key+'认可度'] = 0
                    else:
                        mu = np.mean(score)
                        pos = [x for x in score if x > mu]
                        tmp[key] = len(score)
                        tmp[key+'认可度'] = len(pos)/len(score)
                tmp['商品链接'] = df['商品链接'][0]
                RankList.append(tmp.copy())
                print('\rrank={} ending'.format(index), end='\t')
            except Exception as e:
                print('\rrank={}, {}'.format(index, e), end='\t')
        re = pd.DataFrame(RankList)
        re.loc['sum'] = re[keys].apply(np.sum, axis=0)
        head = ['产品', '平台', '标题', '类别']
        tail = ['商品链接']
        tmp = re[keys].sort_values(by='sum', axis=1, ascending=False)
        main_order = tmp.columns.values.tolist()
        self.hotkeys = '\r{}的热门关键词：{}'.format(
            self.name, main_order[0:10], end="\t")
        for selfkey in userkeys:
            main_order.remove(selfkey)
            main_order = [selfkey]+main_order
        for key in keys:
            index = main_order.index(key)
            main_order.insert(index+1, key+'认可度')
            # 认可度表示为百分数
            re[key+'认可度'] = re[key+'认可度'].apply(lambda x: format(x, '.1%'))
        main_order = head+main_order+tail
        re = re[main_order]
        re = re.drop('sum', axis=0)
        re.to_csv('{}功效推荐汇总表.csv'.format(self.name),
                  encoding="utf_8_sig", index=False)

    def Show(self, userkey, userkeys, method, order, print_csv=True, save_csv=True):
        if not os.path.exists('{}功效推荐汇总表.csv'.format(self.name)):
            print('asddaa')
            self.Analyze(self, userkeys, order=30)
            sleep(2)
        df = pd.read_csv('{}功效推荐汇总表.csv'.format(self.name))
        if method == 'approval_num':
            df = df.sort_values(by=userkey, axis=0, ascending=False)
            txt = '_按{}认可人数推荐'.format(userkey)
        elif method == 'approval_rate':
            df = df.sort_values(by=userkey+'认可度', axis=0, ascending=False)
            txt = '_按{}认可度推荐'.format(userkey)
        else:
            print(
                "\rmethod does not exist! need 'approval_num' or approval_rate'.", end='\t')
            return
        table = df[['产品', '平台', '标题', '类别', userkey, userkey+'认可度', '商品链接']]
        if print_csv:
            print(table)
        if save_csv:
            table.to_csv('{}{}.csv'.format(self.name, txt),
                         encoding="utf_8_sig", index=False)
        pass


# print('positive:', len(pos))
# print('rate:{:.1%}'.format(len(pos)/len(sentiment)))

# a.to_csv('e.csv')
# print(df[criteria]['追评'])

# 眼霜热门关键词：

# a = '雅诗兰黛眼霜小棕瓶抗蓝光淡化黑眼圈紧致特润修护复眼部精华15ml'
# jieba.add_word('抗蓝光')
# b = jieba.analyse.extract_tags(a, topK=100, withWeight=False)
# print(b)

# print('2', jieba.lcut(a, cut_all=False, HMM=True))
# s = SnowNLP(a)
# print(s.words)
# print(s.sentences)
# print(s.keywords(10))

# for sentence in s.sentences:
#     if key in sentence:
#         print('<{}>的句子情感得分:{}'.format(
#             sentence, SnowNLP(sentence).sentiments))
#         print('<{}>的整体情感得分:{}'.format(comments, s.sentiments))
# s = SnowNLP(com)
# if s.sentiments > 0.7 and s.sentiments < 0.8:
#     print(com)
#     print(s.sentences)
#     for sen in s.sentences:
#         if key in sen:
#             print(SnowNLP(sen).sentiments)


# # 读取csv
# punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~“”？，！【】（）、。：；’‘……￥·"""
# dicts = {i: '' for i in punctuation}
# jieba.add_word('双十一')
# jieba.add_word('双11')
# jieba.add_word('618')
# jieba.add_word('此用户没有填写评论')
# jieba.load_userdict('functional.txt')

# # punc_table = str.maketrans(dicts)
# # string_data = ''

# for index in range(1, 31):
#     try:
#         df = pd.read_csv('./眼霜/comments/comments{}.csv'.format(index))
#         comment = []
#         # content = (','.join(i for i in df['初评'])+','.join(i for i in df['追评']))
#         content = (','.join(i for i in df['标题']))
#         # 定义正则表达式匹配模式（空格等）
#         pattern = re.compile(u'\t|\n|\.|-|:|;|\)|\(|\?|\ |"')
#         tmp = re.sub(pattern, '', content)     # 将符合模式的字符去除
#         string_data = string_data+tmp
#         # print(index)
#     except Exception as e:
#         print(index, e)

# exclude = open('./exclude.txt').read()
# words = jieba.lcut(string_data, cut_all=False, HMM=True)
# obj = []
# for word in words:
#     word = word.translate(punc_table)
#     if len(word) > 1 and word not in exclude:
#         obj.append(word.strip())


# word_counts = collections.Counter(obj)       # 对分词做词频统计
# word_counts_top = word_counts.most_common(30)    # 获取前100个最高频的词
# print(jieba.lcut(df['标题'][0]))
# for i in word_counts_top:
#     print(i[0])
