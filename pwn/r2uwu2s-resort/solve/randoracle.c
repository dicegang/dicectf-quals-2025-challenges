#include <stdio.h>
#include <stdlib.h>

int main() {
  while (1) {
    if (rand() % 4 != 3) {
      printf("%d\n", rand() % 255);
    } else {
      printf("-1\n");
    }
  }
}
