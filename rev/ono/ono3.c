#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/ptrace.h>
#include <string.h>
#include "ono4.h"

unsigned long long mul = 15289878612725095770ULL;
unsigned long long add = 9093965228253084904ULL;

int main(int argc, char* argv[], char* envp[]) {
    unsigned long long prev, inp;
    sscanf(envp[0] + 5, "%llu", &prev);
    sscanf(argv[0], "%llu", &inp);
    if (inp % 1337 == 800) {
        puts("oño.");
        return 1;
    }
    inp = inp * mul + add;
    if (inp != prev) {
        puts("oño.");
        return 1;
    }
    inp = inp * mul + add;
    char env[26];
    char* const newenv[] = {env, NULL};
    snprintf(env, 26, "oño=%llu", inp);
    int fd = memfd_create("oño", 0);
    memfrob(data, sizeof(data));
    write(fd, data, sizeof(data));
    fexecve(fd, argv + 1, newenv);
    puts("oño.");
    return 1;
}
