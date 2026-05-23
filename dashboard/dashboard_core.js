(function initDashboardCore(globalScope) {
  function decisionClass(decision) {
    if (decision === "BLOCK") {
      return "decision-block";
    }
    if (decision === "WARN") {
      return "decision-warn";
    }
    return "decision-pass";
  }

  function productivityLabel(impactType) {
    const labels = {
      prevented_false_positive: "오탐 방지",
      prevented_false_negative: "미탐 방지",
      manual_review_saved: "수동 검토 생략",
      none: "변화 없음",
    };

    return labels[impactType] || impactType;
  }

  function metricRows(metrics) {
    return [
      { key: "total", label: "Total incidents", value: metrics.total || 0 },
      { key: "block", label: "Blocked", value: metrics.block || 0 },
      { key: "warn", label: "Warnings", value: metrics.warn || 0 },
      {
        key: "prevented_false_positive",
        label: "False positives reduced",
        value: metrics.prevented_false_positive || 0,
      },
      {
        key: "prevented_false_negative",
        label: "False negatives caught",
        value: metrics.prevented_false_negative || 0,
      },
    ];
  }

  function summarizeIncident(incident) {
    return {
      id: incident.id,
      title: incident.title || "Untitled incident",
      decision: incident.decision,
      decisionClassName: decisionClass(incident.decision),
      subtitle: `${incident.surface || "unknown"} · ${incident.event_type || "unknown"} · ${incident.created_at || ""}`,
    };
  }

  const api = {
    decisionClass,
    metricRows,
    productivityLabel,
    summarizeIncident,
  };

  globalScope.ContextGuardDashboard = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : window);

