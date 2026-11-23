#!/system/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Yudharn
# HyperCool - installer
# shellcheck disable=SC2034
SKIPUNZIP=0
HC_DATA=/data/adb/hypercool
. "$MODPATH/common/cfg_migrate.sh"

ui_print " "
ui_print "  HyperCool - 温控与续航"
ui_print "  开机一次性应用 | 仅少量可选守护"
ui_print " "

_dev=$(getprop ro.product.device)
_os=$(getprop ro.mi.os.version.name)
[ -z "$_os" ] && _os=$(getprop ro.miui.ui.version.name)
ui_print "- 设备   : $(getprop ro.product.marketname) ($_dev)"
ui_print "- Android: $(getprop ro.build.version.release) (API $API)"
_soc=$(getprop ro.soc.manufacturer)
_plat=$(getprop ro.board.platform)
# ro.board.platform is the shared platform name (SD 675/730/730G/732G all report sm6150)
_model=$(getprop ro.soc.model)
[ -z "$_model" ] && _model=$(cat /sys/devices/soc0/machine 2>/dev/null)
if [ -n "$_model" ] && [ "$_model" != "$_plat" ]; then
  ui_print "- SoC    : ${_soc:-未知} $_model${_plat:+ (平台 $_plat)}"
else
  ui_print "- SoC    : ${_soc:-未知} ${_plat:+($_plat)}"
fi
if [ -n "$_os" ]; then
  ui_print "- ROM    : HyperOS/MIUI $_os"
else
  ui_print "- ROM    : $(getprop ro.build.display.id)"
  ui_print "  仅小米可用的选项（夜间充电、Joyose、"
  ui_print "  自启动、MIUI 模糊）将被跳过。"
fi
_st=""
case "$_soc" in [Mm]ediatek*|MediaTek*|MTK) _st=mtk ;; QTI|[Qq]ualcomm*) _st=qcom ;; esac
if [ "$_st" = qcom ] || { [ -z "$_st" ] && { [ -d /sys/class/kgsl/kgsl-3d0 ] || echo "$_soc $_plat" | grep -qiE 'qti|qualcomm|qcom|msm|sm[0-9]|sdm|kona|lahaina|taro|kalama|pineapple|parrot|crow|bengal|holi|lito|trinket'; }; }; then
  ui_print "- 可使用 Qualcomm 内核功能"
  _lbl="设备：Qualcomm✓ | MediaTek"
elif [ "$_st" = mtk ] || [ -d /proc/ppm ] || [ -d /proc/perfmgr ] || echo "$_soc $_plat" | grep -qiE 'mediatek|mt[0-9]'; then
  ui_print "- 可使用 MediaTek 内核功能"
  ui_print "  （PPM CPU 上限、Mali GPU、perfmgr 触控提频、UFS）"
  _lbl="设备：Qualcomm | MediaTek✓"
else
  ui_print "! 未知 SoC：大部分内核功能将"
  ui_print "! 显示为“不支持”，系统功能仍可使用。"
fi
sed -i "s#^description=.*#description=HyperCool 温控与续航 - ${_lbl:-设备：Qualcomm | MediaTek}（开机一次性应用，仅少量可选守护）。在 WebUI 中配置后重启。Telegram 频道：@ModuleArchives。#" "$MODPATH/module.prop"

[ "$API" -lt 30 ] && abort "! 需要 Android 11 或更高版本"

mkdir -p "$HC_DATA/backup"

