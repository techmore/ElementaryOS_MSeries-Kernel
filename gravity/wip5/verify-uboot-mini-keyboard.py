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
tests.HARNESS = tests.HARNESS.split('static void check_references')[0] + r'''
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
