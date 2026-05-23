# TraceForge 구현 명세

## 1. MVP 목표

TraceForge MVP는 산업 현장의 중요 파일 유출 위험을 탐지하고, AI Agent가 사건을 조사해 보안 담당자에게 사건 카드로 제공하는 보안 관제 프로토타입이다.

MVP에서 반드시 구현할 기능은 다음과 같다.

1. 파일 위험도 자동 분류
2. 업무 기기 행동 이벤트 수집 및 저장
3. 행동 시퀀스 기반 위험 패턴 탐지
4. Agentic 포렌식 조사
5. 보안팀 대시보드용 사건 카드 생성
6. Gemini Provider와 Local LLM Provider를 교체 가능한 구조

MVP에서 구현하지 않는 항목은 다음과 같다.

1. 실제 OS 수준 파일 차단
2. 실제 USB, 메일, 브라우저 후킹
3. 운영 환경용 Wazuh 전체 배포
4. 실제 사내 폐쇄망 LLM 서빙
5. 인사 평가, 근태 분석 등 보안 목적 외 기능

MVP의 차단은 실제 차단이 아니라 `allow`, `warn`, `block` 판단과 알림 생성까지로 제한한다.

## 2. 권장 기술 스택

| 영역 | 기술 |
| --- | --- |
| Backend | Python, FastAPI |
| Agent Framework | Google ADK |
| LLM | Gemini API, LocalLLMProvider stub |
| Database | PostgreSQL 권장, MVP 초기에는 SQLite 허용 |
| Frontend | React 또는 Streamlit |
| Event Simulator | Python CLI 또는 웹 UI |
| Security Infra Adapter | Wazuh 연동 인터페이스, MVP는 Mock Adapter |

## 3. 전체 아키텍처

```text
Endpoint / Simulator
        |
        v
Event Ingestion API
        |
        v
Event Store / File Store Metadata
        |
        v
Risk Pattern Detection Agent
        |
        v
Forensic Investigation Agent
        |
        v
Incident Card API
        |
        v
Security Dashboard
```

LLM 호출은 반드시 Provider 인터페이스 뒤에 숨긴다.

```text
Application
    |
    v
LLMProvider interface
    |-- GeminiProvider
    |-- LocalLLMProvider
```

## 4. 핵심 모듈

### 4.1 File Classification Agent

역할:

- 파일명, 확장자, 작성자, 경로, 본문 일부를 분석한다.
- 파일 위험도를 `critical`, `high`, `medium`, `low` 중 하나로 분류한다.
- 민감 요소를 추출한다.
- 보호 정책을 추천한다.

입력 예시:

```json
{
  "file_id": "file_001",
  "name": "2026_반도체_공정조건.xlsx",
  "extension": "xlsx",
  "owner": "process-team",
  "path": "/rnd/process/",
  "content_sample": "Etching pressure, chamber temperature, yield threshold..."
}
```

출력 예시:

```json
{
  "file_id": "file_001",
  "risk_level": "critical",
  "sensitive_factors": ["공정 수치", "수율 기준", "생산 조건"],
  "recommended_policy": ["외부 전송 차단", "USB 저장 차단", "외부 LLM 입력 차단"],
  "reason": "핵심 제조 공정 조건과 수율 기준이 포함되어 있음"
}
```

### 4.2 Event Ingestion

역할:

- 엔드포인트 또는 시뮬레이터에서 발생한 행동 이벤트를 수집한다.
- 이벤트를 DB에 저장한다.
- 파일 위험도와 사용자, 기기 정보를 연결한다.

MVP에서 지원할 이벤트 타입:

| 이벤트 타입 | 설명 |
| --- | --- |
| `file_open` | 파일 열람 |
| `text_copy` | 파일 내용 복사 |
| `file_copy` | 파일 복사 |
| `screenshot` | 화면 캡처 |
| `print` | 출력 |
| `usb_write` | USB 저장 |
| `cloud_upload` | 클라우드 업로드 |
| `external_email_attach` | 외부 메일 첨부 |
| `partner_share` | 협력사 공유 |
| `off_hours_access` | 비업무시간 접근 |
| `external_llm_input` | 외부 LLM 입력 |

