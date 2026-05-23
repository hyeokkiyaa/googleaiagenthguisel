# ContextGuard Local MVP

## 1. MVP 목적

ContextGuard Local MVP는 TraceForge의 전체 보안 관제 비전 중에서 데모 영상으로 빠르게 검증 가능한 핵심만 남긴 로컬 프로토타입이다.

이번 MVP의 핵심은 다음 두 가지다.

1. 실시간 행동 분석: 사용자가 외부 서비스에 텍스트를 붙여넣거나 파일을 업로드하려는 순간을 감지한다.
2. Local LLM/sLM Agent 판단: 단순 룰 DLP가 놓치거나 과하게 막는 상황을 로컬 AI Risk Engine이 문맥 기반으로 다시 판단한다.

파일 위험도 자동 분류 레이어는 시간이 남을 경우 추가한다. 우선 제출과 프로토타입 영상은 행동 분석과 Local Agent 판단 흐름을 중심으로 구성한다.

## 2. MVP 한 줄 설명

직원이 ChatGPT, Gmail, 업로드 페이지에 민감 정보를 붙여넣거나 파일을 올리려 할 때, Chrome Extension과 macOS Local Agent가 이를 감지하고 Local AI Risk Engine이 `PASS`, `WARN`, `BLOCK`을 결정해 유출을 막는 로컬 보안 Agent.

## 3. 우선순위

### Must Have

1. Chrome Extension에서 paste/upload 이벤트 감지
2. Local Agent API로 분석 요청 전송
3. Rule DLP baseline 판단
4. Mock sLM 또는 Ollama 기반 AI 판단
5. Rule 결과와 AI 결과를 합쳐 최종 `PASS`, `WARN`, `BLOCK` 결정
6. 차단 또는 경고 UI 표시
7. Incident timeline 저장
8. Security Dashboard에서 사건 확인
9. 데모 시나리오 3개 재현

### Should Have

1. macOS clipboard 감시
2. `ExternalUpload` 폴더 감시
3. 위험 파일 Quarantine 폴더 이동
4. productivity impact metric 표시
5. AI reason/evidence 표시

### Optional

1. 파일 위험도 자동 분류 레이어
2. 실제 Ollama 모델 연동
3. Google ADK 기반 Agent 구조
4. Wazuh 연동 Adapter
5. 메뉴바 앱 완성도 개선

## 4. MVP 구성요소

```text
Chrome Extension
  - ChatGPT/Gmail/demo upload page paste 감지
  - 파일 업로드 감지
  - Local Agent에 분석 요청
  - PASS/WARN/BLOCK 결과에 따라 허용/경고/차단

macOS Local Agent
  - 로컬 HTTP API 제공
  - clipboard 감시
  - ExternalUpload 폴더 감시
  - 위험 파일 Quarantine 이동
  - 메뉴바 상태 표시

Local AI Risk Engine
  - rule DLP baseline
  - mock sLM 또는 Ollama 판단
  - context-aware policy decision

Security Dashboard
  - incident timeline
  - rule result vs AI result
  - AI reason/evidence
  - productivity impact metric
```

## 5. 로컬 아키텍처

```text
User Action
  |
  | paste / upload / clipboard / folder write
  v
Chrome Extension or macOS Watcher
  |
  | POST /analyze
  v
Local Agent API
  |
  v
Risk Engine
  |-- Rule DLP Baseline
  |-- Local sLM / Mock AI Judge
  |-- Policy Decision
  |
  v
Decision: PASS / WARN / BLOCK
  |
  |-- PASS: allow action
  |-- WARN: show warning and log
  |-- BLOCK: prevent action, quarantine if file
  |
  v
Incident Store
  |
  v
Security Dashboard
```

## 6. 핵심 판단 구조

기존 룰 DLP는 정규식과 키워드 기반으로만 판단한다.

예시 룰:

