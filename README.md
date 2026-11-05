# PopClip 智能翻译

原生 PopClip 扩展：选择文字后直接调用 DeepSeek / Chat Completions 兼容模型，或使用原 Instant Translate 的 Microsoft 翻译。

[下载安装包](https://github.com/KaylaONeal/popclip-smart-translate/releases/latest/download/SmartTranslate.popclipextz) · [版本发布](https://github.com/KaylaONeal/popclip-smart-translate/releases) · [验收与限制](VALIDATION.md)

## 使用

1. 双击生成的 `SmartTranslate.popclipextz`，在 PopClip 中安装“智能翻译”。
2. 打开 PopClip → Extensions → 智能翻译右侧设置按钮。
3. 选择默认引擎、目标语言、翻译类别。
4. 使用大模型时填写 API 地址、Path、模型名称和 API Key。
5. 选中文字，点击“译”图标，预览译文后可点击粘贴。按住 **⌥ Option** 点击图标，临时使用另一个引擎。

公开安装包默认使用大模型、简体中文、通用类别，需要填写自己的 API Key。本机迁移包默认使用原有 Microsoft 翻译，并沿用旧插件的目标语言。安装新扩展后可取消勾选原来的 Instant Translate，随时可重新启用。

### DeepSeek 配置

| 设置 | 值 |
| --- | --- |
| 默认翻译引擎 | 大模型 · DeepSeek / 兼容 API |
| API 地址 | `https://api.deepseek.com` |
| API Path | `/chat/completions` |
| 模型名称 | `deepseek-flash` |
| API Key | 在 PopClip 的保密字段中填写自己的 Key |

当前默认模型名依据 [DeepSeek 官方文档](https://api-docs.deepseek.com/)（2026-11-05 核对）。官方 DeepSeek 接口使用非思考模式降低等待时间。也可自行填写其他模型名。

其他服务支持 `https://服务商/v1` + `/chat/completions`，也支持完整的 `https://服务商/v1/chat/completions`。完整地址优先；不会重复追加 `/v1`。接口须兼容 Chat Completions 的请求和 `choices[0].message.content` 返回格式，并使用 HTTPS。切换服务商时同时更新地址、模型和 Key。

### 提示词与输出

- 类别：通用、科技/软件、商务/邮件、金融/投资、学术/论文、医学/健康、法律/合同、日常/社交。
- “补充翻译要求”可追加术语或风格要求；只影响大模型翻译。
- 自动识别原文语言，按“翻译为”选择的目标语言输出；保留段落、Markdown、代码、数字和单位。
- 单次最多 20,000 个字符；请求超时 60 秒。不自动重试或切换服务。接口限流、认证失败、余额不足、截断或空输出会给出中文提示。
- 原生 PopClip 预览只显示译文开头；点击预览粘贴的是完整译文。错误提示不会被当成译文返回。

## 构建与验证

运行环境：PopClip 2024.3（build 4508）或更新版本；开发测试使用 Node.js，打包使用 Python 3。扩展运行时使用 PopClip 自带 JavaScriptCore 和 Axios，无后台进程、额外端口或外部运行时依赖。

```sh
npm test
npm run test:package
npm run build
npm run build:local
npm run test:native
```

- `build`：生成 `dist/SmartTranslate.popclipextz` 及 `.sha256` 校验文件，不含任何凭据；需填写大模型 Key 或自己的 Microsoft Key。相同源码生成字节一致的安装包。
- `build:local`：从本机已安装的 Instant Translate 读取旧凭据和目标语言，在 `~/Library/Application Support/PopClipSmartTranslate/<时间>/` 生成权限受限的本机安装包。**迁移包含旧服务凭据，不要分享。** 不改动原扩展或原设置。
- 大模型 Key 使用 PopClip 的 `secret` 字段保存到 macOS 钥匙串。源码、测试、日志和公开构建包不保存 Key 或翻译内容。
- 原有翻译是 Microsoft 在线服务，并非离线翻译；它的内置凭据是否有效由原服务维护方决定。可填写自己的 Microsoft Key 和区域。

校验下载文件：在下载目录执行 `shasum -a 256 -c SmartTranslate.popclipextz.sha256`。

原生测试脚本针对 PopClip 2024.3 的 `runjs` 调试接口；较新的 PopClip 已调整该调试接口，但不影响扩展运行。该脚本使用模拟的选区/修饰键桥接和真实 JavaScriptCore/Axios，不替代实际划词预览验收。

## 实现

- `SmartTranslate.popclipext/main.js`：原生设置、入口、预览及错误提示。
- `core.js`：请求、地址规范化、引擎切换、超时与结果校验。
- `prompts.json`：八种领域提示词，直接修改即可扩展。
- `scripts/build.py`：无凭据构建及本机私有迁移。
- `tests/translation.test.js`：请求协议、路径、领域提示词、引擎切换和失败路径测试。

语言列表来自 Instant Translate（原作者 harmy，后续维护 chenggiant、Nick Moore）。[上游许可与署名](SmartTranslate.popclipext/NOTICE.txt) 随安装包保留。翻译逻辑重新实现；原扩展的签名未沿用。

参考：[PopClip 扩展设置](https://www.popclip.app/dev/options)、[PopClip 包格式](https://www.popclip.app/dev/packages)、[DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)。