이벤트 입력 예시:

```json
{
  "event_id": "evt_001",
  "timestamp": "2026-05-23T11:30:00+09:00",
  "user_id": "user_001",
  "device_id": "device_001",
  "file_id": "file_001",
  "event_type": "external_llm_input",
  "target": "chat.openai.com",
  "payload_sample": "공정 압력 조건과 수율 기준은...",
  "metadata": {
    "browser": "Chrome"
  }
}
```

### 4.3 Risk Pattern Detection Agent

역할:

- 단일 이벤트가 아니라 사용자별 행동 시퀀스를 분석한다.
- 룰 기반 점수와 LLM 해석을 결합해 위험도를 판단한다.
- 대응 액션을 `allow`, `warn`, `block` 중 하나로 결정한다.

기본 위험 점수 예시:

| 조건 | 점수 |
| --- | ---: |
| Critical 파일 접근 | +30 |
| High 파일 접근 | +20 |
| 비업무시간 접근 | +15 |
| 파일 내용 복사 | +20 |
| USB 저장 | +35 |
| 클라우드 업로드 | +35 |
| 외부 메일 첨부 | +40 |
| 외부 LLM 입력 | +45 |
| 10분 내 위험 이벤트 3개 이상 | +25 |

대응 기준:

| 총점 | 액션 |
| ---: | --- |
| 0-39 | `allow` |
| 40-69 | `warn` |
| 70 이상 | `block` |

LLM은 다음을 보완한다.

- 행동의 의도 해석
- 정상 업무 가능성 판단
- 설명 문장 생성
- 추가 조사 필요 여부 판단

### 4.4 Forensic Investigation Agent

역할:

- 위험 이벤트 발생 시 조사 가설을 생성한다.
- 필요한 Tool을 호출해 관련 로그를 조회한다.
- 사용자, 기기, 파일, 이벤트 흐름을 타임라인으로 재구성한다.
- 권한이나 정보가 부족하면 Human-in-the-loop 요청을 생성한다.

필수 Tool:

| Tool | 설명 |
| --- | --- |
| `get_file_classification(file_id)` | 파일 위험도 조회 |
| `search_events(user_id, file_id, time_range)` | 관련 이벤트 조회 |
| `get_user_profile(user_id)` | 사용자 부서, 역할 조회 |
| `get_device_profile(device_id)` | 기기 등록 상태 조회 |
| `create_incident_card(incident)` | 사건 카드 생성 |
| `request_human_review(question, context)` | 사람 확인 요청 |

조사 출력 예시:

```json
{
  "incident_id": "inc_001",
  "severity": "critical",
  "hypothesis": "사용자가 Critical 파일 내용을 외부 LLM에 입력해 기밀 유출 가능성이 있음",
  "timeline": [
    {
      "timestamp": "2026-05-23T11:10:00+09:00",
      "event": "critical file opened"
    },
    {
      "timestamp": "2026-05-23T11:12:00+09:00",
      "event": "text copied from file"
    },
    {
      "timestamp": "2026-05-23T11:14:00+09:00",
      "event": "copied content submitted to external LLM"
    }
  ],
  "recommended_actions": ["세션 차단", "사용자 확인", "파일 접근권한 재검토"],
  "needs_human_review": true,
  "human_review_question": "해당 사용자가 외부 LLM 사용 승인을 받은 프로젝트에 참여 중인지 확인이 필요함"
}
```

### 4.5 Orchestrator Agent

역할:

- 파일 분류, 이벤트 분석, 포렌식 조사를 연결한다.
- 각 Agent의 실행 순서와 상태를 관리한다.
- 사건 카드 생성 조건을 판단한다.

기본 흐름:

