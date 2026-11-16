# HyperCool - Heat & Battery Fix

[English](README.en.md) | **简体中文**

![HyperCool](banner.jpg)

适用于 高通 和 联发科 手机的 KernelSU / Magisk 模块。更少发热、更低耗电、更长续航。
专注续航，而非峰值性能。

<p align="center">
  <a href="https://github.com/yudharn/HyperCool/releases"><img alt="下载量" src="docs/badges/downloads.svg"></a>
  <a href="https://github.com/yudharn/HyperCool/stargazers"><img alt="Star" src="docs/badges/stars.svg"></a>
  <img alt="Android 11+" src="docs/badges/android.svg" />
  <a href="https://github.com/yudharn/HyperCool/releases/latest"><img alt="最新版本" src="docs/badges/release.svg"></a>
</p>

所有设置都在 WebUI 中完成，并在下次开机时一次性生效。除你主动开启的小型守护进程外，不会有任何常驻服务：
充电上限、熄屏守护（同时负责熄屏保持 Wi-Fi）、压缩后台应用、长时间熄屏关闭定位和蓝牙、F2FS 垃圾回收与自动应用优化、自动清理缓存、CPU 守护、自适应刷新率、电池校准。

`每项功能在 WebUI 中都有独立开关；更改在开机时生效，关闭功能（或卸载模块）会恢复原始值`

## 截图

<table align="center">
  <tr>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/home.jpg" alt="首页" width="200" /><br />
      <b>首页</b>
    </td>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/heat-control.jpg" alt="温控" width="200" /><br />
      <b>温控</b>
    </td>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/battery-drain.jpg" alt="耗电控制（内核）" width="200" /><br />
      <b>耗电控制（内核）</b>
    </td>
  </tr>
  <tr>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/protected-apps.jpg" alt="应用保护与限制" width="200" /><br />
      <b>应用保护</b>
    </td>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/battery-calibration.jpg" alt="电池校准" width="200" /><br />
      <b>电池校准</b>
    </td>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/long-battery.jpg" alt="续航增强" width="200" /><br />
      <b>续航增强</b>
    </td>
  </tr>
  <tr>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/advanced.jpg" alt="高级与实验性" width="200" /><br />
      <b>高级</b>
    </td>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/extra-kernel-tuning.jpg" alt="内核进阶调校" width="200" /><br />
      <b>内核进阶调校</b>
    </td>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/ram-management.jpg" alt="内存管理" width="200" /><br />
      <b>内存管理</b>
    </td>
  </tr>
  <tr>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/google-services.jpg" alt="Google 服务与遥测" width="200" /><br />
      <b>Google 服务</b>
    </td>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/storage.jpg" alt="存储" width="200" /><br />
      <b>存储</b>
    </td>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/app-cache.jpg" alt="应用缓存与优化应用" width="200" /><br />
      <b>应用缓存</b>
    </td>
  </tr>
  <tr>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/appearance-status.jpg" alt="外观与配置" width="200" /><br />
      <b>工具</b>
    </td>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/extra-power-saving.jpg" alt="额外省电" width="200" /><br />
      <b>额外省电</b>
    </td>
    <td align="center" valign="top">
      <img src="docs/screenshots/zh/battery-drain-system.jpg" alt="耗电控制（系统）" width="200" /><br />
      <b>耗电控制（系统）</b>
    </td>
  </tr>
</table>

## 功能

**温控**
- 大核频率上限（带锁定）
- 小核频率上限（默认关闭，带锁定）
- GPU 频率上限（来自本机 GPU 频率表，带锁定）
- GPU 电源收缩
- 降低 CPU 调度器激进程度（WALT / schedutil）
- 关闭内核触控提频
- 后台应用仅使用小核
- 停用超大核（Qualcomm；内核关闭 core_ctl 时自动开启，并验证核心确实已停用、锁定节点）
- CPU 守护：ROM 撤销限制时重新应用大/小核上限和超大核停用
- 关闭界面模糊
- 更凉爽的充电（限流）与约 80% 充电上限（小米）

**耗电控制（内核）**
- 自适应熄屏省电配置
- CPU 深度休眠、UFS 省电
- 减少回写唤醒、减少 I/O 统计
- 关闭内核调试、内核唤醒锁拦截
- 熄屏期间保持 Wi-Fi（ROM 关闭后自动重开；你手动关闭的 Wi-Fi 保持关闭）
- 长时间熄屏后关闭定位和蓝牙（亮屏后恢复；默认关闭）
- 熄屏时执行 F2FS 垃圾回收（存储；回收只有 GC 能释放的空间；最多每周一次，无需充电；默认关闭）
- 熄屏时每周自动优化应用（dex2oat）（存储；speed-profile，不强制重新编译，完成后通知；默认关闭）
- 耗电排行（首页；只读：用户应用、系统应用、系统服务和硬件，数据来自 Android 电池统计）

