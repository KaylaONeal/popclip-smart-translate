"use strict";

const axiosModule = require("axios");
const http = axiosModule.default || axiosModule;
const core = require("./core.js");
const categories = require("./prompts.json");
const languages = require("./langs.json").translation;
const preferredLanguages = ["zh-Hans", "zh-Hant", "en", "ja", "ko", "de", "fr", "es"];
const codes = preferredLanguages.concat(Object.keys(languages)
  .filter(code => !preferredLanguages.includes(code))
  .sort((a, b) => languages[a].name.localeCompare(languages[b].name)));

exports.options = [
  { identifier: "engine", label: "默认翻译引擎", type: "multiple", defaultValue: "llm",
    values: ["original", "llm"], valueLabels: ["原有翻译 · Microsoft", "大模型 · DeepSeek / 兼容 API"],
    description: "按住 ⌥ 点击翻译图标，可临时使用另一个引擎。两种方式都需要联网。" },
  { identifier: "destlang", label: "翻译为", type: "multiple", defaultValue: "zh-Hans", values: codes,
    valueLabels: codes.map(code => languages[code].nativeName + " / " + languages[code].name) },
  { identifier: "category", label: "翻译类别（大模型）", type: "multiple", defaultValue: "general",
    values: categories.map(item => item.id), valueLabels: categories.map(item => item.label) },
  { identifier: "baseurl", label: "API 地址", type: "string", defaultValue: "https://api.deepseek.com",
    description: "填写 HTTPS Base URL，也可直接填写完整的 /chat/completions 地址。" },
  { identifier: "apipath", label: "API Path", type: "string", defaultValue: "/chat/completions",
    description: "兼容 Chat Completions；API 地址已含 /chat/completions 时忽略此项。" },
  { identifier: "model", label: "模型名称", type: "string", defaultValue: "deepseek-flash" },
  { identifier: "apikey", label: "API Key", type: "secret", keychain: "local",
    description: "由 PopClip 保存到 macOS 钥匙串。切换服务商时请同时更换地址、模型和 Key。" },
  { identifier: "customprompt", label: "补充翻译要求（可选）", type: "string", defaultValue: "",
    description: "叠加到所选类别，例如：保留英文专业术语，使用简洁书面语。" },
  { identifier: "microsoft", label: "原有翻译（本机迁移后无需填写）", type: "heading" },
  { identifier: "microsoftkey", label: "Microsoft Key（可选）", type: "secret", keychain: "local",
    description: "留空时复用本机原 Instant Translate 的凭据。" },
  { identifier: "microsoftregion", label: "Microsoft 区域（可选）", type: "string", defaultValue: "",
    description: "仅使用自己的区域型 Microsoft Key 时填写，例如 eastasia。" }
];

function getLegacyKey() {
  // Only the private local installation package contains this file. Never include it in source control.
  const access = require("./access.json");
  return util.clarify(access.access).key;
}

exports.action = async (input, options) => {
  try {
    return await core.translate(input.text, options, { http, getLegacyKey }, popclip.modifiers.option);
  } catch (error) {
    // Errors are notifications, never text returned to the preview/paste pipeline.
    popclip.showText(error.translationMessage || "翻译失败，请检查设置后重试。");
  }
};
