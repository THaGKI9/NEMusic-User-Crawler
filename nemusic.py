# coding:utf-8
import logging
import re
from json import dumps

import requests
from requests.exceptions import ConnectionError
from Crypto.Cipher import AES


logger = logging.getLogger(__name__)


def aes_encrypt(data, key, iv='0102030405060708'):
    '''encrypt with aes-128-cbc alogrithm

    :param data: data to encrypt
    :param key:
    :param iv: intializing vector
    :returns: base64 encoded string
    '''
    # PKCS #7 padding
    padding_length = AES.block_size - len(data) % AES.block_size
    data += padding_length * chr(padding_length)

    # AES.new generate a object that can be used ONLY ONE TIME
    #   this feature waste me two days to solve.
    coder = AES.new(key, AES.MODE_CBC, iv)
    return coder.encrypt(data).encode('base64').strip()


def encode_payload(payload):
    '''encode payload before POST to server

    :param payload: a dict
    :returns: a dict
    '''
    text = dumps(payload)
    key = '0CoJUm6Qyw8W8jud'

    seed = 'd47cmt5fXEoyUbPd'  # the random seed
    encText = aes_encrypt(aes_encrypt(text, key), seed)
    # this key is computing using two constants and a random 16 length string
    # i used a fixed random string to produce this key
    # the algorithm can be found in the webpage's core.js script
    #   by searching this 'h.encSecKey = c'
    #   Reference Library: BarrettMu.js and BigInt.js on Github
    encSecKey = (
        '0032827ffab3bd5e08fa89039eb0f5e8c59da02531c2b7c477b2cb47152a4885'
        'fd04466bee9a435367db73270509fd0b0d94e4a4d64247f871fd2b324a77987f'
        'b2f351216159fac9f7d820965ad0b37c81b8eb37a0f0066df7cf921c61e6e1b6'
        '137e2a24e0b6fc4dc3584c29ce4996f7f96af386d0e742b901c44b054befb347'
    )

    return {'params': encText, 'encSecKey': encSecKey}


def get_fans(uid, offset=0):
    '''query a set of user[uid]'s fans

    :param uid: user id
    :param offset: times of 100
    :returns: tuple(is_success, is_more, user_set)
    '''
    log_prefix = 'getting fans of %s, offset %d. ' % (uid, offset)
    logger.debug(log_prefix)

    param = {'userId': uid, 'offset': offset, 'limit': 100, 'total': 'false'}
    url = 'http://music.163.com/weapi/user/getfolloweds/'
    referer = 'http://music.163.com/user/fans?id=' + str(uid)
    result = requests.post(url=url, data=encode_payload(param),
                           headers={'Referer': referer})

    if result:
        json = result.json()
        code = json.get('code', 0)
        if code == 200:
            user_list = {str(user.get('userId', ''))
                         for user in json.get('followeds', [])}
            return True, json.get('more', False), user_list
        else:
            logger.debug(log_prefix + 'Get reply with code %d, json:',
                         code, result.content)
    else:
        logger.debug(log_prefix + 'Get reply with HTTP status code %d',
                     result.status_code)

    return False, None, None


def get_follows(uid, offset=0):
    '''query a set of user[uid]'s follows

    :param uid: user id
    :param offset: times of 100
    :returns: tuple(is_success, is_more, user_set)
    '''
    log_prefix = 'getting follows of %s, offset %d. ' % (uid, offset)
    logger.debug(log_prefix)

    param = {'userId': uid, 'offset': offset, 'limit': 100, 'total': 'false'}
    url = 'http://music.163.com/weapi/user/getfollows/' + uid
    referer = 'http://music.163.com/user/follows?id=' + uid
    result = requests.post(url=url, data=encode_payload(param),
                           headers={'Referer': referer})

    if result:
        json = result.json()
        code = json.get('code', 0)
        if code == 200:
            user_list = {str(user.get('userId', ''))
                         for user in json.get('follow', [])}
            return True, json.get('more', False), user_list
        else:
            logger.debug(log_prefix + 'Get reply with code %d, json:',
                         code, result.content)
    else:
        logger.debug(log_prefix + 'Get reply with HTTP status code %d',
                     result.status_code)

    return False, None, None


re_uid = re.compile(ur'window.hostId = (\d*?);')
re_nickname = re.compile(ur'<span class="tit f-ff2 s-fc0">([\s\S]*?)</span>')
re_gender = re.compile(ur'<i class="icn u-icn u-icn-0(\d)"></i>')
re_location = re.compile(ur's-fc3">\n<span>所在地区：([\s\S]*?)</span>')
re_level = re.compile(ur'icn2-lev">(\d*?)<i class="right u-icn2 u-icn2-levr">')

re_listened_count = re.compile(ur'<h4>累积听歌(\d*?)首</h4>')
re_fan_count = re.compile(ur'<strong id="fan_count">(\d*?)</strong>')
re_follow_count = re.compile(ur'<strong id="follow_count">(\d*?)</strong>')
re_event_count = re.compile(ur'<strong id="event_count">(\d*?)</strong>')

re_create_count = re.compile(ur'f-ff2">[\s\S]*?创建的歌单（(\d*?)）</span>')
re_collect_count = re.compile(ur'f-ff2">[\s\S]*?收藏的歌单（(\d*?)）</span>')


def get_profile(uid):
    result = requests.get('http://music.163.com/user/home?id=' + str(uid))
    if not result:
        return

    response_text = result.content.decode(result.encoding)

    def extract_group(regexp, is_int=False, group=1):
        match = regexp.search(response_text)
        rv = match.group(group) if match else ''
        if is_int:
            try:
                rv = int(rv)
            except ValueError:
                rv = -1
        return rv

    profile = {
        'uid': extract_group(re_uid, True),
        'nickname': extract_group(re_nickname),
        'gender': extract_group(re_gender, True),
        'location': extract_group(re_location),
        'level': extract_group(re_level, True),
        'listened_count': extract_group(re_listened_count, True),
        'fan_count': extract_group(re_fan_count, True),
        'follow_count': extract_group(re_follow_count, True),
        'event_count': extract_group(re_event_count, True),
        'create_count': extract_group(re_create_count, True),
        'collect_count': extract_group(re_collect_count, True),
    }

    return profile


if __name__ == '__main__':
    pprint = __import__('pprint').pprint
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    # print len(get_fans('3503249')[2])
    # print len(get_follows('3503249')[2])
    # print get_profile('3503249')