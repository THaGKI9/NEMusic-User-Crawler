from base64 import b64encode
from json import dumps
from Crypto.Cipher import AES


def aes_encrypt(data, key, iv='0102030405060708'):
    '''encrypt with aes-128-cbc alogrithm

    :param data: data to encrypt
    :param key:
    :param iv: intializing vector
    :returns: base64 encoded string
    '''
    # PKCS #7 padding
    padding_length = AES.block_size - len(data) % AES.block_size
    data += padding_length * chr(padding_length).encode()

    # AES.new generate a object that can be used ONLY ONE TIME
    #   this feature waste me two days to solve.
    coder = AES.new(key, AES.MODE_CBC, iv)
    return b64encode(coder.encrypt(data))


def encode_payload(payload, seed="d47cmt5fXEoyUbPd"):
    '''encode payload before POST to server

    :param payload: a dict
    :param seed: a 16-size string in random combination
    :returns: a dict
    '''
    text = dumps(payload).encode('utf-8')
    key = '0CoJUm6Qyw8W8jud'

    encText = aes_encrypt(aes_encrypt(text, key), seed).decode()
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
