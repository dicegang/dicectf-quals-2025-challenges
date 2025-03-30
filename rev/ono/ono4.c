#include <stdio.h>

#define BIT(n, i) (((n) >> (i)) & 1)

unsigned char grid[] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 7, 0, 0, 3, 0, 0, 4, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0};
int offs[4][2] = {
    {1, 0},
    {-1, 0},
    {0, 1},
    {0, -1}
};

int ff(unsigned long long solve, int i, unsigned long long* seen) {
    *seen |= 1ULL << i;
    int r = i / 8;
    int c = i % 8;
    int ret = 1;
    for (int o = 0; o < 4; o ++) {
        int nr = r + offs[o][0];
        int nc = c + offs[o][1];
        int j = nr * 8 + nc;
        if (nr >= 0 && nr < 8 && nc >= 0 && nc < 8 && !BIT(*seen, j) && BIT(solve, j) == BIT(solve, i)) {
            ret += ff(solve, j, seen);
        }
    }
    return ret;
}

int main(int argc, char* argv[], char* envp[]) {
    unsigned long long prev;
    sscanf(envp[0] + 5, "%llu", &prev);
    unsigned long long solve;
    sscanf(argv[0], "%llu", &solve);
    solve ^= prev;
    int blackInd = 0;
    int blackCount = 0;
    for (int i = 0; i < 64; i ++) {
        if (!BIT(solve, i)) {
            blackInd = i;
            blackCount ++;
        }
    }
    unsigned long long seen = 0;
    if (blackCount > 0 && ff(solve, blackInd, &seen) != blackCount) {
        puts("oño.");
        return 1;
    }
    for (int i = 0; i < 64; i ++) {
        seen = 0;
        if (grid[i] && (!BIT(solve, i) || ff(solve, i, &seen) != grid[i])) {
            puts("oño.");
            return 1;
        }
    }
    puts("You've diced the oño and found the flag!");
    return 0;
}
