#!/usr/bin/env python3
"""Exercise the patched U-Boot chosen importer with real libfdt fixtures.

Pass a U-Boot source tree with wip5/0007 and 0009 applied. No device access.
"""
import importlib.util
import pathlib
import subprocess
import sys
import tempfile

repo = pathlib.Path(sys.argv[1]).resolve()
test_file = repo / 'test/py/tests/test_apple_j713_fdt.py'
spec = importlib.util.spec_from_file_location('j713_tests', test_file)
tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tests)
# Include the real importer and its existing fixture loader; invoke the
# production helper directly so the three cases isolate keyboard policy.
preamble = tests.HARNESS.split('static void check_references')[0]
tests.HARNESS = preamble + r'''
int main(int argc, char **argv) {
 assert(argc == 3);
 void *source = load(argv[1], 128 * 1024), *target = load(argv[2], 1024 * 1024);
 int chosen = fdt_path_offset(source, "/chosen");
 assert(!fdt_delprop(source, chosen, "asahi,kblang-code"));
 assert(j713_chosen(target, source, false) != 0); /* Air still requires it */
 assert(j713_chosen(target, source, true) == 0);   /* mini permits absence */
 chosen = fdt_path_offset(source, "/chosen");
 assert(!fdt_setprop(source, chosen, "asahi,kblang-code", "bad", 3));
 assert(j713_chosen(target, source, true) != 0);   /* malformed is rejected */
 puts("Air required; mini absent accepted; mini malformed rejected");
 free(target); free(source); return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='j773g-chosen-') as tmp:
    tmp = pathlib.Path(tmp)
    binary = tests.build_importer(tmp)
    source = tests.compile_tree(tmp, 'source', tests.fixture_tree(True))
    target = tests.compile_tree(tmp, 'target', tests.fixture_tree(False))
    subprocess.run([str(binary), str(source), str(target)], check=True)

# Exercise the complete mini importer using a synthetic storage handoff.
tests.HARNESS = preamble + r'''
int main(int argc, char **argv) {
 assert(argc == 3); void *s=load(argv[1],128*1024), *d=load(argv[2],1024*1024);
 const char compat[]="apple,j773g\0apple,t8132"; const char names[]="nvme\0nvmmu\0ans";
 assert(!fdt_setprop(s,0,"compatible",compat,sizeof(compat))); assert(!fdt_setprop(d,0,"compatible",compat,sizeof(compat)));
 int node=fdt_path_offset(d,"/chosen"); assert(!fdt_setprop_string(d,node,"u-boot,j773g-dtb-source","0123456789012345678901234567890123456789"));
 node=fdt_path_offset(s,"/chosen"); assert(!fdt_delprop(s,node,"asahi,kblang-code"));
 const char *aliases[]={"ans","ans-mbox","sart-ans"}; const char *types[]={"apple,t8132-nvme-ans2","apple,asc-mailbox-v4","apple,t6000-sart"};
 for (int i=0;i<3;i++) { node=fdt_path_offset(s,aliases[i]); assert(node>=0); assert(!fdt_setprop_string(s,node,"compatible",types[i])); node=fdt_path_offset(s,aliases[i]); assert(!fdt_setprop_string(s,node,"status","okay")); }
 node=fdt_path_offset(s,"ans"); assert(!fdt_setprop(s,node,"reg-names",names,sizeof(names))); node=fdt_path_offset(d,"ans"); assert(!fdt_setprop(d,node,"reg-names",names,sizeof(names)));
 node=fdt_path_offset(s,"/reserved-memory/asc-firmware@900000000"); if(node>=0) assert(!fdt_del_node(s,node)); node=fdt_path_offset(s,"/reserved-memory/flash@900080000"); if(node>=0) assert(!fdt_del_node(s,node));
 int ret=apple_j773_import_fdt(d,s); printf("mini importer: %d\n",ret); assert(ret==1); assert(!apple_j773_complete_fdt(d)); free(s); free(d); return 0; }
'''
with tempfile.TemporaryDirectory(prefix='j773g-import-') as tmp:
    tmp = pathlib.Path(tmp)
    binary = tests.build_importer(tmp)
    source = tests.compile_tree(tmp, 'source', tests.fixture_tree(True, graphics=False))
    target = tests.compile_tree(tmp, 'target', tests.fixture_tree(False, graphics=False))
    subprocess.run([str(binary), str(source), str(target)], check=True)
