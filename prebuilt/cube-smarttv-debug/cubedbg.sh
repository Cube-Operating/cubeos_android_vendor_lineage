#!/system/bin/sh
# Cube SmartTV DEBUG ONLY (remove before any release): save cubeOS's boot log to the TV's `cache`
# partition, which the USB rescue package never touches, so it can be read back from stock Android.
#   /cache/cubeos-boot/boot-N/{dmesg,logcat,props,ps,heartbeat}.txt, pstore-prev/ (last boot's kernel tail)
# If boot hasn't completed after 240 s on the FIRST boot, warm-reboot once so the kernel's ramoops
# keeps the hung boot's console log for boot 2 to copy.
D=/dev/cubedbg
mkdir -p $D
i=0
until mountpoint -q $D; do
    for dev in /dev/block/by-name/cache /dev/block/platform/soc/f9830000.emmc/by-name/cache /dev/block/mmcblk0p25; do
        [ -b $dev ] && mount -t ext4 -o rw,nosuid,nodev,noatime $dev $D 2>/dev/null && break
    done
    i=$((i + 1)); [ $i -gt 120 ] && exit 1
    sleep 1
done
B=$D/cubeos-boot
mkdir -p $B
c=$(cat $B/count 2>/dev/null); c=$((${c:-0} + 1)); echo $c > $B/count
O=$B/boot-$c
mkdir -p $O
cp -r /sys/fs/pstore $O/pstore-prev 2>/dev/null
cat /proc/cmdline > $O/cmdline.txt
cat /proc/mounts > $O/mounts-early.txt
t=0
while :; do
    dmesg > $O/dmesg.txt 2>&1
    logcat -d -b all -v uptime > $O/logcat.txt 2>&1
    getprop > $O/props.txt 2>&1
    ps -A > $O/ps.txt 2>&1
    cat /proc/mounts > $O/mounts.txt
    echo "t=$t uptime=$(cat /proc/uptime)" > $O/heartbeat.txt
    sync
    if [ "$(getprop sys.boot_completed)" = 1 ]; then echo booted > $O/booted.txt; sync; break; fi
    t=$((t + 5))
    if [ $t -ge 240 ] && [ $c -le 1 ] && [ ! -f $O/rebooted.txt ]; then
        echo "no boot_completed after ${t}s: warm reboot to keep ramoops" > $O/rebooted.txt
        sync
        echo b > /proc/sysrq-trigger
    fi
    sleep 5
done