- 주민등록번호 패턴
- 전화번호 패턴
- 이메일 대량 포함
- `confidential`, `internal`, `secret`, `proprietary` 키워드
- `customer`, `lead`, `deal`, `pricing`, `source`, `internal-lib` 키워드

Local sLM 또는 mock AI Judge는 문맥을 함께 본다.

예시 판단:

- 이 정보가 개인 본인 정보인지, 회사/고객 정보인지
- 외부 전송 목적이 있는지
- 고객 DB 또는 영업 리스트로 볼 수 있는지
- 사내 라이브러리, 사내 함수명, 내부 프로젝트명이 포함되어 있는지
- 일반 질문인지, 실제 기밀 내용을 전달하는지

최종 정책은 룰 결과와 AI 결과를 함께 사용한다.

| Rule DLP | AI Judge | 최종 결정 | 의미 |
| --- | --- | --- | --- |
| safe | safe | `PASS` | 정상 작업 |
| risky | safe | `PASS` 또는 `WARN` | 룰 과탐 가능성 |
| safe | risky | `BLOCK` | 룰 미탐을 AI가 보완 |
| risky | risky | `BLOCK` | 명확한 위험 |
| uncertain | risky | `WARN` 또는 `BLOCK` | 관리자 검토 필요 |

## 7. Decision Output Schema

모든 분석 결과는 같은 JSON 구조로 저장한다.

```json
{
  "decision": "BLOCK",
  "risk_level": "critical",
  "rule_result": {
    "matched": false,
    "rule_names": [],
    "reason": "No resident registration number or obvious DLP pattern found"
  },
  "ai_result": {
    "matched": true,
    "category": "customer_database_exfiltration",
    "reason": "The pasted content appears to be a sales lead list containing many potential customers and contact details",
    "evidence": ["100 customer-like rows", "company names", "email addresses", "phone numbers"]
  },
  "final_reason": "Rule DLP missed the case, but AI detected a probable customer database export to an external email context",
  "recommended_action": "Block external transfer and create incident"
}
```

## 8. 이벤트 타입

MVP에서 다룰 이벤트는 다음으로 제한한다.

| 이벤트 타입 | 발생 위치 | 설명 |
| --- | --- | --- |
| `browser_paste` | Chrome Extension | ChatGPT/Gmail/demo page에 텍스트 붙여넣기 |
| `browser_upload` | Chrome Extension | 외부 페이지 파일 업로드 |
| `clipboard_change` | macOS Local Agent | 클립보드 변경 |
| `folder_file_created` | macOS Local Agent | `ExternalUpload` 폴더에 파일 생성 |
| `file_quarantined` | macOS Local Agent | 위험 파일 격리 |
| `decision_created` | Local Agent | PASS/WARN/BLOCK 판단 생성 |

## 9. Incident Model

```json
{
  "id": "inc_001",
  "created_at": "2026-05-23T11:30:00+09:00",
  "source": "chrome_extension",
  "surface": "gmail",
  "event_type": "browser_paste",
  "decision": "BLOCK",
  "risk_level": "critical",
  "rule_decision": "PASS",
  "ai_decision": "BLOCK",
  "title": "Potential customer list exfiltration blocked",
  "summary": "A sales user attempted to paste a probable customer lead list into external email.",
  "evidence": [
    "Multiple customer names",
    "Company names",
    "Contact fields",
    "External email context"
  ],
  "productivity_impact": {
    "rule_only_outcome": "PASS",
    "contextguard_outcome": "BLOCK",
    "impact_type": "prevented_false_negative"
  },
  "raw_sample_redacted": "Customer A, Company B, ***@example.com..."
}
```

## 10. Security Dashboard

대시보드는 영상에서 보안 담당자가 결과를 이해할 수 있을 정도만 구현한다.

필수 표시 항목:

1. 전체 사건 수
2. `PASS`, `WARN`, `BLOCK` 카운트
3. Rule-only 결과와 AI 결과 비교
4. Incident timeline
5. 사건 상세
6. AI reason/evidence
7. Productivity impact metric