# Keep the user's config across updates; add any new keys with defaults.
if [ -f "$HC_DATA/config.conf" ]; then
  ui_print "- 保留现有配置，合并新选项"
  C="$HC_DATA/config.conf"
  if ! grep -q '^cfg_ver=' "$C"; then
    ui_print "- 正在迁移 v1.0 配置值"
    sed -i -e 's/^cpu_cap=1$/cpu_cap=95/' -e 's/^cpu_cap=2$/cpu_cap=88/' -e 's/^cpu_cap=3$/cpu_cap=80/' \
      -e 's/^charge_cool=1$/charge_cool=3000/' -e 's/^charge_cool=2$/charge_cool=2000/' -e 's/^charge_cool=3$/charge_cool=1500/' \
      -e 's/^doze_aggr=1$/doze_aggr=2/' "$C"
  fi
  if grep -qx 'wl_list=qcom_rx_wakelock;wlan_wow_wl;wlan_extscan_wl;netmgr_wl;NETLINK;IPA_WS;wlan_ipa;wlan_pno_wl;wcnss_filter_lock;IPCRTR_lpass_rx;hal_bluetooth_lock;sensor_ind' "$C"; then
    ui_print "- 唤醒锁列表：已从旧默认值中移除通知类唤醒锁"
    sed -i 's/^wl_list=.*/wl_list=wlan_pno_wl;wlan_extscan_wl;wcnss_filter_lock/' "$C"
  fi
  # v2.3.3 battery defaults: a value moves only while it still holds the old default,
  # so anything the user chose is kept exactly as it is
  hc_migrate_config "$C" && ui_print "- 电池输入默认值已更新（你自行修改的值会保留）"
  # make sure the last line ends with a newline before appending missing keys
  [ -s "$HC_DATA/config.conf" ] && [ -n "$(tail -c1 "$HC_DATA/config.conf")" ] && echo >> "$HC_DATA/config.conf"
  grep -E '^[a-z0-9_]+=' "$MODPATH/common/default.conf" | while IFS='=' read -r k v; do
    grep -q "^$k=" "$HC_DATA/config.conf" || echo "$k=$v" >> "$HC_DATA/config.conf"
  done
else
  ui_print "- 安装默认配置"
  cp -f "$MODPATH/common/default.conf" "$HC_DATA/config.conf"
fi
cp -f "$MODPATH/common/restore.sh" "$HC_DATA/restore.sh"
cp -f "$MODPATH/common/radio.sh" "$HC_DATA/radio.sh"
cp -f "$MODPATH/common/heat_watch.sh" "$HC_DATA/heat_watch.sh"
cp -f "$MODPATH/common/soff_restore.sh" "$HC_DATA/soff_restore.sh"
# guard: restores ROM changes even while the module is disabled (removes itself after uninstall)
mkdir -p /data/adb/service.d
cp -f "$MODPATH/common/hc_guard.sh" /data/adb/service.d/.hypercool_guard.sh
chmod 0755 /data/adb/service.d/.hypercool_guard.sh

if [ "$KSU" = "true" ]; then
  ui_print "- 检测到 KernelSU $KSU_VER"
fi

set_perm "$MODPATH/post-fs-data.sh" 0 0 0755
set_perm "$MODPATH/service.sh" 0 0 0755
set_perm "$MODPATH/uninstall.sh" 0 0 0755
set_perm "$MODPATH/action.sh" 0 0 0755
set_perm "$MODPATH/common/restore.sh" 0 0 0755
set_perm "$MODPATH/common/soff_restore.sh" 0 0 0755
set_perm "$MODPATH/common/charge_cal.sh" 0 0 0755
set_perm "$MODPATH/common/chg_watch.sh" 0 0 0755
set_perm "$MODPATH/common/soff_watch.sh" 0 0 0755
set_perm "$MODPATH/common/monet.sh" 0 0 0755
set_perm "$MODPATH/common/cache_clean.sh" 0 0 0755
set_perm "$MODPATH/common/cpu_watch.sh" 0 0 0755
set_perm "$MODPATH/common/dexopt.sh" 0 0 0755
set_perm "$MODPATH/common/hc_guard.sh" 0 0 0755

ui_print " "
ui_print "- 打开 WebUI 选择功能，然后重启。"
ui_print "- 所有选项每次开机会应用一次。"
ui_print " "
