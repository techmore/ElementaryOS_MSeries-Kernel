#!/usr/bin/env python3
"""Exercise m1n1-to-U-Boot MAC data transfer with synthetic firmware input."""
import ast
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

m1n1, uboot = map(Path, sys.argv[1:3])
spec = importlib.util.spec_from_file_location('j713', uboot / 'test/py/tests/test_apple_j713_fdt.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
preamble = t.HARNESS.split('static void check_references')[0]
source = (m1n1 / 'src/kboot.c').read_text()
start = source.index('static struct {\n    const char *alias;\n    const char *fdt_property;')
end = source.index('\nstatic ', source.index('static int dt_set_mac_addresses(void)', start) + 1)
production = source[start:end]
stubs = r'''
static void *adt, *dt;
static int chip_id;
#define T8140 8140
#define bail(...) return -1
static int adt_path_offset(void *a,const char *p) { (void)a; return strcmp(p,"/chosen") ? -1 : 1; }
static int fake_prop(const char *name, uint8_t *out) {
 static const uint8_t addr[6]={2,1,2,3,4,5};
 if(strcmp(name,"mac-address-ethernet0")) return -1;
 memcpy(out,addr,6); return 6;
}
#define ADT_GETPROP_ARRAY(a,n,p,v) ((void)(a),(void)(n),fake_prop((p),(v)))
'''
fixture = Path(__file__).with_name('verify-uboot-mini-ethernet-mac.py').read_text()
assignments = [n for n in ast.parse(fixture).body if isinstance(n, ast.Assign) and isinstance(n.value, ast.BinOp) and isinstance(n.value.right, ast.Constant) and isinstance(n.value.right.value, str)]
assert len(assignments) == 2
main = assignments[1].value.right.value
old = 'sn=fdt_path_offset(s,"/soc/pcie@1cb0000000/pci@2,0/ethernet@0,0"); assert(!fdt_setprop(s,sn,"local-mac-address",good,6));'
new = r'''int a=fdt_path_offset(s,"/aliases"); assert(a>=0); assert(!fdt_setprop_string(s,a,"ethernet0","/soc/pcie@1cb0000000/pci@2,0/ethernet@0,0"));
 dt=s; assert(!dt_set_mac_addresses());'''
assert old in main
main = main.replace(old, new, 1)
t.HARNESS = preamble + stubs + production + main
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)
    binary=t.build_importer(p)
    source=t.compile_tree(p,'source',t.fixture_tree(True,graphics=False))
    target=t.compile_tree(p,'target',t.fixture_tree(False,graphics=False))
    subprocess.run([str(binary),str(source),str(target)],check=True)
