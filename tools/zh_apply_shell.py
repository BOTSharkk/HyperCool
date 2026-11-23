#!/usr/bin/env python3
"""Apply the Simplified Chinese localization to shell-side user-facing text.

This covers system notifications, the module description shown by KernelSU,
the installer output and the action-button report. It is idempotent: running it
again after an upstream merge re-applies the same replacements.

Usage:
    python3 tools/zh_apply_shell.py            # apply and report
    python3 tools/zh_apply_shell.py --check    # report only, change nothing

Strings that are parsed by the WebUI (for example the "Kept awake by <pkg>"
line in Recent activity) are intentionally left in English.
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RULES = {
    "module.prop": [
        ("description=Heat and battery fix for Android - Device: Qualcomm | MediaTek (one-shot at boot, only tiny opt-in keepers). Configure in WebUI, then reboot. Telegram Channel: @ModuleArchives.",
         "description=HyperCool 温控与续航 - 设备：Qualcomm | MediaTek（开机一次性应用，仅少量可选守护）。在 WebUI 中配置后重启。Telegram 频道：@ModuleArchives。"),
    ],
    "customize.sh": [
        ('ui_print "  HyperCool - Heat & Battery Fix"', 'ui_print "  HyperCool - 温控与续航"'),
        ('ui_print "  one-shot at boot | tiny opt-in keepers only"',
         'ui_print "  开机一次性应用 | 仅少量可选守护"'),
        ('ui_print "- Device : $(getprop ro.product.marketname) ($_dev)"',
         'ui_print "- 设备   : $(getprop ro.product.marketname) ($_dev)"'),
        ('ui_print "- SoC    : ${_soc:-unknown} $_model${_plat:+ (platform $_plat)}"',
         'ui_print "- SoC    : ${_soc:-未知} $_model${_plat:+ (平台 $_plat)}"'),
        ('ui_print "- SoC    : ${_soc:-unknown} ${_plat:+($_plat)}"',
         'ui_print "- SoC    : ${_soc:-未知} ${_plat:+($_plat)}"'),
        ('ui_print "  Xiaomi-only options (night charging, Joyose,"',
         'ui_print "  仅小米可用的选项（夜间充电、Joyose、"'),
        ('ui_print "  autostart, MIUI blur) will be skipped."',
         'ui_print "  自启动、MIUI 模糊）将被跳过。"'),
        ('ui_print "- Qualcomm kernel features available"',
         'ui_print "- 可使用 Qualcomm 内核功能"'),
        ('ui_print "- MediaTek kernel features available"',
         'ui_print "- 可使用 MediaTek 内核功能"'),
        ('ui_print "  (CPU cap with PPM, Mali GPU, perfmgr touch boost, UFS)"',
         'ui_print "  （PPM CPU 上限、Mali GPU、perfmgr 触控提频、UFS）"'),
        ('ui_print "! Unknown SoC: most kernel features will"',
         'ui_print "! 未知 SoC：大部分内核功能将"'),
        ('ui_print "! show Unsupported, system features still work."',
         'ui_print "! 显示为“不支持”，系统功能仍可使用。"'),
        ('_lbl="Device: Qualcomm✓ | MediaTek"', '_lbl="设备：Qualcomm✓ | MediaTek"'),
        ('_lbl="Device: Qualcomm | MediaTek✓"', '_lbl="设备：Qualcomm | MediaTek✓"'),
        ('description=Heat and battery fix for Android - ${_lbl:-Device: Qualcomm | MediaTek} (one-shot at boot, only tiny opt-in keepers). Configure in WebUI, then reboot. Telegram Channel: @ModuleArchives.',
         'description=HyperCool 温控与续航 - ${_lbl:-设备：Qualcomm | MediaTek}（开机一次性应用，仅少量可选守护）。在 WebUI 中配置后重启。Telegram 频道：@ModuleArchives。'),
        ('abort "! Android 11 or newer is required"', 'abort "! 需要 Android 11 或更高版本"'),
        ('ui_print "- Existing config kept, merging new options"',
         'ui_print "- 保留现有配置，合并新选项"'),
        ('ui_print "- Migrating v1.0 config values"', 'ui_print "- 正在迁移 v1.0 配置值"'),
        ('ui_print "- Wakelock list: removed notification wakelocks from the old default"',
         'ui_print "- 唤醒锁列表：已从旧默认值中移除通知类唤醒锁"'),
        ('ui_print "- Battery input defaults updated (your own values are kept)"',
         'ui_print "- 电池输入默认值已更新（你自行修改的值会保留）"'),
        ('ui_print "- Installing default config"', 'ui_print "- 安装默认配置"'),
        ('ui_print "- KernelSU $KSU_VER detected"', 'ui_print "- 检测到 KernelSU $KSU_VER"'),
        ('ui_print "- Open the WebUI to choose features, then reboot."',
         'ui_print "- 打开 WebUI 选择功能，然后重启。"'),
        ('ui_print "- Every option is applied once per boot."',
         'ui_print "- 所有选项每次开机会应用一次。"'),
    ],
    "service.sh": [
        ('_hgrun=", heat guard running"', '_hgrun="，温度守护运行中"'),
        ('_desc="Heat and battery fix for Android - $(hc_soc_label) (one-shot at boot',
         '_desc="HyperCool 温控与续航 - $(hc_soc_label)（开机一次性应用'),
        (', charge-limit keeper running', '，充电上限守护运行中'),
        (', screen-off keeper running', '，熄屏守护运行中'),
        (')). Last boot: $_a applied, $_p partial, $_s unsupported, $_f failed, $_o off. Configure in WebUI. Telegram Channel: @ModuleArchives."',
         ')）。上次开机：$_a 项已应用，$_p 项部分应用，$_s 项不支持，$_f 项失败，$_o 项关闭。在 WebUI 中配置。Telegram 频道：@ModuleArchives。"'),
        ('_nm="HyperCool applied successfully: $((_a + _p)) features active. Less heat, longer battery!"',
         '_nm="HyperCool 已成功应用：$((_a + _p)) 项功能生效。更少发热，更长续航！"'),
        ('_nm="HyperCool applied: $((_a + _p)) features active, $_f failed. Open the WebUI for details."',
         '_nm="HyperCool 已应用：$((_a + _p)) 项功能生效，$_f 项失败。打开 WebUI 查看详情。"'),
    ],
    "post-fs-data.sh": [
        ('description=SAFE MODE: HyperCool switched itself off after 3 boots that did not finish ($_sd). Turn it on again in the manager to use it.',
         'description=安全模式：HyperCool 连续 3 次开机未完成，已自动停用（$_sd）。在管理器中重新启用后即可使用。'),
    ],
    "common/functions.sh": [
        ('qcom) echo "Device: Qualcomm✓ | MediaTek" ;;', 'qcom) echo "设备：Qualcomm✓ | MediaTek" ;;'),
        ('mtk) echo "Device: Qualcomm | MediaTek✓" ;;', 'mtk) echo "设备：Qualcomm | MediaTek✓" ;;'),
        ('*) echo "Device: Qualcomm | MediaTek" ;;', '*) echo "设备：Qualcomm | MediaTek" ;;'),
    ],
    "common/cache_clean.sh": [
        ('notify "App cache cleaned: ', 'notify "应用缓存已清理：从 ${_ap:-0} 个应用清理 '),
        (' from ${_ap:-0} apps"', '"'),
    ],
    "common/bcal_watch.sh": [
        ('klog calibration "Battery calibration" "$1"', 'klog calibration "电池校准" "$1"'),
        ('notify "Battery calibration: battery at ${_l}%. Plug in the charger now and charge to 100% without unplugging."',
         'notify "电池校准：电量 ${_l}%。请现在插上充电器，并一直充到 100%，中途不要拔掉。"'),
        ('notify "Battery calibration: battery at 100%. Keep the charger plugged in until charging finishes (at most 1 h), HyperCool tells you when."',
         'notify "电池校准：电量 100%。请保持充电器连接直到充电完成（最多 1 小时），完成后 HyperCool 会通知你。"'),
        ('notify "Battery calibration: charging stopped at ${_l}%. Plug the charger back in and charge to 100% without unplugging."',
         'notify "电池校准：充电在 ${_l}% 中断。请重新插上充电器，并一直充到 100%，中途不要拔掉。"'),
        ('notify "Battery calibration done. You can unplug the charger now."',
         'notify "电池校准完成，现在可以拔掉充电器了。"'),
    ],
    "common/soff_watch.sh": [
        ('_dmsg="Screen-off drain was ${_dr}%/h (${_dd}% in ${_dh} h)."',
         '_dmsg="熄屏耗电为 ${_dr}%/小时（${_dh} 小时内耗电 ${_dd}%）。"'),
        ('_dmsg="$_dmsg The app with the most wake lock time: $_dtp ($_dtm min)."',
         '_dmsg="$_dmsg 唤醒锁时间最长的应用：$_dtp（$_dtm 分钟）。"'),
        ('_dmsg="$_dmsg Open HyperCool, Wake sources to see what kept the phone awake."',
         '_dmsg="$_dmsg 打开 HyperCool 的“唤醒来源”查看是什么让手机保持唤醒。"'),
    ],
    "common/dexopt.sh": [
        ('_msg="Reset $_ok apps to default."', '_msg="已将 $_ok 个应用恢复默认。"'),
        ('_msg="Optimized $_ok apps."', '_msg="已优化 $_ok 个应用。"'),
        ('_msg="$_msg $_fl failed."', '_msg="$_msg $_fl 个失败。"'),
        ('_msg="$_msg ${_min} min."', '_msg="$_msg 用时 ${_min} 分钟。"'),
        ('_msg="Stopped: battery low or not readable. $_dn of $TOTAL apps done."',
         '_msg="已停止：电量低或无法读取。已完成 $_dn/$TOTAL 个应用。"'),
        ('_msg="Stopped: storage almost full or not readable. $_dn of $TOTAL apps done."',
         '_msg="已停止：存储空间不足或无法读取。已完成 $_dn/$TOTAL 个应用。"'),
        ('_msg="Stopped: battery too warm or the temperature is not readable. $_dn of $TOTAL apps done."',
         '_msg="已停止：电池温度过高或温度无法读取。已完成 $_dn/$TOTAL 个应用。"'),
        ('_msg="Stopped: screen turned on. $_dn of $TOTAL apps done."',
         '_msg="已停止：屏幕亮起。已完成 $_dn/$TOTAL 个应用。"'),
        ('_msg="Stopped. $_dn of $TOTAL apps done."', '_msg="已停止。已完成 $_dn/$TOTAL 个应用。"'),
        ('_msg="Auto optimize: $_msg"', '_msg="自动优化：$_msg"'),
        ('klog screen-off "App optimization (auto)"', 'klog screen-off "应用优化（自动）"'),
        ('klog tools "App optimization (manual)"', 'klog tools "应用优化（手动）"'),
    ],
    "common/f2gc.sh": [
        ('if [ "$_gns" -lt 90 ]; then _gnt="${_gns} s"; else _gnt="$(((_gns + 30) / 60)) min"; fi',
         'if [ "$_gns" -lt 90 ]; then _gnt="${_gns} 秒"; else _gnt="$(((_gns + 30) / 60)) 分钟"; fi'),
        ('_gnm="F2FS cleanup done: reclaimable space ${_gnb} GB to ${_gna} GB in ${_gnt}"',
         '_gnm="F2FS 清理完成：可回收空间从 ${_gnb} GB 变为 ${_gna} GB，用时 ${_gnt}"'),
        ('_gnm="$_gnm, fstrim done"', '_gnm="$_gnm，fstrim 完成"'),
        ('_gnm="F2FS cleanup stopped, battery low: reclaimable space ${_gnb} GB to ${_gna} GB"',
         '_gnm="F2FS 清理已停止，电量低：可回收空间从 ${_gnb} GB 变为 ${_gna} GB"'),
        ('_gnm="F2FS cleanup stopped, battery too warm: reclaimable space ${_gnb} GB to ${_gna} GB"',
         '_gnm="F2FS 清理已停止，电池温度过高：可回收空间从 ${_gnb} GB 变为 ${_gna} GB"'),
        ('_gnm="F2FS cleanup stopped, screen turned on: reclaimable space ${_gnb} GB to ${_gna} GB"',
         '_gnm="F2FS 清理已停止，屏幕亮起：可回收空间从 ${_gnb} GB 变为 ${_gna} GB"'),
        ('_gnm="F2FS cleanup could not start: this kernel did not accept gc_urgent"',
         '_gnm="F2FS 清理无法启动：此内核不接受 gc_urgent"'),
        ('klog screen-off "F2FS cleanup (auto)" "${_gnm#F2FS cleanup }"',
         'klog screen-off "F2FS 清理（自动）" "${_gnm#F2FS 清理 }"'),
    ],
    "action.sh": [
        ('echo "=== HyperCool - last boot report ==="', 'echo "=== HyperCool - 上次开机报告 ==="'),
        ('echo "Applied at: $(cat "$HC_DATA/last_boot")"', 'echo "应用时间：$(cat "$HC_DATA/last_boot")"'),
        ('echo "No report yet - reboot once after installing."', 'echo "暂无报告 - 安装后请重启一次。"'),
        ('echo "Open the WebUI to change options. Changes apply after reboot."',
         'echo "打开 WebUI 修改选项，重启后生效。"'),
    ],
}


def main():
    ap = argparse.ArgumentParser(description="Apply zh-CN shell text to HyperCool")
    ap.add_argument("--check", action="store_true", help="report only, do not write files")
    args = ap.parse_args()

    missing = []
    changed = 0
    already = 0
    for rel, rules in RULES.items():
        path = os.path.join(ROOT, rel)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        original = text
        for old, new in rules:
            if old in text:
                text = text.replace(old, new)
                changed += 1
            elif new in text:
                already += 1
            else:
                missing.append(f"{rel}: {old[:90]}")
        if text != original and not args.check:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
    print(f"applied {changed}, already {already}, missing {len(missing)}")
    for m in missing:
        print("MISSING", m)
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
