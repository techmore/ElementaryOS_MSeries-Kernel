#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Wrap an OmarchyM4Mini J773g image as an Omarchy Mac installer payload.

  make-gravity-payload.py IMAGE_DIR STAGE1 ICON TEMPLATE_JSON OUT_DIR

IMAGE_DIR      andreinita21/OmarchyM4Mini tools/j773g-image.sh output (root.img, boot.img, esp/)
STAGE1         Gravity's raw m1n1 Stage 1 (gravity-bootloader-stage1 m1n1-asahi.bin)
ICON           omarchy-volume.icns (from the previous Omarchy payload)
TEMPLATE_JSON  the previous installer_data.json (our engine's fields)
OUT_DIR        writes omarchy-<date>-aarch64-apple-silicon-mac-j773g-gravity-os-package.zip
               and installer_data.json, ready for Packaging/build-j773g-developer.sh

The engine (j773g/gravity-boot-chain) registers esp/gravity/stage1-j773g.bin as the stub's
boot object, with chosen.gravity,efi-system-partition and chainload variables.
"""
import datetime
import hashlib
import json
import os
import sys
import zipfile

image_dir, stage1, icon, template, out_dir = sys.argv[1:6]
stage1_data = open(stage1, "rb").read()
assert stage1_data.endswith(b"STACKBOT") and len(stage1_data) % 65536 == 0, "not a raw Gravity Stage 1"
for name in ("root.img", "boot.img"):
    size = os.path.getsize(os.path.join(image_dir, name))
    assert size > 0 and size % 4096 == 0, f"{name} size {size} is not 4 KiB aligned"
esp = os.path.join(image_dir, "esp")
for required in ("m1n1/boot.bin", "EFI/BOOT/BOOTAA64.EFI", "limine.conf"):
    assert os.path.getsize(os.path.join(esp, required)) > 0, f"esp/{required} missing"

date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y.%m.%d")
package = f"omarchy-{date}-aarch64-apple-silicon-mac-j773g-gravity-os-package.zip"
os.makedirs(out_dir, exist_ok=True)
zip_path = os.path.join(out_dir, package)

with zipfile.ZipFile(zip_path, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for root, dirs, files in os.walk(esp):
        dirs.sort()
        for f in sorted(files):
            full = os.path.join(root, f)
            assert not os.path.islink(full), f"symlink on the ESP: {full}"
            rel = os.path.relpath(full, esp)
            if rel.startswith("gravity/"):
                continue
            z.write(full, "esp/" + rel)
    z.writestr("esp/gravity/stage1-j773g.bin", stage1_data)
    z.write(icon, "omarchy-volume.icns")
    z.write(os.path.join(image_dir, "boot.img"), "boot.img")
    z.write(os.path.join(image_dir, "root.img"), "root.img")

data = json.load(open(template))
entry = data["os_list"][0]
entry["package"] = package
entry["name"] = "Omarchy"
entry["supported_fw"] = ["26.6.2"]
json.dump(data, open(os.path.join(out_dir, "installer_data.json"), "w"), indent=2)

digest = hashlib.sha256()
with open(zip_path, "rb") as fd:
    for block in iter(lambda: fd.read(1 << 20), b""):
        digest.update(block)
print(f"{package} {os.path.getsize(zip_path)} bytes sha256 {digest.hexdigest()}")
