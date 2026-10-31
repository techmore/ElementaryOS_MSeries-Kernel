# Manual diagnostic only. Do not install or run without a recovery route.
# No saveenv: these changes exist only in the current U-Boot session.
if test -n "${fw_dev_part}" && part uuid nvme ${fw_dev_part} inspection_uuid && test "${inspection_uuid}" = "ca0747c3-afff-435b-9a54-7be212d75f19" && test -n "${kernel_addr_r}" && test -n "${fdt_addr_r}" && test -n "${ramdisk_addr_r}"; then
    if load nvme ${fw_dev_part} ${kernel_addr_r} aurora/j773g-gpu-inspection-usb2/Image && load nvme ${fw_dev_part} ${fdt_addr_r} aurora/j773g-gpu-inspection-usb2/kernel-target.dtb && load nvme ${fw_dev_part} ${ramdisk_addr_r} aurora/j773g-gpu-inspection-usb2/initramfs.cpio.gz; then
        setenv inspection_initrd_size ${filesize}
        setenv skip_board_fixup 0
        setenv bootargs 'console=tty0 loglevel=7'
        booti ${kernel_addr_r} ${ramdisk_addr_r}:${inspection_initrd_size} ${fdt_addr_r}
    else
        echo Diagnostic files could not be loaded; no diagnostic boot attempted.
    fi
else
    echo ESP PARTUUID or loader addresses do not match; no diagnostic boot attempted.
fi
