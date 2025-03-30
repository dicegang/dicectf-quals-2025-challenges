def fmt_bytes(b: bytes):
    return f"unsigned char data[] = {{{",".join(str(n) for n in b)}}};\n"


flag = b"dice{n0w_w3r3_c0oK1nG_w1tH_g4s!}"
flagparts = [int.from_bytes(flag[i : i + 8], "little") for i in range(0, len(flag), 8)]

def rotl(n, i):
    return ((n << i) % 2**64) | (n >> (64 - i))

def transform_ono2(cur):
    for _ in range(32):
        cur = ((cur * 37) % 2**64) ^ ((cur * 42424242) % 2**64)
        cur = rotl(cur, 7)
    return cur

try:
    with open("ono4", "rb") as f:
        d = f.read()
    # ono2_prev = transform_ono2(flagparts[0])
    # ono3_prev = ono2_prev ^ flagparts[1]
    d = bytes(x ^ 42 for x in d)
    with open("ono4.h", "w") as f:
        f.write(fmt_bytes(d))
except FileNotFoundError:
    pass

try:
    with open("ono3", "rb") as f:
        d = f.read()
    inv = pow(flagparts[1], -1, 2**64)
    d = bytearray(d)
    for i in range(len(d) - 9, -1, -1):
        chunk = int.from_bytes(d[i:i + 8], "little")
        chunk = (chunk * inv) % 2**64
        d[i:i + 8] = chunk.to_bytes(8, "little")
    with open("ono3.h", "w") as f:
        f.write(fmt_bytes(d))
except FileNotFoundError:
    pass

try:
    with open("ono2", "rb") as f:
        d = f.read()
    nums = [int.from_bytes(d[i : i + 8], "little") for i in range(0, len(d), 8)]
    inv = pow(1337133713371337, -1, 2**64)
    cur = flagparts[0]
    for i in range(len(nums)):
        nums[i] = ((nums[i] ^ cur) * inv) % 2**64
        cur = transform_ono2(cur)
    joined = b"".join(n.to_bytes(8, "little") for n in nums)
    with open("ono2.h", "w") as f:
        f.write(fmt_bytes(joined))
except FileNotFoundError:
    pass
