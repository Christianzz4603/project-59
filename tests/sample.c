/* Tiny freestanding test program. No libc, so the ELF only contains these functions. */
int sum_squares(int a, int b) {
    return a * a + b * b;
}

int sum_to_n_squared(int n) {
    int s = 0;
    for (int i = 1; i <= n; i++)
        s += i * i;
    return s;
}

unsigned fnv1a(const unsigned char *p, int n) {
    unsigned h = 2166136261u;
    while (n-- > 0) {
        h ^= *p++;
        h *= 16777619u;
    }
    return h;
}

int clamp_sum(int a, int b, int lo, int hi) {
    int s = a + b;
    if (s < lo) return lo;
    if (s > hi) return hi;
    return s;
}

void _start(void) {}
