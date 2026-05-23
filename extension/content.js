(function initContextGuardContentScript() {
  const core = window.ContextGuardCore;

  if (!core) {
    return;
  }

  document.addEventListener(
    "paste",
    async (event) => {
      const pastedText = event.clipboardData && event.clipboardData.getData("text/plain");
      if (!pastedText || !pastedText.trim()) {
        return;
      }

      event.preventDefault();
      const target = event.target;
      const decision = await core.analyzePaste({
        text: pastedText,
        url: window.location.href,
      });

      if (core.shouldBlockPaste(decision)) {
        showContextGuardBanner(core.buildUserMessage(decision), "block");
        return;
      }

      if (core.shouldWarnPaste(decision)) {
        showContextGuardBanner(core.buildUserMessage(decision), "warn");
        const shouldContinue = window.confirm(`${core.buildUserMessage(decision)}\n\nContinue paste?`);
        if (!shouldContinue) {
          return;
        }
      }

      insertText(target, pastedText);
    },
    true,
  );

  function insertText(target, text) {
    if (target instanceof HTMLTextAreaElement || target instanceof HTMLInputElement) {
      const start = target.selectionStart || 0;
      const end = target.selectionEnd || 0;
      const before = target.value.slice(0, start);
      const after = target.value.slice(end);

      target.value = `${before}${text}${after}`;
      const cursor = start + text.length;
      target.setSelectionRange(cursor, cursor);
      target.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertFromPaste", data: text }));
      return;
    }

    if (target && target.isContentEditable) {
      target.focus();
      document.execCommand("insertText", false, text);
    }
  }

  function showContextGuardBanner(message, level) {
    const existing = document.getElementById("contextguard-local-banner");
    if (existing) {
      existing.remove();
    }

    const banner = document.createElement("div");
    banner.id = "contextguard-local-banner";
    banner.textContent = message;
    banner.style.position = "fixed";
    banner.style.top = "16px";
    banner.style.right = "16px";
    banner.style.zIndex = "2147483647";
    banner.style.maxWidth = "360px";
    banner.style.padding = "12px 14px";
    banner.style.borderRadius = "8px";
    banner.style.fontFamily = "system-ui, -apple-system, BlinkMacSystemFont, sans-serif";
    banner.style.fontSize = "13px";
    banner.style.lineHeight = "1.4";
    banner.style.boxShadow = "0 10px 30px rgba(0, 0, 0, 0.18)";
    banner.style.color = "#111827";
    banner.style.background = level === "block" ? "#fee2e2" : "#fef3c7";
    banner.style.border = level === "block" ? "1px solid #ef4444" : "1px solid #f59e0b";

    document.documentElement.appendChild(banner);

    window.setTimeout(() => {
      banner.remove();
    }, 6000);
  }
})();
