#!/usr/bin/env python3
"""Compile production U-Boot USB3 transfer helpers against libfdt host fixtures."""
from pathlib import Path
import os, re, subprocess, tempfile
p = Path('arch/arm/mach-apple/j713_fdt.c')
s = p.read_text()
def function(name):
    m = re.search(r'^static (?:int|bool) ' + name + r'\(', s, re.M)
    assert m, name
    b = s.index('{', m.start()); depth=1; end=b+1
    while depth:
        depth += (s[end] == '{') - (s[end] == '}'); end += 1
    return s[m.start():end] + '\n'
pre = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <libfdt.h>
typedef uint32_t u32; typedef uint64_t u64;
#define ARRAY_SIZE(x) (sizeof(x)/sizeof((x)[0]))
#define J713_FDT_MAX_SOURCE 262144
'''
names=['j713_check_ranges','j713_alias_node','j713_atc_tunables','j773_fixed_usb3_tunables']
test=r'''
static const char banks[] = "usb2phy\0pipehandler\0core\0axi2af\0lioa\0fabric\0common-config";
static const char *const props[] = {"apple,tunable-usb3-axi2af", "apple,tunable-usb3-lioa",
 "apple,tunable-usb3-fabric", "apple,tunable-usb3-config", "apple,tunable-usb3-common",
 "apple,tunable-usb3-efuse", "apple,tunable-lane0-usb", "apple,tunable-lane1-usb"};
static void setup(char *f, bool source, bool optin) {
 int n, chosen, aliases, soc; fdt32_t regs[28], triple[3];
 assert(!fdt_create_empty_tree(f, 8192));
 assert(!fdt_setprop_string(f,0,"compatible","apple,j773g"));
 assert(!fdt_setprop_u32(f,0,"#address-cells",2));assert(!fdt_setprop_u32(f,0,"#size-cells",2));
 chosen=fdt_add_subnode(f,0,"chosen");assert(chosen>=0);
 if(optin) assert(!fdt_setprop(f,chosen,"u-boot,j773g-usb3-calibration",NULL,0));
 aliases=fdt_add_subnode(f,0,"aliases");assert(aliases>=0);
 assert(!fdt_setprop_string(f,aliases,"atcphy2","/soc/phy"));
 soc=fdt_add_subnode(f,0,"soc");assert(soc>=0);
 assert(!fdt_setprop_u32(f,soc,"#address-cells",2));assert(!fdt_setprop_u32(f,soc,"#size-cells",2));
 n=fdt_add_subnode(f,soc,"phy");assert(n>=0);
 assert(!fdt_setprop_string(f,n,"compatible","apple,t8132-atcphy"));
 assert(!fdt_setprop_string(f,n,"status","disabled"));
 assert(!fdt_setprop(f,n,"apple,fixed-usb3",NULL,0));
 assert(!fdt_setprop(f,n,"reg-names",banks,sizeof(banks)));
 for(unsigned i=0;i<7;i++){regs[4*i]=cpu_to_fdt32(1);regs[4*i+1]=cpu_to_fdt32(0x10000*i);regs[4*i+2]=0;regs[4*i+3]=cpu_to_fdt32(0x4000);}
 assert(!fdt_setprop(f,n,"reg",regs,sizeof(regs)));
 triple[0]=cpu_to_fdt32(0x100);triple[1]=cpu_to_fdt32(0xff);triple[2]=cpu_to_fdt32(0x55);
 if(source) for(unsigned i=0;i<ARRAY_SIZE(props);i++)assert(!fdt_setprop(f,n,props[i],triple,sizeof(triple)));
}
int main(void){
 char src[8192],dst[8192]; int n,len; const void *p;
 setup(src,true,true);setup(dst,false,false);
 assert(!j773_fixed_usb3_tunables(dst,src)); n=fdt_path_offset(dst,"/soc/phy");
 assert(!fdt_getprop(dst,n,props[0],&len));
 setup(dst,false,true); assert(!j773_fixed_usb3_tunables(dst,src)); n=fdt_path_offset(dst,"/soc/phy");
 for(unsigned i=0;i<ARRAY_SIZE(props);i++){p=fdt_getprop(dst,n,props[i],&len);assert(p && len==12);}
 setup(dst,false,true);n=fdt_path_offset(src,"/soc/phy");assert(!fdt_delprop(src,n,props[0]));
 assert(j773_fixed_usb3_tunables(dst,src)==-EINVAL);
 setup(src,true,true);setup(dst,false,true);n=fdt_path_offset(src,"/soc/phy");
 fdt32_t bad[]={cpu_to_fdt32(0x4000),cpu_to_fdt32(0xff),cpu_to_fdt32(0)};
 assert(!fdt_setprop(src,n,props[0],bad,sizeof(bad)));assert(j773_fixed_usb3_tunables(dst,src)==-EINVAL);
 setup(src,true,true);setup(dst,false,true);n=fdt_path_offset(dst,"/soc/phy");
 fdt32_t other[]={cpu_to_fdt32(9)};assert(!fdt_setprop(dst,n,"reg",other,sizeof(other)));
 assert(j773_fixed_usb3_tunables(dst,src)==-EINVAL);
 setup(src,true,true);setup(dst,false,true);n=fdt_path_offset(dst,"/soc/phy");
 assert(!fdt_setprop_string(dst,n,"status","okay")); assert(j773_fixed_usb3_tunables(dst,src)==-EINVAL);
 setup(src,true,true);setup(dst,false,true);n=fdt_path_offset(dst,"/chosen");
 assert(!fdt_setprop_u32(dst,n,"u-boot,j773g-usb3-calibration",1)); assert(j773_fixed_usb3_tunables(dst,src)==-EINVAL);
 setup(src,true,true);setup(dst,false,true);n=fdt_path_offset(src,"/soc/phy");
 assert(!fdt_setprop(src,n,props[0],bad,8)); assert(j773_fixed_usb3_tunables(dst,src)==-EINVAL);
 puts("U-Boot mini USB3: opt-in, complete bundle, bounds and bank match passed");
}
'''
with tempfile.TemporaryDirectory() as td:
 c=Path(td)/'test.c'; exe=Path(td)/'test'; c.write_text(pre+''.join(function(n) for n in names)+test)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I',os.environ.get('LIBFDT_INCLUDE', '/usr/include'),str(c),'-lfdt','-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
