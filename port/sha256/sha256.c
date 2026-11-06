/* SHA256: the SHA-256 of a file, for AmigaOS 3 (68020 and up).
 *
 *   SHA256 FILE,EXPECT/K,CHECK/K,QUIET/S
 *
 * FILE alone prints "<hash>  <file>", as sha256sum does.
 * FILE EXPECT=<hash> prints "<file>: OK" or "<file>: FAILED" and returns 0 or
 * 10 (ERROR), so an Installer script or a Shell script can act on it.
 * CHECK=<list> reads a sha256sum list ("<hash>  <name>" per line); each name
 * is taken from the list's own drawer. 10 if any file differs.
 * Ctrl-C stops it (20). A file that cannot be read gives 20.
 *
 * SHA-256 written from FIPS 180-4. Uses dos.library only.
 * MIT licence. Copyright (c) 2026 AmiCradle Team.
 */
#include <exec/types.h>
#include <exec/memory.h>
#include <dos/dos.h>
#include <proto/exec.h>
#include <proto/dos.h>

static const char version[] __attribute__((used)) = "$VER: SHA256 1.0 (6.11.2026)";

#define BUFSIZE 65536

typedef struct {
    ULONG h[8];
    ULONG lo, hi;           /* message length in bytes */
    UBYTE block[64];
    ULONG fill;
} Sha;

static const ULONG K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

#define ROR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

