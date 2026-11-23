#!/system/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Yudharn
# HyperCool - Action button: print last boot report (read-only)
HC_DATA=/data/adb/hypercool
echo "=== HyperCool - 上次开机报告 ==="
[ -f "$HC_DATA/last_boot" ] && echo "应用时间：$(cat "$HC_DATA/last_boot")"
echo ""
if [ -f "$HC_DATA/status.conf" ]; then
  while IFS='=' read -r k rest; do
    [ -n "$k" ] || continue
    state=${rest%%\|*}
    det=${rest#*\|}
    printf '%-16s %-8s %s\n' "$k" "$state" "$det"
  done < "$HC_DATA/status.conf"
else
  echo "暂无报告 - 安装后请重启一次。"
fi
echo ""
echo "打开 WebUI 修改选项，重启后生效。"
