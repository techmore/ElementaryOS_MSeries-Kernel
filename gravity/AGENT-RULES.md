# Rules for the M4 mini port (agents and people)

These rules cover every repo in the Mac mini M4 (J773g) Omarchy port:

| Repo | Working branch | What it holds |
|---|---|---|
| [techmore/linux-m1pro-touchid](https://github.com/techmore/linux-m1pro-touchid) | `elementaryos-mseries` | Kernel: Aurora `aurora-wip` plus our J773g commits |
| [techmore/m1n1](https://github.com/techmore/m1n1) | `elementaryos-mseries` | Boot loader: GPU, storage and display handoff |
| [techmore/omarchy-pkgs](https://github.com/techmore/omarchy-pkgs) | `elementaryos-mseries` (+ `-mlx`, `-safeboot`, `-ane`) | Pacman packages built from the pins above |
| [techmore/omarchy-mac-installer](https://github.com/techmore/omarchy-mac-installer) | `elementaryos-mseries` | macOS installer app, engine, image and catalog |
| [techmore/ElementaryOS_MSeries-Kernel](https://github.com/techmore/ElementaryOS_MSeries-Kernel) | `gravity-series-validation` | These docs: release gate, audits, procedures |

Each rule says why, so you can judge edge cases. If a rule and the owner disagree, the owner wins; then fix the rule here.

## 1. Where work goes

1. **Work only in the `techmore` forks above.** Push to our working branches or `mini/*` topic branches. Never push, open PRs, open issues or comment on upstream projects (aurora-silicon, AsahiLinux, GravityLinux, omacom, basecamp) on your own initiative.
   *Why:* our branches are where we get it booting. Upstream sees it only after it works.
2. **Port up, not down.** Gravity's M4 work is ported up onto Aurora `aurora-wip` as small, focused commits. We don't rebase our tree onto Gravity.
   *Why:* Aurora is the base we will submit to. Gravity is a source of fixes, not a base.
3. **Upstream only after hardware validation and owner approval.** "Validated" means it passed [RELEASE-GATE-2026-10-31.md](RELEASE-GATE-2026-10-31.md) on the owner's M4 mini. Then ask the owner about each submission, one at a time.
4. **Check before you submit or comment anywhere.** First look at the target repo's open PRs, branches and recent commits for the same work. Then read its contributing rules, commit style and sign-off rules. Check twice.
   *Why:* upstream projects often already have a branch or PR for the thing you found.
5. **Never commit secrets.** Signing keys live in `~/.config/omarchy-dev-keys/` (mode 700/600) and nowhere else. No passwords, tokens or private keys go in repos, logs, artifacts or PR text. Public SSH keys come from `github.com/techmore.keys` at install time.

## 2. Branches and merges

1. **Cut topic branches from the current working branch.** Name them `mini/<area>` (`mini/hdmi`, `mini/audio`, `mini/usb4`, `mini/bt`, `mini/smc-power`). Branch from today's `elementaryos-mseries`, not from an old copy.
   *Why:* a topic branch cut from an old tree carries old files back in. The audio branch carried an old workflow, and merging it silently reverted CI to a 24.04 hosted runner with no cache.
2. **A topic branch changes only its own area.** Before you merge, run `git diff <working-branch>...<topic> --stat`. Any file outside the topic's area (especially `.github/`) is a bug. Drop it from the topic first.
3. **Merge topics together, then build once.** Merge every green topic into the working branch locally, check the device trees (section 4), and push once.
4. **Each commit stands alone.** One logical change per commit, with a message that says what and why. Upstream submission later depends on this.
5. **Keep fork-only commits separate.** CI routing, runner changes and agent notes are ours, not upstream's. Give them their own commits (`ci: ...`, `docs: ...`) so they are easy to drop when we submit upstream.
6. **Follow each repo's own agent policy.** Aurora's m1n1 carries an `aurora-agent-policy` workflow that resets `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` and `.github/copilot-instructions.md` to the copy on `main`, every push and every hour. Don't edit those files there. Our m1n1 notes live in `ELEMENTARYOS-MSERIES.md`.

## 3. CI

All CI runs on the owner's Mac mini M4. Five self-hosted runners live in a Lima VM named `kbuild` (Ubuntu 26.04 LTS, Apple Virtualization). Setup and management: [CI-RUNNER-M1PRO.md](CI-RUNNER-M1PRO.md).

| Repo | Repo variable | Runners |
|---|---|---|
| linux-m1pro-touchid | `KERNEL_RUNNER` | `m4mini-kbuild`, `m4mini-kbuild-2` |
| m1n1 | `M1N1_RUNNER` | `m4mini-m1n1` |
| omarchy-pkgs | `PKG_RUNNER`, `PKG_BUILD_JOBS` | `m4mini-pkgs`, `m4mini-pkgs-2` |

1. **Route jobs with the repo variable, never a hard-coded label.** Write `runs-on: ${{ fromJSON(vars.KERNEL_RUNNER || '"ubuntu-26.04-arm"') }}`. Set the variable to `["self-hosted","linux","arm64","m4mini"]`.
   *Why:* when the mini boots Linux for testing, the runners go offline. Deleting the variable sends jobs to GitHub's runners with no code change.
2. **Ubuntu 26.04 only.** Build and test jobs fall back to `ubuntu-26.04-arm`. The VM is 26.04. Don't add `ubuntu-24.04*` to anything. Use `ubuntu-latest` only for tiny jobs that build nothing, like computing a matrix.
   *Why:* 26.04 is the current LTS, with the newer kernel and toolchain we target.
3. **Keep build state on self-hosted runners.**
   - Kernel builds use `ccache clang` and a persistent output tree, `O=$HOME/kbuild/<branch-slug>`. The 4 newest trees are kept.
   - Package builds keep their container layers.
   - Use `actions/cache` only on hosted runners. Uploading and restoring a cache on our own disk is slower than the disk.
   - Self-hosted jobs skip `apt`. Install toolchain changes in the VM image instead, and pin versions (Rust 1.99.0, bindgen 0.73.2).
4. **Keep artifacts small.** Upload only what boot or install needs: the xz-compressed `Image`, the `t8132-*.dtb` files, `.config`, `kernelrelease` and `SHA256SUMS`. Never upload a build tree or modules tarball "just in case".
5. **Batch pushes.** Push once when the batch is ready.
   - In the kernel repo, a new push cancels the branch's running build (`cancel-in-progress: true`). A cancelled kernel build wastes the 30+ minutes it already ran.
   - In m1n1 and the packages repo, each push queues another full build behind the first. The runners are shared, so the extra build delays everything else.
   - Docs-only commits use `[skip ci]`.
   - Don't push to a branch with a build running unless you mean to replace that build.
6. **Pin and verify inputs.** Build inputs from other repos (kernel config, bindgen wrapper, config validator) come from a pinned commit and are checked with sha256. Never fetch `main` at build time.
7. **Check the device tree in CI.** The kernel job checks the J773g DTB with `fdtget`. A job that builds without the board's nodes is a failure, not a pass.
8. **Watch runs, don't guess.** Use `gh run list --repo techmore/<repo> --limit 5` or the Actions tab. Report a cancelled or failed run as cancelled or failed.

## 4. Before you push the kernel

1. **Run the device-tree check.** The `pre-push` hook compiles all six `t8132` device trees and blocks the push if any fails. Install it in every kernel clone. Skip it (`SKIP_DT_CHECK=1`) only for pushes that don't touch `arch/arm64/boot/dts`.
   *Why:* a bad merge in `t8132-j773g.dts` costs a 30-minute CI run to find. `dtc` finds it in seconds.
2. **Resolve device-tree conflicts by hand, then compile.** Never just delete the conflict markers. Rebuild the node list on purpose, then run the hook.

## 5. macOS host pitfalls

Work happens on a Mac, which bites in these ways:

1. **Never `git add -A` or `git add .` in a kernel checkout.** The macOS disk is case-insensitive, so the kernel's case-pair files (netfilter `xt_*`, for example) show as modified forever. Stage the files you changed by name.
2. **`.github/` is gitignored in the kernel tree.** Use `git add -f .github/workflows/<file>`.
3. **zsh eats `$var:x`.** zsh reads `$t:arch` or `$c:r` as a modifier and mangles refs. Always write `${var}`.
4. **`/bin/bash` is 3.2.** It has no associative arrays and no `mapfile`. Use `case`, or run scripts in the VM.
5. **`log` is a zsh builtin.** For the macOS unified log, use `/usr/bin/log show ...`.
6. **Don't do destructive disk work for the owner.** Partitioning, `diskutil` erase or resize, and deleting volumes are the owner's to run. Prepare the exact commands and explain them.
7. **Long jobs survive only if detached.** A background `&` dies with its shell. Use a real background runner (the agent's background task, `nohup`, or the VM).

## 6. Hardware facts to remember

- The board is J773g (Mac16,10, T8132 M4). The GPU firmware matches macOS 26.6.2 (25G83); the installer installs a 26.6.2 stub. Don't bump the host macOS before the first validated install.
- Most "unsupported board" gates in Aurora were only name checks. The J773g ADT matches J713 for the GPU and the PMP. Check the ADT before you write new code.
- HDMI on the mini goes through a DPTX PHY and an internal DP-to-HDMI converter. Port inventory: [J773G-PORTS-FROM-MACOS-2026-10-31.md](J773G-PORTS-FROM-MACOS-2026-10-31.md).
- Debug SSH is on by default in developer builds (keys from `github.com/techmore.keys`, mDNS name). It is how to debug a blank or broken GUI.

## 7. Keep these rules current

When something bites you twice, add a rule here in the same commit as the fix, with its why. Keep each repo's `AGENTS.md` a short pointer to this file. Don't copy the rules into each repo, or the copies will drift.
