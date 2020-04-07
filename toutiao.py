# coding=utf-8
import base64
import binascii
import datetime
import hashlib
import json
import logging
import math
import random
import re
import time
from urllib.parse import urlparse

import requests
from fake_useragent import UserAgent
from requests.packages.urllib3.exceptions import *

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

"""
根据头条号id获取账号作品列表页， 在列表页取出视频id，再获取视频下载页，组合下载地址
"""


class Spider(object):
    def __init__(self):
        super(Spider, self).__init__()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                            filename='./logging.txt')
        self.logger = logging.getLogger()

    # URL拼接
    @staticmethod
    def right_shift(val, n):
        return val >> n if val >= 0 else (val + 0x100000000) >> n

    @staticmethod
    def read_from(path):
        with open(path, 'r') as f:
            con = f.readlines()
        return con

    @staticmethod
    def write_into(path, content):
        with open(path, 'a') as f:
            f.write(content)
            f.write('\n')

    def start(self):
        """ 启动方法 """
        t_name = "网上车市"
        t_id = '54564789207'

        next_cursor = 0
        self.get_response(next_cursor=next_cursor, t_name=t_name, t_id=t_id)

    def get_response(self, next_cursor, t_name, t_id):
        """
        请求作品列表页
        :param next_cursor: 偏移量
        :param t_name: 账号名
        :param t_id: 账号id
        :return:  None
        """
        mid = self.get_mid(openid=t_id)
        if mid == "0":
            print("mid is None")
        else:
            headers = {
                'authority': 'www.dcdapp.com',
                'method': 'GET',
                'path': '/motor/profile/get_news?media_id={}&cursor=0'.format(mid),
                'scheme': 'https',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Mobile Safari/537.36',
                }
            start_urls = "https://www.dcdapp.com/motor/profile/get_news?media_id={}&cursor={}".format(mid, next_cursor)
            print(start_urls)
            time.sleep(random.randint(2, 3))
            try:
                content = requests.get(start_urls, headers=headers, timeout=30, verify=False)
                res = content.text
                rjson_json = json.loads(res, encoding="utf-8")
                status = rjson_json.get('message')
                rjson = rjson_json.get('data').get('list')
                if status != "success" or not rjson:
                     print("page error")
                next_cursor = rjson_json.get('data').get('next_cursor')
            except Exception as e:
                self.write_into(path='./error.recoder.txt', content='error ' + str(e))

            else:
                stop_flag = self.parse(data=rjson, headers=headers, toutiao_user_id=t_id, toutiao_user_name=t_name)
                if stop_flag == "next page":
                    self.get_response(next_cursor=next_cursor, t_name=t_name, t_id=t_id)

    def get_mid(self, openid):
        """
        获取 mid 参数
        :param openid: 账号id
        :return: String
        """
        ua = UserAgent()
        url = 'http://m.toutiao.com/profile/' + str(openid) + '/'
        headers = {
            'User-Agent': ua.random
        }
        try:
            body = requests.get(url, headers=headers).text
        except Exception as error:
            self.logger.info(', '.join([u'请求mid错误', str(openid), str(error)]))
            return None
        else:
            obj = re.findall('\"media_id\": (\d+),', body)
            try:
                a = obj[0]
            except Exception as error:
                return None
            else:
                return a

    @staticmethod
    def get_as_cp():
        """
        获取 as cp 参数
        :return: None
        """
        t = int(math.floor(time.time()))
        e = hex(t).upper()[2:]
        m = hashlib.md5()
        m.update(str(t).encode(encoding='utf-8'))
        i = m.hexdigest().upper()

        if len(e) != 8:
            AS = "479BB4B7254C150"
            CP = "7E0AC8874BB0985"
            return AS, CP
        n = i[0:5]
        a = i[-5:]
        s = ''
        r = ''

        for o in range(5):
            s += n[o] + e[o]
            r += e[o + 3] + a[o]
        AS = 'A1' + s + e[-3:]
        CP = e[0:3] + r + 'E1'
        return AS, CP

    def parse(self, data, headers, toutiao_user_id, toutiao_user_name):
        """
        解析json列表
        """
        if len(data) == 0:
            self.logger.info(', '.join([u'账号页面请求错误记录-列表为空', toutiao_user_name, str(toutiao_user_id)]))
            return 'next account'

        for element in data:
            cells = element.get("group_cell")
            if cells is None:
                print('group_cell is none')
                cells = element.get("thread_cell")

                self.logger.info(' '.join([u'group_cell 内容是None', toutiao_user_name, str(toutiao_user_id)]))
                if cells is None:
                    print('thread_cell is none')
                    self.logger.info(', '.join([u'thread_cell 内容是None', toutiao_user_name, str(toutiao_user_id)]))
                    continue
                else:
                    print('thread_cell is not none')

            video_id = cells.get("video_id")

            publish_time = element.get("create_time")
            publish_time = datetime.datetime.fromtimestamp(publish_time).strftime("%Y-%m-%d")

            image_list = cells.get('image_list')
            if image_list is None:
                continue

            if len(image_list) < 1:
                continue


            temp = image_list[0]
            cover_url = temp.get('url')
            title = cells.get('title')

            # 只要 video
            if video_id is None:
                print("文章")
                self.logger.info(', '.join([u'视频的id为空', toutiao_user_name, str(toutiao_user_id)]))
                continue
            else:

                self.get_video_url(video_id=video_id)

        return 'next page'

    def get_video_url(self, video_id):
        # 组合获取视频url
        r = str(random.random())[2:]
        mid_url = 'http://i.snssdk.com/video/urls/1/toutiao/mp4/%s' % video_id

        n = urlparse(mid_url).path + '?r=' + r
        c = binascii.crc32(n.encode())
        s = self.right_shift(c, 0)
        p1 = mid_url + '?r=%s&s=%s' % (r, s)

        try:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Host': 'i.snssdk.com',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
                }

            req_content = requests.get(p1, headers=headers)
            self.logger.info("请求视频链接地址：" + req_content.url)
            content = req_content.text

        except Exception as e:
            self.logger.info(', '.join(['请求下载视频链接出错', str(e)]))
        else:
            try:
                json_content = json.loads(content)
            except Exception as error:
                self.logger.info(', '.join(['获取下载url的json解析出错', str(error)]))
            else:
                main_url = self.get_main_url(json_content=json_content)
                if main_url is None:
                    self.logger.info("获取720p链接失败")
                else:
                    self.logger.info("获取720p链接成功")
                    download_url = base64.b64decode(main_url).decode()
                    print("download_url", download_url)
                    self.logger.info(', '.join(['下载 url', download_url]))

    @staticmethod
    def get_main_url(json_content):
        """ 解析json 获取 main_url  只取720p"""
        data = json_content.get('data')
        if data is None:
            return None

        video_list = data.get("video_list")
        if video_list is None:
            return None

        for video_key, video_value in video_list.items():
            video = video_list.get(video_key)
            definition = video.get('definition')

            if '720p' in definition:
                main_url = video.get('main_url')
                return main_url


if __name__ == '__main__':
    spider = Spider()
    spider.start()

