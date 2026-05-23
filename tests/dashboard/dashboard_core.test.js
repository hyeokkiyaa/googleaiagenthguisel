const test = require("node:test");
const assert = require("node:assert/strict");

const {
  decisionClass,
  metricRows,
  productivityLabel,
  summarizeIncident,
} = require("../../dashboard/dashboard_core.js");

test("maps decisions to stable CSS classes", () => {
  assert.equal(decisionClass("BLOCK"), "decision-block");
  assert.equal(decisionClass("WARN"), "decision-warn");
  assert.equal(decisionClass("PASS"), "decision-pass");
});

test("formats metric rows in dashboard order", () => {
  const rows = metricRows({
    total: 3,
    pass: 0,
    warn: 1,
    block: 2,
    prevented_false_positive: 1,
    prevented_false_negative: 2,
    manual_review_saved: 0,
  });

  assert.deepEqual(rows.map((row) => row.key), [
    "total",
    "block",
    "warn",
    "prevented_false_positive",
    "prevented_false_negative",
  ]);
});

test("formats productivity labels", () => {
  assert.equal(productivityLabel("prevented_false_positive"), "오탐 방지");
  assert.equal(productivityLabel("prevented_false_negative"), "미탐 방지");
  assert.equal(productivityLabel("none"), "변화 없음");
});

test("summarizes incident for list rendering", () => {
  const summary = summarizeIncident({
    id: "inc_000001",
    decision: "BLOCK",
    surface: "gmail",
    event_type: "browser_paste",
    title: "Risky external action blocked",
    created_at: "2026-05-23T11:30:00+09:00",
  });

  assert.equal(summary.id, "inc_000001");
  assert.equal(summary.decisionClassName, "decision-block");
  assert.match(summary.subtitle, /gmail/);
  assert.match(summary.subtitle, /browser_paste/);
});

