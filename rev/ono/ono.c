#define _GNU_SOURCE

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include "ono2.h"

int main(void) {
    printf("oño? ");
    fflush(stdout);
    char inp[64];
    fgets(inp, sizeof(inp), stdin);
    size_t len = strcspn(inp, "\n");
    inp[len] = '\0';
    if (len != 32) {
        puts("oño.");
        return 1;
    }
    unsigned long long* ptr = (unsigned long long*) inp;
    unsigned long long n0 = ptr[0];
    char n1[21];
    char n2[21];
    char n3[21];
    char env[26];
    char* const argv[] = {n1, n2, n3, NULL};
    char* const envp[] = {env, NULL};
    for (int i = 0; i < 3; i ++) {
        snprintf(argv[i], 21, "%llu", ptr[i + 1]);
    }
    int fd = memfd_create("oño", 0);
    ptr = (unsigned long long*) data;
    for (int i = 0; i < sizeof(data) / sizeof(*ptr); i ++) {
        ptr[i] = (ptr[i] * 1337133713371337ULL) ^ n0;
        for (int j = 0; j < 32; j ++) {
            n0 = (n0 * 37) ^ (n0 * 42424242);
            n0 = (n0 << 7) | (n0 >> 57);
        }
        if (i == 0) {
            snprintf(env, 26, "oño=%llu", n0);
        }
    }
    write(fd, data, sizeof(data));
    fexecve(fd, argv, envp);
    puts("oño.");
    return 1;
}
