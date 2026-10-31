# J773g (Mac mini M4) audio: speaker and 3.5 mm jack on elementaryos-mseries

Branch `mini/audio` on techmore/linux-m1pro-touchid, based on `origin/elementaryos-mseries` (fa26b0f92ef6).
Worktree: `/private/tmp/claude-501/wt/audio`.

## Result

| Path | State |
|---|---|
| Internal speaker (SN012776 on i2c3 @0x38, MCA TX0) | Ported. It is Gravity's code as it ran on the mini (byte-identical `sound/soc/apple/t8132/*`), built as the opt-in module `snd-t8132-speaker`. Not tested on hardware with this kernel. |
| Headphone jack (CS42L84 on i2c1 @0x4b) | Partly done. The codec is described and Aurora's `cs42l84` driver binds to it, but **no card plays through it** (blocker below). |

## Commits (oldest first)

| Commit | Author | Content |
|---|---|---|
| ASoC: apple: mca: support the T8132 banked TX path | Niklas Sheth (Gravity 0046) | `mca_variant` table, `apple,t8132-mca` (one cluster, TX only, staged enables, fixed-parent divider), binding. Hand-merged: there was a single conflict in `mca_be_shutdown`, where Aurora's `scoped_guard()` is kept. T8103, T6000 and T8112 get the identity layout, so their behaviour is unchanged. |
| ASoC: tas2764: add fail-closed protected attenuation helpers | Niklas Sheth (0047) | `tas2764_{set,get}_protected_attenuation`, `tas2764_check_fault`. Hand-merged next to Aurora's SDZ-group code. `protection_failed` and the group failure now both refuse power-up, resume and stream startup. |
| ASoC: apple: add kernel-protected J773g speaker playback | Niklas Sheth (0048) | The `t8132/` machine driver, its Kconfig and Makefile, and `apple,j773g-speaker.yaml`. |
| …t8132: rely on ALSA for underrun stopping | Niklas Sheth (0053) | Applied unchanged. |
| …t8132: remove the codec speaker volume control | Niklas Sheth (0055) | Applied unchanged. The result equals `m4-mini-gravity` and `d1d4269fcce1`. |
| ASoC: apple: t8132: make the J773g speaker an explicit opt-in | claude | Kconfig: "(EXPERIMENTAL)" prompt, off by default, help text warning about the thermal limiter. `CONFIG_SND_SOC_APPLE_T8132_SPEAKER=m` added to `arch/arm64/configs/asahi.config`, which the workflow merges. Gravity's `t8132-audio.config` (built-in =y) is not carried. |
| arm64: dts: apple: add T8132 audio controllers and power domains | Niklas Sheth (0049) | `pmgr_audio` plus `ps_audio_{a,fr,p,base_ns_a,mca0_m}`, `dart_audio`, `mca` (one cluster) and `admac`. Everything is disabled, `pmgr_audio` included, so J713 and the other T8132 boards get no new power domains. The domains are defined inside the `pmgr_audio` node, not in `t8132-pmgr.dtsi`, because `drivers/soc/apple/t8132-platform-data.dts` (the J713 loader-ABI blob) includes that file and has no `pmgr_audio`. Putting them in `t8132-pmgr.dtsi` broke CI run 1. |
| arm64: dts: apple: enable the J773g internal speaker | Niklas Sheth (0050) | `speaker-audio`, i2c3 `speaker_amp` (shutdown GPIO AP 15), and enables the audio nodes. |
| arm64: dts: apple: t8132-j773g: add the headphone jack codec | claude | i2c1 `jack_codec`: `cirrus,cs42l84`, reset nub GPIO 0x11 (active high = run), IRQ AP 98 level low, prefix "Jack". |

Gravity's Signed-off-by lines and Assisted-By trailers are kept. Each modified commit has an `[elementaryos-mseries: …]` note and a `Co-Authored-By: Claude Opus 5.5` trailer.

## Choices that differ from the audit drafts

