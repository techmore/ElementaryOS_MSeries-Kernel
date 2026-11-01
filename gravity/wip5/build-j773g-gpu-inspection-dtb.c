/* Isolated DTB opt-in preparation; does not modify a live boot tree. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libfdt.h>

int main(int argc, char **argv)
{
    if (argc != 4 || (strcmp(argv[3], "source") && strcmp(argv[3], "target")))
        return 2;
    FILE *in = fopen(argv[1], "rb"), *out;
    if (!in || fseek(in, 0, SEEK_END)) return 1;
    long n = ftell(in);
    if (n <= 0 || n > 2 * 1024 * 1024 || fseek(in, 0, SEEK_SET)) return 1;
    void *original = malloc(n), *tree = malloc(n + 8192);
    if (!original || !tree || fread(original, 1, n, in) != (size_t)n) return 1;
    fclose(in);
    if (fdt_check_full(original, n) || fdt_totalsize(original) != n ||
        fdt_node_check_compatible(original, 0, "apple,j773g") ||
        fdt_node_check_compatible(original, 0, "apple,t8132") ||
        fdt_open_into(original, tree, n + 8192)) return 1;
    int aliases = fdt_path_offset(tree, "/aliases"), len;
    const char *path = aliases < 0 ? NULL : fdt_getprop(tree, aliases, "gpu", &len);
    if (!path || len < 2 || path[len - 1] || strlen(path) + 1 != (size_t)len) return 1;
    int gpu = fdt_path_offset(tree, path);
    if (gpu < 0 || fdt_node_check_compatible(tree, gpu, "apple,agx-t8132")) return 1;
    const char *status = fdt_getprop(tree, gpu, "status", &len);
    if (!status || len != sizeof("disabled") || memcmp(status, "disabled", len)) return 1;
    const char *forbidden[] = {"apple,j773g-gpu-handoff-draft", "apple,j773g-gpu-diagnostic-draft",
        "apple,g16-handoff-version", "apple,firmware-segment-vas", "apple,firmware-segment-flags"};
    for (size_t i = 0; i < sizeof(forbidden) / sizeof(forbidden[0]); i++)
        if (fdt_getprop(tree, gpu, forbidden[i], &len)) return 1;
    const char *marker = strcmp(argv[3], "source") ? "apple,j773g-gpu-diagnostic-draft" :
                                                      "apple,j773g-gpu-handoff-draft";
    if (fdt_setprop_empty(tree, gpu, marker) || fdt_pack(tree)) return 1;
    /* Refuse to overwrite a previous artifact. */
    out = fopen(argv[2], "wx");
    if (!out || fwrite(tree, 1, fdt_totalsize(tree), out) != fdt_totalsize(tree) || fclose(out)) return 1;
    free(tree); free(original);
    return 0;
}
