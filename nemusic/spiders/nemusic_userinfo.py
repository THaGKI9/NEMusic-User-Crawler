from json import dumps, loads
from urllib.parse import urlencode

import scrapy
import scrapy.loader
import scrapy.loader.processors

from nemusic.items import NEMusicUserProfile
from nemusic.utils import nemusic_crypto


class NemusicUserinfoSpider(scrapy.Spider):
    name = "nemusic_userinfo"
    user_seed = '3503249'
    allowed_domains = ['music.163.com']

    def start_requests(self):
        return [self.make_request_get_user_profile(self.user_seed)]

    def make_request_get_user_profile(self, uid, from_uid=None):
        url = 'http://music.163.com/user/home?id=' + str(uid)
        return scrapy.Request(
            url,
            callback=self.parse_user_profile,
            meta={'uid': str(uid), 'from_uid': str(from_uid)}
        )

    def make_request_get_fans(self, uid, offset=0):
        '''
        :param uid: user id
        :param offset: times of 100
        :rtype: scrapy.Request
        '''
        params = dict(userId=uid, offset=offset, limit=100, total='false')
        return scrapy.Request(
            method='POST',
            url='http://music.163.com/weapi/user/getfolloweds',
            headers={
                'Referer': 'http://music.163.com/user/fans?id=' + str(uid),
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body=urlencode(nemusic_crypto.encode_payload(params)),
            callback=self.parse_fans,
            meta=params,
            dont_filter=True
        )

    def make_request_get_follows(self, uid, offset=0):
        '''
        :param uid: user id
        :param offset: times of 100
        :rtype: scrapy.Request
        '''
        params = dict(userId=uid, offset=offset, limit=100, total='false')
        return scrapy.Request(
            method='POST',
            url='http://music.163.com/weapi/user/getfollows/' + str(uid),
            headers={
                'Referer': 'http://music.163.com/user/follows?id=' + str(uid),
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body=urlencode(nemusic_crypto.encode_payload(params)),
            callback=self.parse_follows,
            meta=params,
            dont_filter=True
        )

    def parse_user_profile(self, res):
        p = scrapy.loader.ItemLoader(item=NEMusicUserProfile(), response=res)
        p.default_output_processor = scrapy.loader.processors.TakeFirst()

        p.add_css('uid', '.m-record::attr(data-uid)')
        p.add_css('nickname', '.tit.f-ff2.s-fc0::text')
        p.add_css('gender', '.icn.u-icn::attr(class)', re=r'u-icn u-icn-0(\d)')
        p.add_css('location', '.inf.s-fc3 span::text', re=r'所在地区：([\s\S]*)')
        p.add_css('level', '.u-icn2-lev::text')
        p.add_css('listened_count', '.m-record::attr(data-songs)')
        p.add_css('fan_count', '#fan_count::text')
        p.add_css('follow_count', '#follow_count::text')
        p.add_css('event_count', '#event_count::text')
        p.add_css('create_count', '#cHeader .f-ff2::text',
                  re=r'[\s\S]*?创建的歌单（(\d*?)）')
        p.add_css('collect_count', '#sHeader .f-ff2::text',
                  re=r'[\s\S]*?收藏的歌单（(\d*?)）')

        item = p.load_item()
        if item == {}:
            self.log('Ignore empty profile. uid=%(uid)s, from=%(from_uid)s',
                     res.meta)
        else:
            yield p.load_item()
        yield self.make_request_get_fans(res.meta['uid'])
        yield self.make_request_get_follows(res.meta['uid'])

    def parse_fans(self, res):
        uid = res.meta['userId']
        tips = 'uid=%(userId)s, offset=%(offset)s, limit=%(limit)s' % res.meta
        try:
            data = loads(res.body_as_unicode())
        except:
            self.logger.error('Get fans failed. No json is loaded. ' + tips)
            return

        if str(data.get('code')) != '200':
            self.logger.error('Get fans faield. Code is %s. %s',
                              (str(data.code), tips))
            return

        fans = data.get('followeds')
        if not isinstance(fans, list):
            self.logger.warn('Get a empty list of fans. ' + tips)
        else:
            for fan in fans:
                fan_id = fan.get('userId')
                if not fan_id:
                    log = 'A fan\'s profile does not contains a user id. '
                    log += 'Profile: %s. ' + dumps(fan)
                    log += tips
                    self.logger.warn(log)
                    continue
                yield self.make_request_get_user_profile(fan_id, uid)

        has_more = data.get('more') is True
        if has_more:
            uid = res.meta['userId']
            offset = res.meta['offset']
            yield self.make_request_get_fans(uid, offset + 100)

    def parse_follows(self, res):
        uid = res.meta['userId']
        tips = 'uid=%(userId)s, offset=%(offset)s, limit=%(limit)s' % res.meta
        try:
            data = loads(res.body_as_unicode())
        except:
            self.logger.error('Get follows failed. No json is loaded. ' + tips)
            return

        if str(data.get('code')) != '200':
            self.logger.error('Get follows faield. JSON is %s. %s',
                              (str(res.body_as_unicode()), tips))
            return

        fans = data.get('follow')
        if not isinstance(fans, list):
            self.logger.warn('Get a empty list of follows. ' + tips)
        else:
            for fan in fans:
                fan_id = fan.get('userId')
                if not fan_id:
                    log = 'A followed\'s profile does not contains a user id. '
                    log += 'Profile: %s. ' + dumps(fan)
                    log += tips
                    self.logger.warn(log)
                    continue
                yield self.make_request_get_user_profile(fan_id, uid)

        has_more = data.get('more') is True
        if has_more:
            uid = res.meta['userId']
            offset = res.meta['offset']
            yield self.make_request_get_follows(uid, offset + 100)