Productivity impact metric 예시:

| metric | 의미 |
| --- | --- |
| `prevented_false_positive` | 룰은 막았지만 AI가 정상 업무로 판단해 통과시킨 케이스 |
| `prevented_false_negative` | 룰은 놓쳤지만 AI가 위험으로 판단해 차단한 케이스 |
| `manual_review_saved` | 보안 담당자 수동 검토를 줄인 케이스 |

## 11. 데모 시나리오

### Case A: 개인 이력서의 본인 주민번호

목표:

- 룰 DLP가 과하게 차단하는 상황을 AI가 문맥 기반으로 완화하는 장면을 보여준다.

상황:

1. 직원이 개인용 이력서에 본인 주민등록번호를 작성한다.
2. 사용자가 이 내용을 로컬 demo upload page 또는 허용된 내부 페이지에 붙여넣는다.
3. Rule DLP는 주민등록번호 패턴을 탐지해 `BLOCK`으로 판단한다.
4. Local sLM은 본인 PII이며 외부 전송 맥락이 아니라고 판단한다.
5. 최종 결정은 `PASS` 또는 `WARN`이다.

보여줄 포인트:

- Rule-only였다면 업무가 막혔을 상황
- ContextGuard는 문맥을 보고 과탐을 줄임
- Dashboard에 `prevented_false_positive`로 기록

예상 결과:

```text
Rule DLP: BLOCK
AI Judge: PASS
Final Decision: PASS or WARN
Productivity Impact: prevented_false_positive
```

### Case B: 영업팀의 잠재 고객 100명 명단 외부 이메일 전송

목표:

- 주민번호 같은 명확한 패턴이 없어 룰 DLP가 놓치는 고객 DB 유출을 AI가 차단하는 장면을 보여준다.

상황:

1. 영업팀 사용자가 잠재 고객 100명 명단을 Gmail에 붙여넣는다.
2. 명단에는 이름, 회사명, 직책, 이메일, 전화번호, 관심 제품 등이 포함된다.
3. Rule DLP는 주민등록번호나 명확한 기밀 키워드가 없어 `PASS`로 판단한다.
4. Local sLM은 고객 DB 또는 영업 리드 목록으로 판단한다.
5. 최종 결정은 `BLOCK`이다.

보여줄 포인트:

- 정규식 기반 DLP의 미탐
- AI가 데이터 구조와 업무 맥락을 보고 고객 DB를 식별
- Dashboard에 `prevented_false_negative`로 기록

예상 결과:

```text
Rule DLP: PASS
AI Judge: BLOCK
Final Decision: BLOCK
Productivity Impact: prevented_false_negative
```

### Case C: 사내 라이브러리 함수명을 ChatGPT에 붙여넣기

목표:

- 코드 자체가 짧고 개인정보가 없어도 사내 IP 식별자가 포함되면 위험할 수 있음을 보여준다.

상황:

1. 개발자가 코드 디버깅 중 사내 라이브러리 함수명과 내부 프로젝트명을 ChatGPT에 붙여넣는다.
2. 예시는 `hf_internal_pricing_engine`, `TraceForgePolicyResolver`, `customerRiskScorerV2` 같은 내부 식별자를 포함한다.
3. Rule DLP는 개인정보나 명확한 금칙어가 없어 `PASS`로 판단한다.
4. Local sLM은 사내 IP 식별자와 내부 시스템 구조 노출로 판단한다.
5. 최종 결정은 `BLOCK`이다.

보여줄 포인트:

- 코드/식별자 기반 유출은 일반 DLP가 잘 잡지 못함
- AI가 내부 라이브러리명, 프로젝트명, 함수명 패턴을 근거로 차단
- ChatGPT 입력 직전에 차단되는 사용자 경험

예상 결과:

```text
Rule DLP: PASS
AI Judge: BLOCK
Final Decision: BLOCK
Productivity Impact: prevented_false_negative
```

