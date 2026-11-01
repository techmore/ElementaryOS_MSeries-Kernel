#!/usr/bin/env python3
"""Check simultaneous J773g GPU, USB3 and Ethernet imports atomically."""
import importlib.util
from pathlib import Path
import subprocess, sys, tempfile
repo=Path(sys.argv[1]).resolve()
spec=importlib.util.spec_from_file_location('j713',repo/'test/py/tests/test_apple_j713_fdt.py')
t=importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
preamble=t.HARNESS.split('static void check_references')[0]
GPU = r'''
static void init(void *fdt, int src, int fault) {
 const char *names[] = {"uat-ttbs","uat-pagetables","uat-handoff","uat-shared-l2","gpu-fw-text","gpu-fw-data"};
 const char name_list[]="ttbs\0pagetables\0handoff\0shared-l2\0fw-text\0fw-data";
 fdt32_t refs[6], flags[2]={cpu_to_fdt32(1),0};
 fdt64_t vas[2]; fdt64_st(&vas[0],0xfffffc0000000000ULL); fdt64_st(&vas[1],0xfffffc0000060000ULL);
 int soc=fdt_path_offset(fdt,"/soc"); assert(soc>=0); int g=fdt_add_subnode(fdt,soc,"gpu"); assert(g>=0);
 assert(!fdt_setprop_string(fdt,g,"compatible","apple,agx-t8132"));
 g=fdt_path_offset(fdt,"/soc/gpu"); assert(!fdt_setprop_string(fdt,g,"status",((fault==4&&!src)||(fault==5&&src))?"okay":"disabled"));
 g=fdt_path_offset(fdt,"/soc/gpu"); if(src||fault!=1)assert(!fdt_setprop_empty(fdt,g,"apple,j773g-gpu-handoff-draft"));
 int aliases=fdt_path_offset(fdt,"/aliases"); assert(!fdt_setprop_string(fdt,aliases,"gpu","/soc/gpu"));
 for(int i=0;i<6;i++){
  int reserved=fdt_path_offset(fdt,"/reserved-memory");int n=fdt_add_subnode(fdt,reserved,names[i]); assert(n>=0);
  u64 base=0x800000000ULL+(u64)i*0x200000; u64 size=i==4?0x60000:i==5?0x13c000:0x4000;
  if(fault==3&&i==1)base=0x800000000ULL;
  if(fault==8&&!src&&i==1)base+=0x4000;
  fdt64_t reg[2]; fdt64_st(&reg[0],base);fdt64_st(&reg[1],size);
  assert(!fdt_setprop(fdt,n,"reg",reg,sizeof(reg)));
  assert(!fdt_add_mem_rsv(fdt,base,size)); reserved=fdt_path_offset(fdt,"/reserved-memory");n=fdt_subnode_offset(fdt,reserved,names[i]);assert(!fdt_setprop_empty(fdt,n,"no-map"));
  reserved=fdt_path_offset(fdt,"/reserved-memory");n=fdt_subnode_offset(fdt,reserved,names[i]);assert(!fdt_setprop_string(fdt,n,"status","okay"));
  reserved=fdt_path_offset(fdt,"/reserved-memory");n=fdt_subnode_offset(fdt,reserved,names[i]);u32 phandle=(src?600:700)+i;assert(!fdt_setprop_u32(fdt,n,"phandle",phandle));refs[i]=cpu_to_fdt32(phandle);
 }
 g=fdt_path_offset(fdt,"/soc/gpu"); if(fault==7&&src) refs[0]=cpu_to_fdt32(9999);assert(!fdt_setprop(fdt,g,"memory-region",refs,sizeof(refs)));
 g=fdt_path_offset(fdt,"/soc/gpu");assert(!fdt_setprop(fdt,g,"memory-region-names",name_list,sizeof(name_list)));
 if(src){g=fdt_path_offset(fdt,"/soc/gpu");assert(!fdt_setprop_u32(fdt,g,"apple,g16-handoff-version",fault==2?2:1));
  g=fdt_path_offset(fdt,"/soc/gpu");if(fault==6)fdt64_st(&vas[1],0);assert(!fdt_setprop(fdt,g,"apple,firmware-segment-vas",vas,sizeof(vas)));
  g=fdt_path_offset(fdt,"/soc/gpu");assert(!fdt_setprop(fdt,g,"apple,firmware-segment-flags",flags,sizeof(flags)));}
}
'''

USB = r'''
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
'''

