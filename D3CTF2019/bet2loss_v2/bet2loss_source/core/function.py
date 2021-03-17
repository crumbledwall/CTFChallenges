import smtplib
import traceback
from random import Random
import hashlib
import time

def random_str(size=8):
    str = ""
    chars = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890'
    length = len(chars) - 1
    random = Random()

    for i in range(size):
        str += chars[random.randint(0, length)]
    return str


def random_num(start=2 ** 20, end=2 ** 30):
    random = Random()
    return random.randint(start, end)

def get_code():
    hashobj = hashlib.md5()
    hashobj.update(bytes(str(time.time()), encoding='utf-8'))
    code_hash = hashobj.hexdigest()[:6]
    return code_hash