static void sha_block(Sha *s, const UBYTE *p)
{
    ULONG w[64], a, b, c, d, e, f, g, h, t1, t2;
    int i;
    for (i = 0; i < 16; i++, p += 4)
        w[i] = ((ULONG)p[0] << 24) | ((ULONG)p[1] << 16) | ((ULONG)p[2] << 8) | p[3];
    for (; i < 64; i++) {
        ULONG s0 = ROR(w[i - 15], 7) ^ ROR(w[i - 15], 18) ^ (w[i - 15] >> 3);
        ULONG s1 = ROR(w[i - 2], 17) ^ ROR(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    a = s->h[0]; b = s->h[1]; c = s->h[2]; d = s->h[3];
    e = s->h[4]; f = s->h[5]; g = s->h[6]; h = s->h[7];
    for (i = 0; i < 64; i++) {
        t1 = h + (ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i];
        t2 = (ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)) + ((a & b) ^ (a & c) ^ (b & c));
        h = g; g = f; f = e; e = d + t1;
        d = c; c = b; b = a; a = t1 + t2;
    }
    s->h[0] += a; s->h[1] += b; s->h[2] += c; s->h[3] += d;
    s->h[4] += e; s->h[5] += f; s->h[6] += g; s->h[7] += h;
}

static void sha_init(Sha *s)
{
    static const ULONG iv[8] = {
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    };
    int i;
    for (i = 0; i < 8; i++)
        s->h[i] = iv[i];
    s->lo = s->hi = 0;
    s->fill = 0;
}

static void sha_update(Sha *s, const UBYTE *p, ULONG n)
{
    ULONG old = s->lo;
    s->lo += n;
    if (s->lo < old)
        s->hi++;
    if (s->fill) {
        while (n && s->fill < 64) {
            s->block[s->fill++] = *p++;
            n--;
        }
        if (s->fill < 64)
            return;
        sha_block(s, s->block);
        s->fill = 0;
    }
    while (n >= 64) {
        sha_block(s, p);
        p += 64;
        n -= 64;
    }
    while (n--)
        s->block[s->fill++] = *p++;
}

static void sha_final(Sha *s, char *hex)
{
    static const char digits[] = "0123456789abcdef";
    ULONG bits_hi = (s->hi << 3) | (s->lo >> 29), bits_lo = s->lo << 3;
    int i;
    s->block[s->fill++] = 0x80;
    if (s->fill > 56) {
        while (s->fill < 64)
            s->block[s->fill++] = 0;
        sha_block(s, s->block);
        s->fill = 0;
    }
    while (s->fill < 56)
        s->block[s->fill++] = 0;
    for (i = 0; i < 4; i++) {
        s->block[56 + i] = (UBYTE)(bits_hi >> (24 - 8 * i));
        s->block[60 + i] = (UBYTE)(bits_lo >> (24 - 8 * i));
    }
    sha_block(s, s->block);
    for (i = 0; i < 32; i++) {
        UBYTE v = (UBYTE)(s->h[i >> 2] >> (24 - 8 * (i & 3)));
        hex[2 * i] = digits[v >> 4];
        hex[2 * i + 1] = digits[v & 15];
    }
    hex[64] = 0;
}

static UBYTE *buffer;

/* 0: done, 1: cannot read, 2: break */
static int hash_file(CONST_STRPTR name, char *hex)
{
    Sha s;
    LONG n;
    BPTR fh = Open(name, MODE_OLDFILE);
    if (!fh)
        return 1;
    sha_init(&s);
    for (;;) {
        if (SetSignal(0, SIGBREAKF_CTRL_C) & SIGBREAKF_CTRL_C) {
            Close(fh);
            return 2;
        }
        n = Read(fh, buffer, BUFSIZE);
        if (n < 0) {
            Close(fh);
            return 1;
        }
        if (n == 0)
            break;
        sha_update(&s, buffer, (ULONG)n);
    }
    Close(fh);
    sha_final(&s, hex);
    return 0;
}

/* a: our lowercase hash; b: the expected one, any case, ended by a blank */
static int same_hash(const char *a, const char *b)
{
    int i;
    for (i = 0; i < 64; i++) {
        char y = b[i];
        if (y >= 'A' && y <= 'F')
            y += 32;
        if (a[i] != y)
            return 0;
    }
    return b[64] == 0 || b[64] == ' ' || b[64] == '\t' || b[64] == '\n' || b[64] == '\r';
}

static int broken;

/* one file against an expected hash: RETURN_OK, RETURN_ERROR or RETURN_FAIL */
static LONG check_one(CONST_STRPTR name, CONST_STRPTR shown, const char *want, BOOL quiet)
{
    char hex[65];
    int r = hash_file(name, hex);
    if (r == 2) {
        PutStr("***Break\n");
        broken = 1;
        return RETURN_FAIL;
    }
    if (r == 1) {
        Printf("%s: cannot be read\n", (LONG)shown);
        return RETURN_FAIL;
    }
    if (same_hash(hex, want)) {
        if (!quiet)
            Printf("%s: OK\n", (LONG)shown);
        return RETURN_OK;
    }
    Printf("%s: FAILED (its SHA-256 is %s)\n", (LONG)shown, (LONG)hex);
    return RETURN_ERROR;
}

static LONG check_list(CONST_STRPTR list, BOOL quiet)
{
    static char line[1024], path[1024];
    LONG rc = RETURN_OK, base_len;
    BPTR fh = Open(list, MODE_OLDFILE);
    if (!fh) {
        Printf("%s: cannot be read\n", (LONG)list);
        return RETURN_FAIL;
    }
    base_len = (LONG)(PathPart(list) - list);
    if (base_len < 0 || base_len >= (LONG)sizeof(path) - 2)
        base_len = 0;
    while (!broken && FGets(fh, line, sizeof(line) - 1)) {
        char *name, *end;
        LONG r, len = 0;
        while (line[len])
            len++;
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r' || len == 0)
            continue;
        if (len < 66) {
            Printf("%s: a line is not \"<SHA-256>  <name>\"\n", (LONG)list);
            rc = RETURN_FAIL;
            continue;
        }
        name = line + 64;
        while (*name == ' ' || *name == '\t' || *name == '*')
            name++;
        for (end = name; *end && *end != '\n' && *end != '\r'; end++)
            ;
        *end = 0;
        CopyMem((APTR)list, path, base_len);
        path[base_len] = 0;
        if (!*name || !AddPart(path, name, sizeof(path))) {
            Printf("%s: a line has no usable file name\n", (LONG)list);
            rc = RETURN_FAIL;
            continue;
        }
        r = check_one((CONST_STRPTR)path, (CONST_STRPTR)name, line, quiet);
        if (r > rc)
            rc = r;
    }
    Close(fh);
    return rc;
}

int main(void)
{
    enum { A_FILE, A_EXPECT, A_CHECK, A_QUIET, A_N };
    LONG args[A_N] = { 0 };
    LONG rc;
    struct RDArgs *rd = ReadArgs("FILE,EXPECT/K,CHECK/K,QUIET/S", args, NULL);
    if (!rd) {
        PrintFault(IoErr(), "SHA256");
        return RETURN_FAIL;
    }
    if (!args[A_FILE] == !args[A_CHECK]) {
        PutStr("SHA256: give a FILE, or a list with CHECK=\n");
        FreeArgs(rd);
        return RETURN_FAIL;
    }
    buffer = AllocMem(BUFSIZE, MEMF_ANY);
    if (!buffer) {
        PutStr("SHA256: not enough memory\n");
        FreeArgs(rd);
        return RETURN_FAIL;
    }
    if (args[A_CHECK]) {
        rc = check_list((CONST_STRPTR)args[A_CHECK], args[A_QUIET] != 0);
    } else if (args[A_EXPECT]) {
        rc = check_one((CONST_STRPTR)args[A_FILE], (CONST_STRPTR)args[A_FILE],
                       (const char *)args[A_EXPECT], args[A_QUIET] != 0);
    } else {
        char hex[65];
        int r = hash_file((CONST_STRPTR)args[A_FILE], hex);
        if (r == 0) {
            Printf("%s  %s\n", (LONG)hex, args[A_FILE]);
            rc = RETURN_OK;
        } else {
            if (r == 2)
                PutStr("***Break\n");
            else
                Printf("%s: cannot be read\n", args[A_FILE]);
            rc = RETURN_FAIL;
        }
    }
    FreeMem(buffer, BUFSIZE);
    FreeArgs(rd);
    return (int)rc;
}
