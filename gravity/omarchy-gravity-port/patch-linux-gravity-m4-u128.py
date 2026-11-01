#!/usr/bin/env python3
"""Make linux-gravity-m4's PKGBUILD build against linux-api-headers 7.3.

The container's /usr/include/asm/{ptrace,sigcontext}.h (linux-api-headers 7.3) use __u128.
Host tools such as resolve_btfids include this 7.1 tree's tools/include/linux/types.h, which
shadows <linux/types.h> and does not define __u128. prepare() adds the same typedefs the uapi
headers use (repeating an identical typedef is valid C11).
"""
import sys

path = sys.argv[1]
text = open(path).read()
anchor = '  cd $_srcname\n\n  echo "Setting version..."'
if "tools/include/linux/types.h" in text:
    print("already patched")
    sys.exit(0)
assert anchor in text, "prepare() anchor not found"
fix = r'''  cd $_srcname

  # linux-api-headers 7.3 use __u128 in asm/ptrace.h and asm/sigcontext.h; this 7.1 tree's
  # tools/include/linux/types.h (it shadows <linux/types.h> for host tools such as
  # resolve_btfids) lacks it. Add the uapi typedefs; repeating an identical typedef is fine.
  if ! grep -q __u128 tools/include/linux/types.h; then
    python3 - tools/include/linux/types.h <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p).read()
inc = "#include <asm/types.h>\n"
add = ("#ifdef __SIZEOF_INT128__\n"
       "typedef __signed__ __int128 __s128 __attribute__((aligned(16)));\n"
       "typedef unsigned __int128 __u128 __attribute__((aligned(16)));\n"
       "#endif\n")
assert inc in s, "asm/types.h include not found"
open(p, "w").write(s.replace(inc, inc + add, 1))
PYEOF
  fi

  echo "Setting version..."'''
open(path, "w").write(text.replace(anchor, fix, 1))
print("patched", path)
