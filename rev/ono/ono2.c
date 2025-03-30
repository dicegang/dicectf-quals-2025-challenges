#define _GNU_SOURCE

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include "ono3.h"

int main(int argc, char* argv[], char* envp[]) {
    unsigned long long n, orig;
    sscanf(argv[0], "%llu", &n);
    orig = n;
    char* cptr = envp[0] + 5;
    while (*cptr) {
        if (*cptr % 2) {
            n = (n << 19) | (n >> 45);
        } else {
            n *= 1337;
        }
        cptr ++;
    }
    if (n != 17705312960230358457ULL) {
        puts("oño.");
        return 1;
    }
    int fd = memfd_create("oño", 0);
    unsigned long long* ptr;
    for (int i = 0; i < sizeof(data) - sizeof(*ptr); i ++) {
        ptr = (unsigned long long*)(data + i);
        *ptr *= orig;
    }
    write(fd, data, sizeof(data));
    char env[26];
    char* const newenv[] = {env, NULL};
    unsigned long long prev;
    sscanf(envp[0] + 5, "%llu", &prev);
    prev ^= orig;
    snprintf(env, 26, "oño=%llu", prev);
    fexecve(fd, argv + 1, newenv);
    puts("oño.");
    return 1;
}