```text
1. 파일 등록 또는 수정
2. File Classification Agent 실행
3. 파일 위험도 저장
4. 이벤트 수집
5. Risk Pattern Detection Agent 실행
6. warn/block 판단 시 Forensic Investigation Agent 실행
7. 사건 카드 생성
8. Dashboard에 표시
```

## 5. 데이터 모델

### 5.1 files

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | string | 파일 ID |
| `name` | string | 파일명 |
| `extension` | string | 확장자 |
| `owner` | string | 소유자 |
| `path` | string | 경로 |
| `content_sample` | text | 본문 일부 |
| `risk_level` | string | `critical`, `high`, `medium`, `low` |
| `sensitive_factors` | json | 민감 요소 |
| `recommended_policy` | json | 권장 정책 |
| `created_at` | datetime | 생성 시각 |
| `updated_at` | datetime | 수정 시각 |

### 5.2 events

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | string | 이벤트 ID |
| `timestamp` | datetime | 발생 시각 |
| `user_id` | string | 사용자 ID |
| `device_id` | string | 기기 ID |
| `file_id` | string | 파일 ID |
| `event_type` | string | 이벤트 타입 |
| `target` | string | 대상 서비스, 경로, URL |
| `payload_sample` | text | 분석용 샘플 |
| `risk_score` | integer | 룰 기반 점수 |
| `llm_reason` | text | LLM 판단 근거 |
| `action` | string | `allow`, `warn`, `block` |
| `metadata` | json | 추가 정보 |

### 5.3 incidents

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | string | 사건 ID |
| `created_at` | datetime | 생성 시각 |
| `severity` | string | `critical`, `high`, `medium`, `low` |
| `status` | string | `open`, `reviewing`, `closed` |
| `user_id` | string | 관련 사용자 |
| `device_id` | string | 관련 기기 |
| `file_id` | string | 관련 파일 |
| `summary` | text | 사건 요약 |
| `hypothesis` | text | Agent 조사 가설 |
| `timeline` | json | 이벤트 타임라인 |
| `evidence` | json | 근거 이벤트 |
| `recommended_actions` | json | 권장 조치 |
| `needs_human_review` | boolean | 사람 확인 필요 여부 |
| `human_review_question` | text | 확인 요청 질문 |

### 5.4 users

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | string | 사용자 ID |
| `name` | string | 이름 |
| `department` | string | 부서 |
| `role` | string | 직무 |
| `allowed_projects` | json | 허용 프로젝트 |

### 5.5 devices

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | string | 기기 ID |
| `user_id` | string | 소유 사용자 |
| `hostname` | string | 호스트명 |
| `managed` | boolean | 등록 관리 기기 여부 |
| `last_seen_at` | datetime | 마지막 이벤트 시각 |

## 6. Backend API

### 6.1 파일 API

```http
POST /files
GET /files/{file_id}
POST /files/{file_id}/classify
GET /files/{file_id}/classification
```

### 6.2 이벤트 API

```http
POST /events
GET /events
GET /events/{event_id}
GET /users/{user_id}/events
```

### 6.3 위험 분석 API

```http
POST /risk/analyze-event
POST /risk/analyze-sequence
```

### 6.4 사건 API

```http
GET /incidents
GET /incidents/{incident_id}
POST /incidents/{incident_id}/review
POST /incidents/{incident_id}/close
```

### 6.5 대시보드 API

```http
GET /dashboard/summary
GET /dashboard/incidents/recent
GET /dashboard/risk-trends
```

## 7. LLM Provider 인터페이스

모든 Agent는 특정 LLM SDK를 직접 호출하지 않는다.

```python
from typing import Protocol, Any


class LLMProvider(Protocol):
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        ...

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        ...
```

구현체:

- `GeminiProvider`: 해커톤 MVP 기본 Provider
- `LocalLLMProvider`: 사내망 배포용 Provider, MVP에서는 mock 또는 OpenAI-compatible local endpoint로 구현

