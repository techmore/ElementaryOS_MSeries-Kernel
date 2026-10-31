#!/usr/bin/env python3
"""Exercise whole J773g importer with opted-in USB data and atomic failure."""
import importlib.util
from pathlib import Path
import subprocess, sys, tempfile
repo=Path(sys.argv[1]).resolve()
spec=importlib.util.spec_from_file_location('j713',repo/'test/py/tests/test_apple_j713_fdt.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
preamble=t.HARNESS.split('static void check_references')[0]
t.HARNESS=preamble+r'''
static const char banks[]="usb2phy\0pipehandler\0core\0axi2af\0lioa\0fabric\0common-config";
static const char *props[]={"apple,tunable-usb3-axi2af","apple,tunable-usb3-lioa", "apple,tunable-usb3-fabric", "apple,tunable-usb3-config", "apple,tunable-usb3-common", "apple,tunable-usb3-efuse", "apple,tunable-lane0-usb", "apple,tunable-lane1-usb"};
static void add_phy(void *f, int fill) {
 int n=fdt_path_offset(f,"/soc");assert(n>=0);n=fdt_add_subnode(f,n,"phy");assert(n>=0);
 assert(!fdt_setprop_string(f,n,"compatible","apple,t8132-atcphy"));assert(!fdt_setprop_string(f,n,"status","disabled"));assert(!fdt_setprop(f,n,"apple,fixed-usb3",NULL,0));assert(!fdt_setprop(f,n,"reg-names",banks,sizeof(banks)));
 fdt32_t regs[28], t[]={cpu_to_fdt32(0x100),cpu_to_fdt32(0xff),cpu_to_fdt32(0x55)};
 for(int i=0;i<7;i++){regs[i*4]=cpu_to_fdt32(1);regs[i*4+1]=cpu_to_fdt32(i*0x10000);regs[i*4+2]=0;regs[i*4+3]=cpu_to_fdt32(0x4000);}
 assert(!fdt_setprop(f,n,"reg",regs,sizeof(regs)));
 if(fill) for(unsigned i=0;i<sizeof(props)/sizeof(props[0]);i++)assert(!fdt_setprop(f,n,props[i],t,sizeof(t)));
 n=fdt_path_offset(f,"/aliases");assert(!fdt_setprop_string(f,n,"atcphy2","/soc/phy"));
}
int main(int argc,char **argv) {
 assert(argc==3); void *s=load(argv[1],128*1024),*d=load(argv[2],1024*1024);
 const char compat[]="apple,j773g\0apple,t8132", names[]="nvme\0nvmmu\0ans";
 assert(!fdt_setprop(s,0,"compatible",compat,sizeof(compat)));assert(!fdt_setprop(d,0,"compatible",compat,sizeof(compat)));
 int n=fdt_path_offset(d,"/chosen");assert(!fdt_setprop_string(d,n,"u-boot,j773g-dtb-source","0123456789012345678901234567890123456789"));
 n=fdt_path_offset(d,"/chosen");assert(!fdt_setprop(d,n,"u-boot,j773g-usb3-calibration",NULL,0));
 n=fdt_path_offset(s,"/chosen");assert(!fdt_delprop(s,n,"asahi,kblang-code"));
 const char *as[]={"ans","ans-mbox","sart-ans"},*types[]={"apple,t8132-nvme-ans2","apple,asc-mailbox-v4","apple,t6000-sart"};
 for(int i=0;i<3;i++){n=fdt_path_offset(s,as[i]);assert(n>=0);assert(!fdt_setprop_string(s,n,"compatible",types[i]));n=fdt_path_offset(s,as[i]);assert(!fdt_setprop_string(s,n,"status","okay"));}
 n=fdt_path_offset(s,"ans");assert(!fdt_setprop(s,n,"reg-names",names,sizeof(names)));n=fdt_path_offset(d,"ans");assert(!fdt_setprop(d,n,"reg-names",names,sizeof(names)));
 n=fdt_path_offset(s,"/reserved-memory/asc-firmware@900000000");if(n>=0)assert(!fdt_del_node(s,n));n=fdt_path_offset(s,"/reserved-memory/flash@900080000");if(n>=0)assert(!fdt_del_node(s,n));
 add_phy(s,1);add_phy(d,0);n=fdt_path_offset(s,"/soc/phy");assert(!fdt_delprop(s,n,props[7]));
 size_t cap=fdt_totalsize(d);void *before=malloc(cap);assert(before);memcpy(before,d,cap);
 assert(apple_j773_import_fdt(d,s)<0);assert(!memcmp(before,d,cap));free(before);
 n=fdt_path_offset(s,"/soc/phy");fdt32_t triple[]={cpu_to_fdt32(0x100),cpu_to_fdt32(0xff),cpu_to_fdt32(0x55)};assert(!fdt_setprop(s,n,props[7],triple,sizeof(triple)));
 assert(apple_j773_import_fdt(d,s)==1);n=fdt_path_offset(d,"/soc/phy");int len;for(unsigned i=0;i<sizeof(props)/sizeof(props[0]);i++)assert(fdt_getprop(d,n,props[i],&len) && len==12);
 assert(!strcmp(fdt_getprop(d,n,"status",&len),"disabled"));puts("complete mini import: failure atomic, complete bundle copied, PHY disabled");free(s);free(d);
}
'''
with tempfile.TemporaryDirectory() as d:
 q=Path(d);binary=t.build_importer(q);source=t.compile_tree(q,'source',t.fixture_tree(True,graphics=False));target=t.compile_tree(q,'target',t.fixture_tree(False,graphics=False));subprocess.run([str(binary),str(source),str(target)],check=True)