**应用**
- 保持重要应用存活
- 限制其他用户应用
- 阻止应用后台运行
- 禁用应用（请谨慎选择）

**耗电控制（系统）**
- 缓存应用冻结、强力 Doze、GMS Doze
- 关闭 Wi-Fi/蓝牙扫描、限制后台定位、网络待机省电
- 应用待机、减少统计、关闭遥测
- 禁用分析和广告包、关闭 Joyose、减少日志
- 熄屏一段时间后关闭移动数据和 NFC，亮屏自动恢复（默认关闭）

**续航增强**
- 更强的省电模式、自动省电档位
- 省电模式下降低屏幕亮度、Smart Pixels（支持的系统）
- 刷新率上限、自适应刷新率（触控时高、空闲时低）、动画缩放

**扩展**
- 调度器、网络和 I/O 调校
- 关闭 MiGT / Metis（小米）
- 均衡系统默认值、通用内核调校
- 内存优化、多任务配置
- ZRAM 大小与压缩（2-8 GB，或自定义最高 12 GB）
- 冻结 GMS 广告/分析、关闭更多遥测
- 清理日志、关闭厂商诊断
- 内核省电开关、能量感知调度器
- 空闲 USB / I2C / SPI 设备省电（需手动开启）
- 减少后台任务：JobScheduler 将后台工作批量推迟 1-2 小时（均衡 / 强力，会回读，ROM 忽略时恢复原值）
- 压缩后台应用：熄屏后且可用内存较低时压缩后台应用内存
- 自动清理应用缓存（每 1-7 天）、保留缓存的应用白名单、缓存清理通知
- 优化应用（dex2oat）：为所有应用提供实时进度（扩展页，按需运行）
- 全部应用完成后发送开机通知

**工具**
- 单色主题（中性黑白外观、系统字体、圆角卡片和列表）
- 深色 / AMOLED / 主题色、模糊顶栏
- 备份、还原、导入设置，开机日志，错误报告，立即还原，重启

**首页**
- 搜索：按名称查找任意功能并跳转
- 待机耗电：自上次拔出充电器以来熄屏时每小时的耗电（下降 1% 后显示）
- 电池检测：健康度、容量、循环次数、温度等
- 电池校准：引导完成一次完整循环（5% → 100% → 直到充电完成），让电量百分比更准确（可选同时删除 batterystats.bin）

每项功能都会显示它更改了什么，以及上次开机的执行结果。
关闭功能会恢复原始值。不支持的功能会被跳过。

## 要求
- Android 11+
- KernelSU、KernelSU Next 或 APatch（Magisk：使用 MMRL 或 KsuWebUI 打开 WebUI）
- 高通 或 联发科 SoC，任意 ROM

## 文件
- `/data/adb/hypercool/config.conf` 设置
- `/data/adb/hypercool/status.conf` 上次开机结果
- `/data/adb/hypercool/boot.log` 日志
- `sh /data/adb/hypercool/restore.sh --all` 手动恢复所有系统更改

## 致谢
- Frosty by Drsexo
- Power Saver Pro by @ShastikXD & @TempMeow（部分代码来自 @kveld9）
- Hyper Optimize by Tatsh
- Xtreme Battery Saver（DethByte64）、Universal GMS Doze、sysconfig-patcher

## 支持

> [!NOTE]
> 如果 HyperCool 对你有帮助，欢迎支持开发：
>
> <a href="https://ko-fi.com/yudharn"><img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="在 Ko-fi 上支持我"></a>

其他支持方式：[SociaBuzz](https://sociabuzz.com/yudharn) · [QRIS](https://t.me/ArchivesModules/1476)

<a href="https://t.me/ModuleArchives"><img src="docs/badges/telegram.svg" alt="Telegram 频道" height="30"></a>

## 免责声明
HyperCool 会修改内核和系统设置。请自行承担风险；作者不对开机循环、数据丢失或设备损坏负责。
请先备份，出现异常时逐项关闭功能。本模块不提供任何担保（详见 GPL）。

## 许可证
GPL-3.0-or-later。版权所有 (C) 2026 Yudharn。参见 [LICENSE](LICENSE)。
修改版本必须继续使用 GPL-3.0、保持源码公开并保留此版权声明。
Google Sans 字体：SIL Open Font License（`webroot/GoogleSans-OFL.txt`）。
