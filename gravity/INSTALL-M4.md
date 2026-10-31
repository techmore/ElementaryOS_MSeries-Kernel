# Installing Omarchy on this Mac mini M4

One page. Do it in order. macOS stays installed and is your fallback the whole time.

## 1. Before you start (2 minutes)

- **Plug in an Ethernet cable if you can.** Wi-Fi calibration loading is new and unproven on this Mac; Ethernet is the safe path for the first boot.
- **Connect the monitor by HDMI** (the fallback cable) and a **wired USB keyboard** straight to the mini. Bluetooth keyboards don't work in the boot menus.
- **Keep your phone nearby** to photograph the screen if anything goes wrong. A crash message only appears on screen.
- Leave **macOS as the startup disk** (System Settings → General → Startup Disk → Macintosh HD). Every failed boot then comes back to macOS by itself.

## 2. Install (macOS side)

1. Double-click **`Omarchy-J773g-developer-wifi.pkg`** in your home folder under `Omarchy-J773g` (`~/Omarchy-J773g/`, 3.4 GB, SHA-256 `c7e5a5fe7ddc3ee44585f77e2c4a30d7a6322e9e7cc9ca84a1e0232f5947206f`, kernel 7.3.0-90-3 with Wi-Fi calibration, installer app 2.3.0).   If macOS blocks it, right-click the file → **Open**, or go to System Settings → Privacy & Security → **Open Anyway**.
   When the package finishes, **delete the `.pkg` file** (Move to Trash, then empty the Trash). The installed app carries its own copy of the image, and the installer needs the space: Omarchy needs at least ~41 GB carved out of the macOS disk.
2. Open **Omarchy Installer** from Applications and follow it. When it asks how much space to give Omarchy, choose about **90 GB**. About 108 GB is free; the installer also needs ~6 GB for a macOS 26.6.2 system stub, and macOS should keep ~10 GB free for itself. It shrinks the macOS partition, adds Omarchy beside it, and asks for your Mac password when it needs admin rights.
3. At the end it asks you to shut down. It also records how long each step took, for the install-speed measurement.

## 3. First boot

1. With the Mac off, **press and hold the power button** until "Loading startup options…" appears, then let go.
2. Pick the **Omarchy** volume and click **Continue**. Don't click "Always Use".
   The first time, macOS may ask you to confirm the new startup security setting: follow the prompts and enter your password.
3. You should see boot text, then Omarchy's first-boot setup, then the desktop **on the HDMI monitor**. Note the time it takes.
4. On first login, Omarchy installs **Claude Code** by itself (needs the network). When `claude --version` answers, the AI gate is met.

**If it goes wrong:** photograph the last screen. A crash restarts the Mac into macOS within about 10 seconds; a hang may need the power button held for 10 seconds. Then tell me what you saw.

## 4. Debug access from another computer

SSH is on automatically, key-only, using the keys on your GitHub account (`github.com/techmore.keys`). Once the desktop is up:

```bash
ssh <your-omarchy-username>@<hostname>.local
```

This is how I can look at a broken desktop if the screen goes blank.

## 5. Measurements (after the desktop is up)

- **Install speed:** `cat /var/log/omarchy/install-timing.jsonl`. It holds the macOS install phases plus first boot, desktop and Claude Code times.
- **MLX speed on Linux:** the MLX runtime is in the image, but the benchmark package isn't. Once SSH works, tell me and I'll install `omarchy-mlx-m4-bench` (it's already built), run it, and compare with the macOS numbers in PR #709.

## What's not tested yet

This is the first time this exact build boots on the Mac. These parts are expected to work but are unproven on hardware: the HDMI picture after Linux takes over, speakers, Bluetooth, and the GPU desktop. USB4 and the Dell dock are not supported yet.
