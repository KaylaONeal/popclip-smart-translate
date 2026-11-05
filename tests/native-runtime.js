// Runs in PopClip's actual JavaScriptCore environment, with a synthetic transport.
const core = require("./core.js");
const main = require("./main.js");
const options = {};
main.options.forEach(option => { if (option.defaultValue !== undefined) options[option.identifier] = option.defaultValue; });
options.engine = "llm";
options.apikey = "synthetic-key-only";
options.category = "technology";
const http = { post: async (url, body, config) => {
  if (url !== "https://api.deepseek.com/chat/completions") throw new Error("URL mismatch");
  if (body.model !== "deepseek-flash" || body.thinking.type !== "disabled") throw new Error("Body mismatch");
  if (config.timeout !== 60000) throw new Error("Timeout mismatch");
  return { data: { choices: [{ message: { content: "原生运行时通过" }, finish_reason: "stop" }] } };
} };
return core.translate("GPU architecture", options, { http }).then(result => {
  if (result !== "原生运行时通过") throw new Error("Result mismatch");
  print("PASS native PopClip runtime; options=" + main.options.length + "; language=" + options.destlang);
});
