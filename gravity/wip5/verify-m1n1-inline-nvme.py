from pathlib import Path
import subprocess, tempfile, sys
s=(Path(sys.argv[1]) / 'src/payload.c').read_text()
gate=s[s.index('        bool j773g_ans ='):s.index('        cpufreq_init();')]
tail=s[s.index('        if (kboot_boot(kernel))'):s.index('    } else if (kernel && !fdt)')]
program=r'''
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#define T8132 1
int chip_id, target, compat, alias, init_ok, live, boot_fail, init_calls, shutdown_calls, cleared, next_stage;
char *expect_compatible, *boot_spec; void *fdt, *kernel;
bool nvme_keep_running_for_linux;
int fdt_node_check_compatible(void *f, int n, const char *c) { (void)f; (void)n; return strcmp(c, compat==1 ? "apple,j773g" : compat==2 ? "apple,j713" : "other"); }
void *fdt_get_alias(void *f, const char *n) { (void)f; (void)n; return alias ? (void*)1 : NULL; }
bool nvme_init(void) { init_calls++; return init_ok; }
bool nvme_has_live_post_m4_session(void) { return live; }
int kboot_boot(void *k) { (void)k; return boot_fail; }
void kboot_set_initrd(void *p, int n) { (void)p; (void)n; cleared++; }
void nvme_shutdown(void) { shutdown_calls++; }
struct { void *entry; } next_stage_obj;
#define next_stage next_stage_obj
int run(void) {
''' + gate + tail + r'''
}
void reset(void) { chip_id=T8132; expect_compatible="apple,j773g"; compat=1; alias=1; init_ok=live=1; boot_fail=init_calls=shutdown_calls=cleared=0; boot_spec=NULL; nvme_keep_running_for_linux=false; }
int main(void) {
 reset(); assert(!run() && init_calls==1 && nvme_keep_running_for_linux && !shutdown_calls);
 reset(); init_ok=0; assert(run()==-1 && init_calls==1 && shutdown_calls==1 && !nvme_keep_running_for_linux);
 reset(); boot_fail=1; assert(run()==-1 && shutdown_calls==1 && !nvme_keep_running_for_linux);
 reset(); live=0; assert(run()==-1 && shutdown_calls==1 && !nvme_keep_running_for_linux);
 reset(); alias=0; assert(!run() && !init_calls && !nvme_keep_running_for_linux);
 reset(); expect_compatible="apple,j713"; assert(!run() && !init_calls && !nvme_keep_running_for_linux);
 reset(); chip_id=2; assert(!run() && !init_calls && !nvme_keep_running_for_linux);
 reset(); compat=2; expect_compatible="apple,j713"; assert(!run() && init_calls==1 && !nvme_keep_running_for_linux);
 reset(); boot_spec="x"; assert(!run() && init_calls==1 && nvme_keep_running_for_linux);
 puts("9 payload handoff cases passed");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.c'; p.write_text(program); subprocess.run(['cc','-Wall','-Wextra','-Werror',str(p),'-o',d+'/test'],check=True); subprocess.run([d+'/test'],check=True)
