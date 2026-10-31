# J773g (Mac mini M4) SMC power: button, AC, poweroff/reboot

Branch: `techmore/linux-m1pro-touchid` `mini/smc-power` (base `origin/elementaryos-mseries` fa26b0f92ef6).
Worktree: /private/tmp/claude-501/wt/smc. CI: https://github.com/techmore/linux-m1pro-touchid/actions/runs/41209947725 (success)

## Result: DT-only, two commits, J773g file only

| Commit | What |
|---|---|
| bfb761728aae `arm64: dts: apple: t8132-j773g: describe the primary PMU NVMEM` | Enables `nub_spmi` and adds `pmic1: pmic@e` (`apple,abbey-pmic`, `apple,spmi-nvmem`) with the J713 NVMEM layout. Adds the `spmi-primary` and `pmu-primary` aliases. |
| b248af9c2e2e `arm64: dts: apple: t8132-j773g: add SMC poweroff and restart` | Adds `smc_reboot: reboot` (`apple,t8132-smc-reboot`, `apple,smc-reboot`) with the shutdown_flag, boot_stage, boot_error_count and panic_count cells. |

No driver changes. Aurora's macsmc already has everything the M6 work had to add:

- T8132 takes the full macsmc path: NTAP notifications on, plus the `macsmc-input`, `macsmc-power`, gpio, hwmon, reboot and rtc cells. Joshua's 308a7f0a9a94 and 017d8cebaee1 only remove a T8152-only early return that our tree doesn't have.
- All drivers are built: `INPUT_MACSMC_INPUT=m`, `POWER_RESET_MACSMC=m`, `MACSMC_POWER=m`, `NVMEM_APPLE_SPMI=y`, `SPMI_APPLE=y`, `RTC_DRV_MACSMC=y` (arch/arm64/configs/asahi.config).

## Evidence from the J773g ADT (/private/tmp/claude-501/kern/adt-j773.txt)

- **Power button.**
  - `/buttons`: `function-button_hold = 241:btnR('bHLD')` (l.27539).
  - `smc-pmu`: `event_name-bit0 = pwrbtn`.
  - `macsmc-input` registers with no DT node and binds when `bHLD` exists. It reports KEY_POWER for event 0x7201 button 0x01 ("Mac Mini chassis"). A long hold calls `kernel_power_off()`, which now has a handler. **No DT needed.**
- **Poweroff/restart.**
  - `pmu-main`: `function-external_standby = 241:keyW('MBSE')` (l.25426). That is the key macsmc-reboot writes (`offw`/`off1` for poweroff, `phra` for restart).
- **PMU.**
  - `/arm-io/nub-spmi0/pmu-main`: `compatible = pmu,spmi, pmu,abbey`, `hw-name = abbey`, `is-primary = 1`, `reg` = 0xe.
  - Same scratchpads as the J713's Abbey: `info-rtc_scrpad` 0x2100, `info-leg_scrpad` 0xf800.
  - nub-spmi0 `reg[0]` = 0x188714000/0x4000, which maps to DT 0x3_88714000.
- **m1n1.** `dt_set_t8132_lifecycle()` in techmore/m1n1 `elementaryos-mseries` (src/kboot.c:6540, called at l.6998) fills the SPMI reg and the PMU slave ID **only for `apple,j713`**. So the J773g DT hard-codes both values. The aliases are added so that a future m1n1 that handles the J773g rewrites them with the same values.
- **AC.**
  - The AC input sensors (`PDTR`, `VD0R`, `ID0R`; the `PSTR`/`PMVR` power keys too) are already in `hwmon-common.dtsi`, which J773g includes. These are the same keys as Joshua's 449fbe39add3.
  - `macsmc-power` registers a `macsmc-ac` supply (`ONLINE` from `CHIS`) only if the SMC has `CHIS`. The ADT has no key list, so whether the mini has `CHIS` is **unknown until boot**.
  - If it does not, there is no power_supply. systemd/upower then treat the machine as on AC, which is correct for a desktop. No change made.
- **gp00 (Gravity 3988dac166 / f33138368c / ab76ccfdd0).**
  - Already in Aurora as `apple,smc-low-gpio`.
  - It is **not** the power button: the commits use it for the M3 Pro/Max keyboard and trackpad and for the DP-to-HDMI converter.
  - On the J773g, the only `gp` key is `gp0e` (stockholm/NFC enable, l.1454), so no low-gpio node is added.

## Risks and checks on first boot

- **SPMI.** This is the first J773g use of `nub_spmi`. The J713 uses the same controller, compatible and PMU.
  - Check: `dmesg | grep -i -e spmi -e nvmem -e macsmc-reboot`.
  - Check: `/sys/bus/nvmem/devices/`.
- **macsmc-reboot probe** writes `boot_stage` = kernel-started and clears the PMU panic and boot-error counts (same as the J713).
- **Poweroff bit.** `shutdown_flag` is boot key 0xf bit 3 (J713/t8103/t8122). Joshua's M6 decode suggests macOS may use bit 4.
  - If `poweroff` restarts the mini, change the cell to `shutdown-flag@f80f,4` with `bits = <4 1>`.
  - After a real poweroff, the mini needs the physical button to power on.
- **Power button.** `evtest`: look for "Apple SMC power/lid events" with KEY_POWER. logind handles it (HandlePowerKey).
- **AC.** `ls /sys/class/power_supply/` (`macsmc-ac` only if `CHIS` exists). `sensors` shows AC Input Power/Voltage/Current.
- **Not done:** `smc-rtc`. The `rtc_offset` cell is defined, so enabling it is one node (copy the J713 `rtc` node). It was left out to keep the change minimal.

## Verification

- dtc (`audit/dtcbuild`, flags from dtc-branch.sh): all six t8132 boards compile with 0 errors. The only new warnings are the expected `spmi@0` unit-address ones (the J713 has the same placeholder node).
- CI run 41209947725 passed (Image, modules and DTBs, with the config validated).