## 12. 개발 순서

### Phase 1: Local Agent API와 Risk Engine

1. FastAPI 또는 Node 기반 Local Agent API 생성
2. `POST /analyze` 구현
3. Rule DLP baseline 구현
4. Mock sLM 판단 구현
5. `PASS`, `WARN`, `BLOCK` decision schema 확정
6. Incident JSON 저장

완료 기준:

- curl 또는 Postman으로 3개 케이스 분석 가능
- Rule 결과와 AI 결과가 다르게 나오는 로그 확인 가능

### Phase 2: Chrome Extension

1. content script에서 paste 이벤트 감지
2. ChatGPT, Gmail, demo upload page URL 구분
3. Local Agent로 붙여넣기 텍스트 전송
4. `BLOCK`이면 paste 취소
5. `WARN`이면 confirm modal 표시
6. `PASS`이면 정상 진행

완료 기준:

- ChatGPT 또는 demo page에서 Case A/B/C 재현 가능
- 차단 UI가 영상에 명확히 보임

### Phase 3: Dashboard

1. Incident list 표시
2. Incident detail 표시
3. Rule result vs AI result 비교 표시
4. Timeline 표시
5. Productivity impact metric 표시

완료 기준:

- 3개 데모 케이스가 Dashboard에 누적 표시됨
- 보안 담당자가 왜 통과/차단됐는지 이해 가능

### Phase 4: macOS Local Agent 기능

1. clipboard 감시
2. `ExternalUpload` 폴더 감시
3. 위험 파일 Quarantine 이동
4. 메뉴바 상태 표시

완료 기준:

- 위험 텍스트가 clipboard에 잡히거나 위험 파일이 폴더에 들어오면 분석됨
- `BLOCK` 파일이 Quarantine 폴더로 이동됨

### Phase 5: Optional 파일 위험도 분류

1. 파일명, 확장자, 본문 샘플 기반 위험도 분류
2. `critical`, `high`, `medium`, `low` 등급 부여
3. 파일 위험도를 행동 분석에 가중치로 반영

완료 기준:

- 고객 DB CSV, 내부 코드 파일, 일반 문서를 구분 가능
- 파일 위험도가 `BLOCK` 판단 근거에 포함됨

## 13. Local Agent API 초안

### POST /analyze

요청:

```json
{
  "source": "chrome_extension",
  "surface": "chatgpt",
  "event_type": "browser_paste",
  "content_type": "text",
  "content": "debug this function: TraceForgePolicyResolver...",
  "metadata": {
    "url": "https://chat.openai.com/",
    "user_action": "paste"
  }
}
```

응답:

```json
{
  "decision": "BLOCK",
  "risk_level": "high",
  "message": "Internal code identifiers should not be pasted into external AI tools.",
  "rule_result": {
    "decision": "PASS",
    "matched_rules": []
  },
  "ai_result": {
    "decision": "BLOCK",
    "reason": "The text contains internal library and policy resolver identifiers.",
    "evidence": ["TraceForgePolicyResolver", "internal policy engine"]
  },
  "incident_id": "inc_003"
}
```

### GET /incidents

Dashboard에서 사건 목록을 가져온다.

### GET /incidents/{incident_id}

Dashboard에서 사건 상세를 가져온다.

### GET /metrics

Dashboard에서 productivity impact metric을 가져온다.

## 14. Mock sLM 설계

초기에는 실제 Ollama 없이도 데모가 가능하도록 mock sLM을 먼저 구현한다.

Mock 판단 규칙:

| 조건 | AI 판단 |
| --- | --- |
| `resume`, `my own`, `personal resume`, `본인`, `이력서` 문맥 + 주민번호 | `PASS` 또는 `WARN` |
| 30개 이상 연락처, 회사명, 이메일이 반복됨 | `BLOCK` |
| `internal`, `policy resolver`, `pricing engine`, 사내 프로젝트명 | `BLOCK` |
| 일반 질문, 공개 코드, 샘플 문장 | `PASS` |