MAC = r'''
static int endpoint(void *f) {
 int n=fdt_path_offset(f,"/soc"); assert(n>=0);
 n=fdt_path_offset(f,"/soc/pcie@1cb0000000"); assert(n>=0);
 n=fdt_add_subnode(f,n,"pci@2,0"); assert(n>=0);
 fdt32_t portreg[]={cpu_to_fdt32(0x1000),0,0,0,0};
 assert(!fdt_setprop(f,n,"reg",portreg,sizeof(portreg)));
 assert(!fdt_setprop_string(f,n,"compatible","pciclass,0604"));
 n=fdt_add_subnode(f,n,"ethernet@0,0"); assert(n>=0);
 fdt32_t reg[]={cpu_to_fdt32(0x20000),0,0,0,0};
 assert(!fdt_setprop(f,n,"reg",reg,sizeof(reg)));
 assert(!fdt_setprop_string(f,n,"status","disabled")); return n;
}
'''

MAIN = r'''
int main(int argc,char **argv) {
 assert(argc==3); for(int fault=0;fault<4;fault++) {
 void *s=load(argv[1],128*1024),*d=load(argv[2],1024*1024);init(s,1,fault==1?3:0);init(d,0,0);
 const char compat[]="apple,j773g\0apple,t8132",names[]="nvme\0nvmmu\0ans";
 assert(!fdt_setprop(s,0,"compatible",compat,sizeof(compat)));assert(!fdt_setprop(d,0,"compatible",compat,sizeof(compat)));
 int n=fdt_path_offset(d,"/chosen");assert(!fdt_setprop_string(d,n,"u-boot,j773g-dtb-source","0123456789012345678901234567890123456789"));
 n=fdt_path_offset(d,"/chosen");assert(!fdt_setprop(d,n,"u-boot,j773g-usb3-calibration",NULL,0));
 n=fdt_path_offset(d,"/chosen");assert(!fdt_setprop(d,n,"u-boot,j773g-ethernet-mac",NULL,0));
 const char *as[]={"ans","ans-mbox","sart-ans"},*types[]={"apple,t8132-nvme-ans2","apple,asc-mailbox-v4","apple,t6000-sart"};
 for(int i=0;i<3;i++){n=fdt_path_offset(s,as[i]);assert(n>=0);assert(!fdt_setprop_string(s,n,"compatible",types[i]));n=fdt_path_offset(s,as[i]);assert(!fdt_setprop_string(s,n,"status","okay"));}
 n=fdt_path_offset(s,"ans");assert(!fdt_setprop(s,n,"reg-names",names,sizeof(names)));n=fdt_path_offset(d,"ans");assert(!fdt_setprop(d,n,"reg-names",names,sizeof(names)));
 n=fdt_path_offset(s,"/reserved-memory/asc-firmware@900000000");if(n>=0)assert(!fdt_del_node(s,n));n=fdt_path_offset(s,"/reserved-memory/flash@900080000");if(n>=0)assert(!fdt_del_node(s,n));
 add_phy(s,1);add_phy(d,0);n=endpoint(s);endpoint(d);unsigned char mac[]={2,1,2,3,4,5};if(fault==3)mac[0]=1;assert(!fdt_setprop(s,n,"local-mac-address",mac,6));
 if(fault==2){n=fdt_path_offset(s,"/soc/phy");assert(!fdt_delprop(s,n,props[7]));}
 while(fdt_num_mem_rsv(d)>0){assert(!fdt_del_mem_rsv(d,0));}size_t cap=fdt_totalsize(d);void *before=malloc(cap);assert(before);memcpy(before,d,cap);
 int ret=apple_j773_import_fdt(d,s);
 if(fault){assert(ret<0);assert(!memcmp(before,d,cap));}else {
  assert(ret==1);int len; n=fdt_path_offset(d,"/soc/gpu");assert(fdt_getprop(d,n,"apple,g16-handoff-version",&len) && len==4);assert(!strcmp(fdt_getprop(d,n,"status",NULL),"disabled"));
  n=fdt_path_offset(d,"/soc/phy");assert(fdt_getprop(d,n,props[7],&len) && len==12);assert(!strcmp(fdt_getprop(d,n,"status",NULL),"disabled"));
  n=fdt_path_offset(d,"/soc/pcie@1cb0000000/pci@2,0/ethernet@0,0");const void *v=fdt_getprop(d,n,"local-mac-address",&len);assert(v && len==6 && !memcmp(v,mac,6));assert(!strcmp(fdt_getprop(d,n,"status",NULL),"disabled"));
 }
 free(before);free(s);free(d);
 } puts("combined GPU, USB3, MAC success and atomic rejection cases passed");return 0;
}
'''

t.HARNESS=preamble+GPU+USB+MAC+MAIN
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp); b=t.build_importer(p); s=t.compile_tree(p,'source',t.fixture_tree(True,graphics=False)); d=t.compile_tree(p,'target',t.fixture_tree(False,graphics=False)); subprocess.run([str(b),str(s),str(d)],check=True)
