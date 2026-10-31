#!/bin/bash
# Pre-push: compile the six T8132 board device trees from the commit being pushed (a few seconds).
# Catches broken DT merges before a 30-minute CI build does. Skip with SKIP_DT_CHECK=1.
[ -n "$SKIP_DT_CHECK" ] && exit 0
B=/private/tmp/claude-501/kern/audit/dtcbuild
[ -x $B/scripts/dtc/dtc ] || exit 0
z=0000000000000000000000000000000000000000
while read -r lref lsha rref rsha; do
  [ "$lsha" = "$z" ] && continue
  git diff --quiet "${rsha/$z/HEAD~0}" "$lsha" -- arch/arm64/boot/dts/apple include/dt-bindings 2>/dev/null && [ "$rsha" != "$z" ] && continue
  T=$(mktemp -d); git archive "$lsha" arch/arm64/boot/dts/apple include/dt-bindings scripts/dtc/include-prefixes | tar -x -C "$T"
  fail=0
  for b in t8132-j773g t8132-j713 t8132-j604 t8132-j715 t8132-j623 t8132-j624; do
    [ -f "$T/arch/arm64/boot/dts/apple/$b.dts" ] || continue
    if ! clang -E -P -nostdinc -undef -D__DTS__ -x assembler-with-cpp -I "$T/include" -I "$T/scripts/dtc/include-prefixes" -I "$T/arch/arm64/boot/dts/apple" "$T/arch/arm64/boot/dts/apple/$b.dts" -o "$T/$b.pre" 2>"$T/err" \
       || ! $B/scripts/dtc/dtc -q -I dts -O dtb -o /dev/null -Wno-unit_address_vs_reg -Wno-simple_bus_reg -Wno-avoid_unnecessary_addr_size -Wno-unique_unit_address "$T/$b.pre" 2>>"$T/err"; then
      echo "pre-push: $b.dts does not compile in $lref:"; grep -i -m3 error "$T/err"; fail=1
    fi
  done
  rm -rf "$T"; [ $fail -eq 0 ] || { echo "pre-push: fix the device tree or set SKIP_DT_CHECK=1"; exit 1; }
done
exit 0