환경 변수 예시:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
LOCAL_LLM_BASE_URL=http://localhost:8001/v1
LOCAL_LLM_MODEL=qwen-local
```

## 8. Event Simulator

MVP는 실제 엔드포인트 에이전트 대신 시뮬레이터로 이벤트를 생성한다.

필수 시나리오:

| 시나리오 | 기대 결과 |
| --- | --- |
| Critical 파일 열람 후 외부 LLM 입력 | `block`, critical incident 생성 |
| High 파일 열람 후 외부 메일 첨부 | `block` 또는 `warn`, incident 생성 |
| Medium 파일 정상 열람 | `allow`, incident 없음 |
| Critical 파일 비업무시간 접근 후 USB 저장 | `block`, incident 생성 |
| 일반 문서 외부 LLM 질문 | `allow`, incident 없음 |
| Critical 파일 열람 후 텍스트 복사만 수행 | `warn`, 필요 시 incident 생성 |
| 관리 기기가 아닌 기기에서 High 파일 접근 | `warn` 또는 `block` |
| 협력사 공유 허용 프로젝트 파일 공유 | `allow` 또는 낮은 `warn` |
| 짧은 시간 내 다수 파일 복사 | `warn` 또는 `block` |
| 외부 업로드 실패 이벤트 반복 | `warn`, 조사 필요 |

샘플 데이터:

- 가짜 기밀 문서 50개
- 정상 행동 시퀀스 10개
- 위험 행동 시퀀스 10개

## 9. Dashboard 요구사항

대시보드는 보안 담당자가 현재 위험 상황을 빠르게 파악하고 사건을 열람할 수 있으면 충분하다.

필수 화면:

1. 사건 목록
2. 사건 상세 카드
3. 사용자별 이벤트 타임라인
4. 자연어 질의 입력창
5. Human-in-the-loop 확인 요청 목록

사건 카드 필수 필드:

- 사건 ID
- 위험도
- 상태
- 사용자
- 기기
- 파일
- 행동 흐름
- AI 판단 근거
- 권장 조치
- 사람 확인 필요 여부

## 10. Agent 워크플로

### 10.1 Sequential Workflow

```text
File Classification Agent
    -> Risk Pattern Detection Agent
    -> Forensic Investigation Agent
    -> Incident Card
```

사용처:

- 일반적인 이벤트 처리
- 데모 기본 시나리오

### 10.2 Hierarchical Workflow

```text
Orchestrator Agent
    |-- File Classification Agent
    |-- Risk Pattern Detection Agent
    |-- Forensic Investigation Agent
```

사용처:

- Agent 간 역할 분담 시연
- Orchestrator가 다음 조사 단계를 결정하는 시나리오

### 10.3 Human-in-the-loop Workflow

```text
Forensic Investigation Agent
    -> request_human_review()
    -> Security Manager Response
    -> Investigation Resume
    -> Incident Card Update
```

사용처:

- 사용자의 프로젝트 권한이 불명확한 경우
- 협력사 공유가 승인된 업무인지 확인해야 하는 경우
- 차단 전에 관리자의 승인이 필요한 경우

## 11. 평가 기준

MVP 검증 기준:

| 항목 | 목표 |
| --- | ---: |
| 파일 위험도 분류 정확도 | 85% 이상 |
| 위험 행동 시나리오 탐지율 | 90% 이상 |
| False Positive 비율 | 15% 이하 |
| 구현된 Multi-Agent 시나리오 | 3종 이상 |
| 이벤트 수집 지연 | 1초 이내 |
| 위험 판단 응답 시간 | 5초 이내 |

초기 개발 단계에서는 정확도보다 전체 end-to-end 흐름 완성을 우선한다.

## 12. 권장 프로젝트 구조

```text
traceforge/
  app/
    main.py
    config.py
    api/
      files.py
      events.py
      incidents.py
      dashboard.py
    agents/
      orchestrator.py
      file_classifier.py
      risk_detector.py
      forensic_investigator.py
    llm/
      base.py
      gemini_provider.py
      local_provider.py
    models/
      file.py
      event.py
      incident.py
      user.py
      device.py
    services/
      scoring.py
      timeline.py
      incident_cards.py
      wazuh_adapter.py
    storage/
      database.py
      repositories.py
  simulator/
    generate_files.py
    generate_events.py
    scenarios.py
  dashboard/
    # React 또는 Streamlit 구현
  tests/
    test_file_classifier.py
    test_risk_detector.py
    test_forensic_workflow.py
  .env.example
  README.md