이후 시간이 남으면 Ollama Provider를 붙인다.

Ollama 후보:

- `llama3.1`
- `qwen2.5`
- `gemma2`
- 한국어 문맥 테스트가 필요하면 더 작은 한국어 지원 모델 검토

## 15. 프로토타입 영상 구성

### 장면 1: 문제 제시

- 기존 Rule DLP는 개인정보 패턴 중심이라 과탐과 미탐이 동시에 발생한다고 설명
- ContextGuard Local은 로컬 Agent가 문맥까지 보고 판단한다고 설명

### 장면 2: Case A

- 주민번호가 들어간 개인 이력서 텍스트 paste
- Rule DLP는 `BLOCK`
- AI Judge는 `PASS`
- 최종 `PASS/WARN`
- Dashboard에서 `prevented_false_positive` 확인

### 장면 3: Case B

- 고객 100명 명단을 Gmail 또는 demo page에 paste
- Rule DLP는 `PASS`
- AI Judge는 `BLOCK`
- paste 차단
- Dashboard에서 고객 DB 의심 근거 확인

### 장면 4: Case C

- 사내 함수명 포함 코드 조각을 ChatGPT에 paste
- Rule DLP는 `PASS`
- AI Judge는 `BLOCK`
- ChatGPT 입력 차단
- Dashboard에서 내부 IP 식별자 evidence 확인

### 장면 5: Dashboard 요약

- 전체 사건 timeline
- Rule-only 결과와 ContextGuard 결과 비교
- 생산성 영향 지표 표시

## 16. 구현 성공 기준

제출 가능한 MVP 기준:

1. Chrome Extension 또는 demo web page에서 paste 차단이 실제로 보인다.
2. Local Agent가 `/analyze` 요청을 받고 판단 결과를 반환한다.
3. 세 가지 데모 케이스가 모두 재현된다.
4. Dashboard에 incident timeline과 AI reason/evidence가 표시된다.
5. Rule DLP와 AI 판단이 다른 장면이 명확히 보인다.

좋은 MVP 기준:

1. clipboard 또는 `ExternalUpload` 폴더 감시까지 동작한다.
2. 위험 파일 Quarantine 이동이 된다.
3. mock sLM 대신 Ollama Provider가 일부 케이스를 판단한다.
4. 파일 위험도 분류가 행동 분석 점수에 반영된다.

## 17. 이번 MVP에서 버릴 것

다음 기능은 이번 영상용 MVP에서는 구현하지 않는다.

1. 실제 기업용 엔드포인트 에이전트
2. 실제 Gmail 전송 API 차단
3. 실제 ChatGPT 서비스 내부 제어
4. 운영용 Wazuh 통합
5. PostgreSQL 필수화
6. 완전한 Google ADK Multi-Agent
7. 대규모 파일 분류 정확도 평가
8. 50개 문서 샘플셋 전체 구축

## 18. 추천 저장소 구조

```text
contextguard-local/
  agent/
    app/
      main.py
      risk_engine.py
      rule_dlp.py
      ai_judge.py
      policy.py
      incidents.py
    data/
      incidents.json
      quarantine/
    requirements.txt
  extension/
    manifest.json
    content.js
    background.js
    popup.html
    popup.js
  dashboard/
    # Streamlit 또는 React
  demo/
    upload_page.html
    samples/
      case_a_resume.txt
      case_b_customer_leads.csv
      case_c_internal_code.txt
  MVP.md
  IMPLEMENTATION.md
  README.md
```

## 19. 바로 다음 작업

1. Local Agent API를 먼저 만든다.
2. 세 케이스를 mock sLM으로 정확히 재현한다.
3. Chrome Extension에서 paste 이벤트를 Local Agent로 보낸다.
4. Dashboard는 가장 단순한 Streamlit으로 먼저 만든다.
5. 시간이 남으면 macOS watcher와 Quarantine을 붙인다.

