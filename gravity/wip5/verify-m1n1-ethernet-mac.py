#!/usr/bin/env python3
"""Exercise m1n1's actual MAC-transfer function with synthetic ADT/FDT data."""
from pathlib import Path
import subprocess
import sys
import tempfile

m1n1, uboot = map(Path, sys.argv[1:3])
s = (m1n1 / 'src/kboot.c').read_text()
start = s.index('static struct {\n    const char *alias;\n    const char *fdt_property;')
end = s.index('\nstatic ', s.index('static int dt_set_mac_addresses(void)', start) + 1)
production = s[start:end]
program = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <libfdt.h>
static void *adt, *dt;
static int chip_id, has_mac=1;
#define T8140 8140
#define bail(...) return -1
static int adt_path_offset(void *a, const char *p) { (void)a; return strcmp(p,"/chosen") ? -1 : 1; }
static int fake_prop(const char *name, uint8_t *out) {
 static const uint8_t mac[6]={2,1,2,3,4,5};
 if (!has_mac || strcmp(name,"mac-address-ethernet0")) return -1;
 memcpy(out,mac,6); return 6;
}
#define ADT_GETPROP_ARRAY(a,n,p,v) ((void)(a),(void)(n),fake_prop((p),(v)))
''' + production + r'''
int main(void) {
 unsigned char buffer[8192], good[6]={2,1,2,3,4,5}; int len;
 assert(!fdt_create_empty_tree(buffer,sizeof(buffer))); dt=buffer;
 int n=fdt_add_subnode(dt,0,"ethernet"); assert(n>=0);
 assert(!fdt_setprop_string(dt,n,"status","disabled"));
 int aliases=fdt_add_subnode(dt,0,"aliases"); assert(aliases>=0);
 assert(!fdt_setprop_string(dt,aliases,"ethernet0","/ethernet"));
 assert(!dt_set_mac_addresses()); n=fdt_path_offset(dt,"/ethernet");
 const void *m=fdt_getprop(dt,n,"local-mac-address",&len); assert(m && len==6 && !memcmp(m,good,6));
 assert(!strcmp(fdt_getprop(dt,n,"status",NULL),"disabled"));
 assert(!fdt_delprop(dt,n,"local-mac-address")); has_mac=0; assert(!dt_set_mac_addresses());
 n=fdt_path_offset(dt,"/ethernet"); assert(!fdt_getprop(dt,n,"local-mac-address",NULL));
 has_mac=1; aliases=fdt_path_offset(dt,"/aliases"); assert(!fdt_delprop(dt,aliases,"ethernet0"));
 assert(!dt_set_mac_addresses()); n=fdt_path_offset(dt,"/ethernet"); assert(!fdt_getprop(dt,n,"local-mac-address",NULL));
 puts("m1n1 MAC transfer and missing ADT/alias cases passed");
}
'''
lib = uboot / 'scripts/dtc/libfdt'
names = ('fdt', 'fdt_ro', 'fdt_rw', 'fdt_sw', 'fdt_wip', 'fdt_empty_tree', 'fdt_strerror', 'fdt_addresses')
with tempfile.TemporaryDirectory() as tmp:
    c, exe = Path(tmp) / 'test.c', Path(tmp) / 'test'
    c.write_text(program)
    subprocess.run(['cc', '-D_GNU_SOURCE', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-I', str(lib), str(c), *[str(lib / (n + '.c')) for n in names], '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