```

## 13. 개발 우선순위

### Phase 1: 백엔드 뼈대

1. FastAPI 프로젝트 생성
2. DB 모델 정의
3. 파일, 이벤트, 사건 API 구현
4. 샘플 데이터 seed 스크립트 구현

### Phase 2: LLM Provider와 파일 분류

1. `LLMProvider` 인터페이스 작성
2. `GeminiProvider` 구현
3. `LocalLLMProvider` mock 구현
4. File Classification Agent 구현
5. 샘플 문서 50개 분류 테스트

### Phase 3: 위험 이벤트 분석

1. 11종 이벤트 타입 정의
2. 룰 기반 점수 계산 구현
3. 행동 시퀀스 조회 구현
4. Risk Pattern Detection Agent 구현
5. 정상/위험 시나리오 테스트

### Phase 4: Agentic 포렌식

1. Tool 함수 구현
2. Forensic Investigation Agent 구현
3. 타임라인 재구성 구현
4. Human-in-the-loop 요청 구현
5. 사건 카드 생성 구현

### Phase 5: 대시보드와 데모

1. 사건 목록 화면 구현
2. 사건 상세 카드 구현
3. 이벤트 타임라인 화면 구현
4. 자연어 질의 인터페이스 구현
5. End-to-end 데모 시나리오 3개 고정

## 14. 데모 시나리오

### 시나리오 A: 외부 LLM 기밀 입력 차단

1. Critical 파일 등록
2. 파일 위험도 자동 분류
3. 사용자가 파일을 열람
4. 사용자가 본문을 복사
5. 사용자가 외부 LLM에 입력
6. Agent가 위험 시퀀스를 탐지
7. `block` 판단
8. 포렌식 Agent가 타임라인 생성
9. 사건 카드 생성

### 시나리오 B: 비업무시간 USB 저장

1. High 또는 Critical 파일 등록
2. 비업무시간 파일 접근 이벤트 발생
3. USB 저장 이벤트 발생
4. Agent가 유출 가능 경로를 조사
5. 사건 카드 생성
6. 관리자 확인 요청 생성

### 시나리오 C: 정상 업무 공유와 False Positive 억제

1. Medium 파일 등록
2. 승인된 협력사 공유 이벤트 발생
3. 사용자 프로젝트 권한 확인
4. Agent가 정상 업무 가능성을 설명
5. `allow` 또는 낮은 수준 `warn` 판단

## 15. 구현 시 주의사항

1. Agent가 직접 DB에 접근하지 않고 Tool 또는 Service 계층을 통해 접근하게 한다.
2. LLM 응답은 가능한 JSON schema로 강제하고, 파싱 실패 시 fallback을 둔다.
3. 파일 원문 전체 저장은 피하고 `content_sample` 중심으로 개발한다.
4. 위험 판단은 LLM 단독이 아니라 룰 점수와 LLM 설명을 함께 사용한다.
5. 모든 사건 카드에는 사람이 검토할 수 있는 근거 이벤트 ID를 포함한다.
6. MVP에서는 Wazuh를 직접 붙이지 않아도 되지만 `wazuh_adapter.py` 인터페이스는 남긴다.
7. 데모용 데이터는 실제 기업명, 실제 개인정보, 실제 영업비밀을 포함하지 않는다.

