# Self-hosted kernel build runner on the M1 Pro

GitHub's hosted arm64 runner has 4 cores, and personal accounts cannot use larger hosted runners. The
owner's M1 Pro (elementary OS, arm64) builds the `elementaryos-mseries` kernel instead when it is registered.

Scope: repository runner for `techmore/linux-m1pro-touchid` only. The workflow
(`.github/workflows/elementaryos-mseries-kernel.yml`) runs on push and manual dispatch, never for pull
requests, so code from forks cannot run on this machine.

## 1. Build tools (once)

```bash
sudo apt-get install -y build-essential bc bison flex cpio dwarves device-tree-compiler kmod libelf-dev libssl-dev python3 clang lld llvm libclang-dev ccache git curl
```

The workflow installs Rust 1.99.0 (rustup) and bindgen 0.73.2 under the runner user's home on first run.

## 2. Runner (actions/runner v2.338.2, linux-arm64)

```bash
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -fsSLO https://github.com/actions/runner/releases/download/v2.338.2/actions-runner-linux-arm64-2.338.2.tar.gz
echo "670adb2f268fe21dcbb58b3db0e0aa9d5b3bddfe2c651481336e561ff86de945  actions-runner-linux-arm64-2.338.2.tar.gz" | sha256sum -c
tar xzf actions-runner-linux-arm64-2.338.2.tar.gz
./config.sh --url https://github.com/techmore/linux-m1pro-touchid --name m1pro-elementary --labels m1pro --unattended --token "$(gh api -X POST repos/techmore/linux-m1pro-touchid/actions/runners/registration-token --jq .token)"
sudo ./svc.sh install && sudo ./svc.sh start
```

The registration token is created by `gh` on the M1 Pro (valid one hour). Without `gh` there, create it on any
machine with `gh api -X POST repos/techmore/linux-m1pro-touchid/actions/runners/registration-token --jq .token`.

## 3. Point the workflow at it

```bash
gh variable set KERNEL_RUNNER --repo techmore/linux-m1pro-touchid --body '["self-hosted","linux","arm64","m1pro"]'
```

Delete the variable to go back to GitHub's runner. If the M1 Pro is off, jobs wait in the queue for it.

## Notes

- Builds use the runner user's disk (about 15 GB for a kernel build tree plus ccache in `~/.cache/ccache`).
- The M1 Pro's own boot is untouched; this only compiles.
- Stop the service with `sudo ./svc.sh stop` in `~/actions-runner`; remove with `./config.sh remove`.
