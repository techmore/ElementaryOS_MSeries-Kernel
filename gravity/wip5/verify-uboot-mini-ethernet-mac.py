#!/usr/bin/env python3
"""Test the opt-in J773g Ethernet MAC importer using synthetic libfdt trees."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

repo = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('j713', repo / 'test/py/tests/test_apple_j713_fdt.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
t.HARNESS = t.HARNESS.split('static void check_references')[0] + r'''
static int endpoint(void *f) {
 int n=fdt_path_offset(f,"/soc"); assert(n>=0);
 n=fdt_path_offset(f,"/soc/pcie@1cb0000000"); assert(n>=0);
 n=fdt_add_subnode(f,n,"pci@2,0"); assert(n>=0);
 n=fdt_add_subnode(f,n,"ethernet@0,0"); assert(n>=0);
 fdt32_t reg[]={cpu_to_fdt32(0x20000),0,0,0,0};
 assert(!fdt_setprop(f,n,"reg",reg,sizeof(reg)));
 assert(!fdt_setprop_string(f,n,"status","disabled")); return n;
}
int main(int argc,char **argv) {
 assert(argc==3); void *s=load(argv[1],128*1024),*d=load(argv[2],1024*1024);
 int sn=endpoint(s),dn=endpoint(d),chosen=fdt_path_offset(d,"/chosen"),len;
 unsigned char good[]={2,1,2,3,4,5}, bad[]={1,1,2,3,4,5}, zero[6]={0};
 assert(!fdt_setprop(s,sn,"local-mac-address",good,6));
 assert(j773_ethernet_mac(d,s)==0); assert(!fdt_getprop(d,dn,"local-mac-address",NULL));
 assert(!fdt_setprop_u32(d,chosen,"u-boot,j773g-ethernet-mac",1));
 assert(j773_ethernet_mac(d,s)<0);
 chosen=fdt_path_offset(d,"/chosen"); assert(!fdt_delprop(d,chosen,"u-boot,j773g-ethernet-mac"));
 assert(!fdt_setprop(d,chosen,"u-boot,j773g-ethernet-mac",NULL,0));
 dn=fdt_path_offset(d,"/soc/pcie@1cb0000000/pci@2,0/ethernet@0,0");
 assert(j773_ethernet_mac(d,s)==0); const void *m=fdt_getprop(d,dn,"local-mac-address",&len);
 assert(m && len==6 && !memcmp(m,good,6));
 assert(!strcmp(fdt_getprop(d,dn,"status",NULL),"disabled"));
 assert(!fdt_setprop(s,sn,"local-mac-address",bad,6)); assert(j773_ethernet_mac(d,s)<0);
 m=fdt_getprop(d,dn,"local-mac-address",&len); assert(m && len==6 && !memcmp(m,good,6));
 assert(!fdt_setprop(s,sn,"local-mac-address",zero,6)); assert(j773_ethernet_mac(d,s)<0);
 assert(!fdt_setprop(s,sn,"local-mac-address",good,5)); assert(j773_ethernet_mac(d,s)<0);
 assert(!fdt_setprop(s,sn,"local-mac-address",good,6));
 fdt32_t wrong[]={cpu_to_fdt32(0x30000),0,0,0,0}; assert(!fdt_setprop(s,sn,"reg",wrong,sizeof(wrong))); assert(j773_ethernet_mac(d,s)<0);
 assert(!fdt_setprop_string(d,dn,"status","okay")); assert(j773_ethernet_mac(d,s)<0);
 puts("MAC opt-in, copy, disabled state and malformed input cases passed"); free(s); free(d);
}
'''
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp)
    binary = t.build_importer(p)
    source = t.compile_tree(p, 'source', t.fixture_tree(True, graphics=False))
    target = t.compile_tree(p, 'target', t.fixture_tree(False, graphics=False))
    subprocess.run([str(binary), str(source), str(target)], check=True)

# Exercise failure atomicity through the complete production importer.
preamble = t.HARNESS.split('static int endpoint')[0]
t.HARNESS = preamble + r'''
static int endpoint(void *f) {
 int n=fdt_path_offset(f,"/soc/pcie@1cb0000000"); assert(n>=0);
 n=fdt_add_subnode(f,n,"pci@2,0"); assert(n>=0);
 n=fdt_add_subnode(f,n,"ethernet@0,0"); assert(n>=0);
 fdt32_t reg[]={cpu_to_fdt32(0x20000),0,0,0,0};
 assert(!fdt_setprop(f,n,"reg",reg,sizeof(reg)));
 assert(!fdt_setprop_string(f,n,"status","disabled")); return n;
}
int main(int argc,char **argv) {
 assert(argc==3); void *s=load(argv[1],128*1024),*d=load(argv[2],1024*1024);
 const char compat[]="apple,j773g\0apple,t8132", names[]="nvme\0nvmmu\0ans";
 assert(!fdt_setprop(s,0,"compatible",compat,sizeof(compat)));assert(!fdt_setprop(d,0,"compatible",compat,sizeof(compat)));
 int n=fdt_path_offset(d,"/chosen"); assert(!fdt_setprop_string(d,n,"u-boot,j773g-dtb-source","0123456789012345678901234567890123456789"));
 assert(!fdt_setprop(d,n,"u-boot,j773g-ethernet-mac",NULL,0));
 n=fdt_path_offset(s,"/chosen"); assert(!fdt_delprop(s,n,"asahi,kblang-code"));
 const char *as[]={"ans","ans-mbox","sart-ans"},*types[]={"apple,t8132-nvme-ans2","apple,asc-mailbox-v4","apple,t6000-sart"};
 for(int i=0;i<3;i++){n=fdt_path_offset(s,as[i]); assert(n>=0); assert(!fdt_setprop_string(s,n,"compatible",types[i])); n=fdt_path_offset(s,as[i]); assert(!fdt_setprop_string(s,n,"status","okay"));}
 n=fdt_path_offset(s,"ans");assert(!fdt_setprop(s,n,"reg-names",names,sizeof(names))); n=fdt_path_offset(d,"ans");assert(!fdt_setprop(d,n,"reg-names",names,sizeof(names)));
 n=fdt_path_offset(s,"/reserved-memory/asc-firmware@900000000");if(n>=0)assert(!fdt_del_node(s,n)); n=fdt_path_offset(s,"/reserved-memory/flash@900080000");if(n>=0)assert(!fdt_del_node(s,n));
 int sn=endpoint(s); endpoint(d); unsigned char bad[]={1,1,2,3,4,5},good[]={2,1,2,3,4,5};
 assert(!fdt_setprop(s,sn,"local-mac-address",bad,6)); size_t cap=fdt_totalsize(d); void *before=malloc(cap); assert(before); memcpy(before,d,cap);
 assert(apple_j773_import_fdt(d,s)<0); assert(!memcmp(before,d,cap)); free(before);
 sn=fdt_path_offset(s,"/soc/pcie@1cb0000000/pci@2,0/ethernet@0,0"); assert(!fdt_setprop(s,sn,"local-mac-address",good,6));
 assert(apple_j773_import_fdt(d,s)==1); int len; n=fdt_path_offset(d,"/soc/pcie@1cb0000000/pci@2,0/ethernet@0,0"); const void *mac=fdt_getprop(d,n,"local-mac-address",&len);
 assert(mac && len==6 && !memcmp(mac,good,6)); assert(!strcmp(fdt_getprop(d,n,"status",NULL),"disabled"));
 puts("complete importer rejects invalid MAC atomically and copies valid MAC"); free(s);free(d);
}
'''
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp)
    binary = t.build_importer(p)
    source = t.compile_tree(p, 'source', t.fixture_tree(True, graphics=False))
    target = t.compile_tree(p, 'target', t.fixture_tree(False, graphics=False))
    subprocess.run([str(binary), str(source), str(target)], check=True)
