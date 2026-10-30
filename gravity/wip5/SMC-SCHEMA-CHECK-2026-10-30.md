# WIP5 J773g SMC schema checks — 2026-10-30

On the full-source replay documented in `SMC-FULL-REPLAY-2026-10-30.md`,
used a private virtual environment with `dtschema` 2026.9 and `yamllint`.
Ran the kernel's `dt_binding_check` for `mailbox/apple,mailbox.yaml` and
`mfd/apple,smc.yaml`; the schema and example checks passed. The first run
skipped YAML lint because the tool was missing; after installing it privately,
a second run performed lint and passed.

Validated the compiled J773g DTB (SHA-256
`c732cc4e058f1494b28272ccef1a7313adff009b078c283306168482740952ad`)
with `dt-validate` against the processed WIP5 schema, limited to those two
binding IDs. It emitted no diagnostics. To verify both schemas were selected,
two separate temporary DTB copies were modified: removing SMC `reg-names`
produced the expected required-property diagnostic from `apple,smc.yaml`, and
removing mailbox `interrupt-names` produced the expected diagnostic from
`apple,mailbox.yaml`. Neither negative-control copy was installed.

This covers the two changed binding files and their corresponding nodes only;
it is not a full-tree `dtbs_check`, a kernel build, driver probe, reboot test,
or evidence of SMC firmware behavior. The DTB was built with defconfig and the
local 0001 draft; the remaining J773g bring-up is incomplete.
