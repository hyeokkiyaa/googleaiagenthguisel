(function initContextGuardCore(globalScope) {
  const LocalAgentAnalyzeUrl = "http://127.0.0.1:8765/analyze";

  function classifySurface(url) {
    let parsedUrl;
    try {
      parsedUrl = new URL(url);
    } catch {
      return "unknown";
    }

    const host = parsedUrl.hostname.toLowerCase();
    const pathname = parsedUrl.pathname.toLowerCase();

    if (host === "chat.openai.com" || host === "chatgpt.com") {
      return "chatgpt";
    }

    if (host === "mail.google.com") {
      return "gmail";
    }

    if (pathname.endsWith("/demo/upload_page.html") || pathname.endsWith("upload_page.html")) {
      return "demo_upload";
    }

    return "unknown";
  }

  function buildAnalyzeRequest({ text, url }) {
    return {
      source: "chrome_extension",
      surface: classifySurface(url),
      event_type: "browser_paste",
      content_type: "text",
      content: text,
      metadata: {
        url,
        user_action: "paste",
      },
    };
  }

  async function analyzePaste({ text, url, fetchImpl }) {
    const request = buildAnalyzeRequest({ text, url });
    const fetchFn = fetchImpl || globalScope.fetch;

    try {
      const response = await fetchFn(LocalAgentAnalyzeUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Local Agent returned HTTP ${response.status}`);
      }

      return response.json();
    } catch {
      return {
        decision: "WARN",
        risk_level: "medium",
        message: "ContextGuard Local Agent is not reachable.",
        localAgentUnavailable: true,
      };
    }
  }

  function shouldBlockPaste(decisionResponse) {
    return decisionResponse && decisionResponse.decision === "BLOCK";
  }

  function shouldWarnPaste(decisionResponse) {
    return decisionResponse && decisionResponse.decision === "WARN";
  }

  function buildUserMessage(decisionResponse) {
    if (decisionResponse.localAgentUnavailable) {
      return "ContextGuard Local Agent is not reachable. Paste was not blocked, but this action should be reviewed.";
    }

    if (decisionResponse.decision === "BLOCK") {
      return decisionResponse.final_reason || decisionResponse.message || "ContextGuard blocked this paste.";
    }

    if (decisionResponse.decision === "WARN") {
      return decisionResponse.final_reason || decisionResponse.message || "ContextGuard detected a risky paste.";
    }

    return decisionResponse.message || "ContextGuard allowed this paste.";
  }

  const api = {
    LocalAgentAnalyzeUrl,
    analyzePaste,
    buildAnalyzeRequest,
    buildUserMessage,
    classifySurface,
    shouldBlockPaste,
    shouldWarnPaste,
  };

  globalScope.ContextGuardCore = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : window);

