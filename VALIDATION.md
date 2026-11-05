# 当前验收

日期：2026-11-05。验收环境：macOS，PopClip 2024.3.2（build 4516）。

- `npm test`：涵盖 DeepSeek 请求格式、其他兼容端点、URL/Path 合并、八种领域提示词、目标语言、默认/临时引擎切换、长文本、首尾空白保留，以及认证/限流/超时/截断/空响应。发布检查共 14 项。
- `npm run test:package`：4 项打包检查，包含凭据污染文件排除、两次构建字节一致、私有迁移权限与语言、损坏配置兼容及缺失凭据拒绝。
- `npm run test:native`：在本机 PopClip JavaScriptCore 中加载完整源码及内置 Axios 成功，合成请求返回通过。旧版 `runjs` 无法解析项目模块，因此测试脚本只在测试时内联本地模块；扩展仍按原生模块安装。
- `scripts/native_test.py --package <已安装扩展目录> --live-microsoft`：调用扩展的实际 `main.action` 入口，经 PopClip 自带网络运行时实际请求 Microsoft；选区与修饰键使用测试桥接。测试原文 `The GPU processes data in parallel.`，返回 `GPU是并行处理数据的。`。
- 普通安装包限定 6 个源码/声明文件，不含 `access.json`；本机迁移包目录权限 0700，安装包及旧凭据文件权限 0600。原 Instant Translate 的配置与签名仍保留。
- DeepSeek：尚无本任务的真实 API Key；协议、提示词和失败路径已验，真实模型返回未验。
- 界面：已安装并启用，八类提示词、两种引擎、API 地址/Path/模型/保密 Key 字段已回读；旧扩展保留并停用。临时测试快捷键已恢复为未设置。
- 尚未验收：自动化选词没有触发系统级浮窗，因此不声称已完成“鼠标划词 → 点击翻译 → 预览粘贴”的全链路测试。可打开 `tests/manual-smoke.rtf` 手动完成该步骤。

## Review 修复与性能选择

- 保留模型输出的首尾空白，避免破坏缩进和 Markdown；仍用去空白检查拒绝空响应。
- 公开包默认走大模型，本机迁移包默认走原翻译，避免公开安装后误选缺少凭据的旧引擎。
- 迁移遇到损坏的偏好文件仍可构建，使用安全默认值；不覆盖用户保存的扩展选项。
- 固定 ZIP 元数据、按显式文件清单打包，生成 SHA-256；原服务凭据只进入私有目录中的迁移包。
- 直接用 PopClip 自带 Axios 请求，官方 DeepSeek 采用非思考模式；不引入后台进程、中转接口、额外请求或依赖包。未设置持久译文缓存，避免把选中文字落盘。

入口：[README](README.md)、[核心实现](SmartTranslate.popclipext/core.js)、[本机测试工具](scripts/native_test.py)。