- The `mca` node uses Gravity's validated single-cluster form: reg 0xc000, one clock, `audio_p` and `mca0_m`, and `tx0a` = ADMAC channel 0. The draft `dt-03` listed three DMAs and three clocks, which the T8132 MCA binding rejects (maxItems 1). The `mca1_m`/`mca2_m` power domains are left out, since nothing would use them. For future use, their offsets are 0xf0 and 0xf8 in `pmgr_audio`.
- `dart_audio` uses the ADT size 0xc000. Gravity used 0x4000. The driver touches only the low registers either way.
- The amplifier has Aurora's compatible pair, `"ti,sn012776", "ti,tas2764"`. The driver matches the first entry, so it behaves the same as Gravity's.
- `speaker-audio` has no `apple,headphone-codec`. Gravity's DTS had that property, but no driver reads it and its binding forbids it.

## DT check

`dtc-branch.sh` adapted to the worktree: j773g, j713, j604, j715, j623 and j624 all compile with 0 errors. In the J773g DTB, mca, admac, dart_audio, pmgr_audio and i2c3 are "okay". In J713, `pmgr_audio` stays "disabled".

## Headphone jack: blocker and next steps

The J773g ADT (`/arm-io/iop-audio-controller`) shows macOS running all audio through the **AOP**. The relevant `dma-channels` entries are: speaker on base-ns ADMAC channel 0, `audio-codec-output` on channel 4 and `audio-codec-input` on channel 5. With two channels per cluster that is TX2/RX2, so **MCA cluster 2**. The data-node reg bytes are `01 13…` for the codec and `01 02…` for the speaker, and the codec frame is 64 bits at 48 kHz, set up through the NCO. T6040 J616s has the same channel numbers, and Aurora's notes there say "jack = MCA cluster 2". Gravity's T8132 MCA variant maps only cluster 0 and itself says it has not checked whether more clusters follow at that stride. Its staged enable registers (base+0x100…0x170, `BIT(cl->no)`) also suggest that the per-cluster layout is not a plain stride. I did not guess MMIO for cluster 2: an unmapped access can SError the machine.

There are two ways to finish the jack:
1. **AOP path (Aurora's M4-generation approach).** Aurora already plays the J616s (T6040) jack through `aop_audio` (`cout`/`cin` services, the `jack` DAI `<&aop_audio 4>`, and the `apple,j616-macaudio-jack` card using `cs42l84`). T8132 would need an `apple,t8132-aop` `AopHwConfig` in `drivers/soc/apple/aop.rs`, `aop`/`aop_mbox` DT nodes (with `dart-aop` = `dart_audio`), a `t8132` variant in `aop_audio.rs`, and a J773g jack card entry. Risk: the AOP firmware owns the MCA, while Gravity's speaker driver programs MCA directly. That would have to be resolved, probably by moving the speaker to the AOP `spkr` service too.
2. **Direct MCA path.** Reverse-engineer cluster 2 on hardware (m1n1 proxy, or a MMIO trace of the AOP), then extend `mca_t8132_variant` and the DT (`tx2a` = `<&admac 4>`, `rx2a` = `<&admac 5>`, `mca2_m`), and add a jack card: macaudio's `"apple,macaudio"` fallback or a small t8132 card.

## Hardware checks once a kernel is booted

- `dmesg | grep -i -E 'mca|admac|tas2764|j773g|speaker limiter'`. The card is `T8132Speaker`. Play with `aplay -D plughw:T8132Speaker file.wav`. The PCM is fixed at mono S24_LE 48 kHz and does not support mmap, so the plug layer is needed.
- `cat /sys/bus/platform/devices/speaker-audio/state` shows the limiter state.
- `dmesg | grep cs42l84` should show the device ID read (the codec answers on i2c1).
- To turn the speaker off: `blacklist snd_t8132_speaker`.

## CI

- Run 41208689879 **failed**: `t8132-pmgr.dtsi: Label or path pmgr_audio not found` while building `drivers/soc/apple/t8132-platform-data.dtb`. Fixed by folding the change into the SoC DT commit. The branch was then force-pushed (only `mini/audio`).
- Run 41210552868 **succeeded** at `mini/audio` head `a01076e2d2b5`. Image, modules and DTBs (j773g and j713) built, and `snd-t8132-speaker.ko` was built and installed. The MCA, TAS2764, CS42L84 and speaker sources produced no warnings. Configure and `validate-config.py` passed with `CONFIG_SND_SOC_APPLE_T8132_SPEAKER=m` from `asahi.config`.
- I also compiled the platform-data DT locally, and all six T8132 board DTBs compile.
