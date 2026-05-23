const test = require("node:test");
const assert = require("node:assert/strict");

const {
  buildAnalyzeRequest,
  buildUserMessage,
  classifySurface,
  shouldBlockPaste,
  shouldWarnPaste,
} = require("../../extension/content_core.js");

test("classifies ChatGPT URL as external AI surface", () => {
  assert.equal(classifySurface("https://chat.openai.com/c/demo"), "chatgpt");
  assert.equal(classifySurface("https://chatgpt.com/"), "chatgpt");
});

test("classifies Gmail URL as external email surface", () => {
  assert.equal(classifySurface("https://mail.google.com/mail/u/0/#inbox"), "gmail");
});

test("classifies demo upload page as demo_upload surface", () => {
  assert.equal(classifySurface("file:///tmp/demo/upload_page.html"), "demo_upload");
  assert.equal(classifySurface("http://127.0.0.1:8080/demo/upload_page.html"), "demo_upload");
});

test("builds analyze request for pasted text", () => {
  const request = buildAnalyzeRequest({
    text: "TraceForgePolicyResolver",
    url: "https://chatgpt.com/",
  });

  assert.equal(request.source, "chrome_extension");
  assert.equal(request.surface, "chatgpt");
  assert.equal(request.event_type, "browser_paste");
  assert.equal(request.content_type, "text");
  assert.equal(request.content, "TraceForgePolicyResolver");
  assert.equal(request.metadata.url, "https://chatgpt.com/");
});

test("blocks paste only for BLOCK decisions", () => {
  assert.equal(shouldBlockPaste({ decision: "BLOCK" }), true);
  assert.equal(shouldBlockPaste({ decision: "WARN" }), false);
  assert.equal(shouldBlockPaste({ decision: "PASS" }), false);
});

test("warns paste only for WARN decisions", () => {
  assert.equal(shouldWarnPaste({ decision: "WARN" }), true);
  assert.equal(shouldWarnPaste({ decision: "BLOCK" }), false);
  assert.equal(shouldWarnPaste({ decision: "PASS" }), false);
});

test("shows a clear message when local agent is unavailable", () => {
  const message = buildUserMessage({
    decision: "WARN",
    localAgentUnavailable: true,
  });

  assert.match(message, /Local Agent is not reachable/);
});

