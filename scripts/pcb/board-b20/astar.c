/* Grid A* for route.py (two layers, 8 directions, through vias). Built by route.py with the system C compiler.
 *
 * All arrays are row-major w*h windows. The free, dst and src arrays hold 0/1 bytes; each extra array is an optional
 * per-cell step cost (NULL for none). Moves: 4 orthogonal (cost 1) and 4 diagonal (cost 1.4142), a diagonal needing both orthogonal
 * neighbours passable; a layer change costs vcost where vok is set. Layer B steps are scaled by bcost. Returns the
 * node count written to out (node = layer * w * h + j * w + i, source first), 0 when no path, -1 when out is short.
 */
#include <math.h>
#include <stdint.h>
#include <stdlib.h>

typedef struct { double f, g; int n; } item;

static void push(item *h, int *len, item it) {
    int k = (*len)++;
    h[k] = it;
    while (k) {
        int p = (k - 1) / 2;
        if (h[p].f < h[k].f || (h[p].f == h[k].f && h[p].g >= h[k].g)) break;
        item t = h[p]; h[p] = h[k]; h[k] = t; k = p;
    }
}

static item pop(item *h, int *len) {
    item top = h[0];
    h[0] = h[--(*len)];
    int k = 0;
    for (;;) {
        int a = 2 * k + 1, b = a + 1, m = k;
        if (a < *len && (h[a].f < h[m].f || (h[a].f == h[m].f && h[a].g > h[m].g))) m = a;
        if (b < *len && (h[b].f < h[m].f || (h[b].f == h[m].f && h[b].g > h[m].g))) m = b;
        if (m == k) break;
        item t = h[m]; h[m] = h[k]; h[k] = t; k = m;
    }
    return top;
}

int astar(int w, int h, const uint8_t *freeF, const uint8_t *freeB, const uint8_t *vok,
          const uint8_t *srcF, const uint8_t *srcB, const uint8_t *dstF, const uint8_t *dstB,
          const float *extraF, const float *extraB, double bcost, double vcost, int *out, int cap) {
    const int N = w * h;
    const uint8_t *fr[2] = {freeF, freeB}, *dt[2] = {dstF, dstB}, *sr[2] = {srcF, srcB};
    const float *ex[2] = {extraF, extraB};
    double lc[2] = {1.0, bcost};
    int tx0 = w, tx1 = -1, ty0 = h, ty1 = -1;
    for (int l = 0; l < 2; l++)
        for (int k = 0; k < N; k++)
            if (dt[l][k]) {
                int j = k / w, i = k % w;
                if (i < tx0) tx0 = i;
                if (i > tx1) tx1 = i;
                if (j < ty0) ty0 = j;
                if (j > ty1) ty1 = j;
            }
    if (tx1 < 0) return 0;
    double *dist = malloc(sizeof(double) * 2 * N);
    int *prev = malloc(sizeof(int) * 2 * N);
    int hcap = 1 << 16, hlen = 0;
    item *heap = malloc(sizeof(item) * hcap);
    for (int k = 0; k < 2 * N; k++) { dist[k] = INFINITY; prev[k] = -1; }
#define HEUR(i, j) hypot((double)((tx0 - (i)) > 0 ? tx0 - (i) : ((i) - tx1) > 0 ? (i) - tx1 : 0), \
                         (double)((ty0 - (j)) > 0 ? ty0 - (j) : ((j) - ty1) > 0 ? (j) - ty1 : 0))
#define PUSH(it) do { if (hlen == hcap) { hcap *= 2; heap = realloc(heap, sizeof(item) * hcap); } push(heap, &hlen, it); } while (0)
    for (int l = 0; l < 2; l++)
        for (int k = 0; k < N; k++)
            if (sr[l][k]) {
                int n = l * N + k;
                dist[n] = 0.0;
                item it = {HEUR(k % w, k / w), 0.0, n};
                PUSH(it);
            }
    static const int di[8] = {-1, 1, 0, 0, -1, 1, -1, 1}, dj[8] = {0, 0, -1, 1, -1, -1, 1, 1};
    static const double dc[8] = {1, 1, 1, 1, 1.4142, 1.4142, 1.4142, 1.4142};
    int found = -1;
    while (hlen) {
        item it = pop(heap, &hlen);
        int n = it.n, l = n / N, k = n % N;
        if (it.g > dist[n]) continue;
        if (dt[l][k]) { found = n; break; }
        int j = k / w, i = k % w;
        for (int m = 0; m < 8; m++) {
            int ni = i + di[m], nj = j + dj[m];
            if (ni < 0 || nj < 0 || ni >= w || nj >= h) continue;
            int nk = nj * w + ni;
            if (!(fr[l][nk] || dt[l][nk])) continue;
            if (m >= 4) {
                int a = j * w + ni, b = nj * w + i;
                if (!((fr[l][a] || dt[l][a]) && (fr[l][b] || dt[l][b]))) continue;
            }
            double ng = it.g + dc[m] * lc[l] + (ex[l] ? ex[l][nk] : 0.0);
            int nn = l * N + nk;
            if (ng < dist[nn]) {
                dist[nn] = ng; prev[nn] = n;
                item q = {ng + HEUR(ni, nj), ng, nn};
                PUSH(q);
            }
        }
        if (vok[k]) {
            int ol = 1 - l, nn = ol * N + k;
            if (fr[ol][k] || dt[ol][k]) {
                double ng = it.g + vcost;
                if (ng < dist[nn]) {
                    dist[nn] = ng; prev[nn] = n;
                    item q = {ng + HEUR(i, j), ng, nn};
                    PUSH(q);
                }
            }
        }
    }
    int len = 0;
    if (found >= 0) {
        for (int n = found; n >= 0; n = prev[n]) len++;
        if (len > cap) len = -1;
        else {
            int k = len;
            for (int n = found; n >= 0; n = prev[n]) out[--k] = n;
        }
    }
    free(dist); free(prev); free(heap);
    return len;
}
