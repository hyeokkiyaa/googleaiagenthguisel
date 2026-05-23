# ContextGuard Local MVP 개발 계획

## 1. 개발 원칙

이 문서는 실제 개발 중 항상 참고하는 실행 체크리스트다. 제품 범위는 `MVP.md`를 기준으로 하고, 구현 순서와 테스트 기준은 이 문서를 기준으로 한다.

개발할 때 반드시 지킬 원칙:

1. 한 번에 큰 기능을 만들지 않고 작은 단위로 나눈다.
2. 각 개발 단위마다 테스트 케이스를 먼저 정의한다.
3. 기능 구현 후 반드시 관련 테스트를 추가하거나 갱신한다.
4. 테스트 없이 기능만 추가하지 않는다.
5. 데모 시나리오 Case A/B/C가 깨지지 않는지 계속 확인한다.
6. `Rule DLP`, `AI Judge`, `Policy Decision`은 분리해서 테스트 가능하게 만든다.
7. 실제 LLM이 없어도 mock sLM으로 전체 데모가 가능해야 한다.
8. 실제 Ollama 연동은 mock 기반 흐름이 안정된 뒤 붙인다.

## 2. 최종 MVP 범위

### 1차 제출 필수 범위

1. Local Agent API
2. Rule DLP baseline
3. Mock sLM AI Judge
4. Policy Decision Engine
5. Incident 저장
6. Chrome Extension paste 감지와 차단
7. Security Dashboard
8. 데모 시나리오 3개

### 시간이 남으면 추가할 범위

1. macOS clipboard watcher
2. `ExternalUpload` 폴더 watcher
3. 위험 파일 Quarantine 이동
4. Ollama Provider
5. 파일 위험도 분류 레이어

## 3. 데모 기준 시나리오

### Case A: 개인 이력서 본인 주민번호

목표:

- Rule DLP 과탐을 AI가 줄이는 장면을 보여준다.

기대 결과:

```text
Rule DLP: BLOCK
AI Judge: PASS 또는 WARN
Final Decision: PASS 또는 WARN
Impact: prevented_false_positive
```

필수 테스트:

1. 주민등록번호 패턴이 있으면 Rule DLP가 `BLOCK`을 반환한다.
2. 이력서, 본인, 개인 문맥이 있으면 AI Judge가 `PASS` 또는 `WARN`을 반환한다.
3. Policy Decision이 Rule `BLOCK`과 AI `PASS` 조합을 최종 `PASS` 또는 `WARN`으로 완화한다.
4. Incident에 `prevented_false_positive`가 기록된다.

### Case B: 잠재 고객 100명 명단 외부 이메일 전송

목표:

- Rule DLP 미탐을 AI가 보완해 고객 DB 유출을 차단하는 장면을 보여준다.

기대 결과:

```text
Rule DLP: PASS
AI Judge: BLOCK
Final Decision: BLOCK
Impact: prevented_false_negative
```

필수 테스트:

1. 주민등록번호가 없으면 Rule DLP가 기본적으로 `PASS`를 반환한다.
2. 다수의 이름, 회사명, 이메일, 전화번호 패턴이 반복되면 AI Judge가 고객 DB로 판단한다.
3. Policy Decision이 Rule `PASS`와 AI `BLOCK` 조합을 최종 `BLOCK`으로 결정한다.
4. Incident에 `prevented_false_negative`가 기록된다.

### Case C: 사내 라이브러리 함수명 ChatGPT 붙여넣기

목표:

- 개인정보가 없어도 사내 IP 식별자가 외부 AI로 나가면 차단하는 장면을 보여준다.

기대 결과:

```text
Rule DLP: PASS
AI Judge: BLOCK
Final Decision: BLOCK
Impact: prevented_false_negative
```

필수 테스트:

1. 개인정보 패턴이 없으면 Rule DLP가 `PASS`를 반환한다.
2. 내부 프로젝트명, 내부 함수명, policy resolver, pricing engine 같은 식별자가 있으면 AI Judge가 `BLOCK`을 반환한다.
3. ChatGPT surface에서 발생한 paste 이벤트는 외부 AI 입력 맥락으로 판단된다.
4. Incident evidence에 내부 식별자가 redaction 또는 요약 형태로 기록된다.

## 4. 개발 단계

## Phase 0: 프로젝트 기본 구조

목표:

- 저장소 구조를 만들고 테스트 실행 환경을 먼저 갖춘다.

작업:

1. `agent/` 디렉터리 생성
2. Python 패키지 구조 생성
3. `pytest` 기반 테스트 구조 생성
4. `requirements.txt` 생성
5. 기본 README 실행 명령 추가

테스트 케이스:

1. `pytest`가 실행되고 최소 1개 smoke test가 통과한다.
2. Agent app 모듈을 import할 수 있다.

완료 조건:

```bash
pytest
```

명령이 성공해야 한다.

## Phase 1: Local Agent API Skeleton

목표:

- `/health`, `/analyze`, `/incidents`, `/metrics` API의 뼈대를 만든다.

작업:

1. FastAPI app 생성
2. `GET /health` 구현
3. `POST /analyze` request/response schema 구현
4. `GET /incidents` 구현
5. `GET /metrics` 구현
6. CORS 설정 추가

테스트 케이스:

1. `GET /health`가 `200 OK`와 `{"status": "ok"}`를 반환한다.
2. `POST /analyze`에 최소 요청을 보내면 decision response schema를 반환한다.
3. 잘못된 요청은 `422`를 반환한다.
4. `GET /incidents`는 빈 리스트로 시작한다.
5. `GET /metrics`는 기본 metric 값을 반환한다.

완료 조건:

```bash
pytest tests/test_api.py
```

명령이 성공해야 한다.

## Phase 2: Rule DLP Baseline

목표:

- 정규식과 키워드 기반의 기본 DLP 판단을 만든다.

작업:

1. 주민등록번호 패턴 탐지
2. 이메일 패턴 탐지
3. 전화번호 패턴 탐지
4. 기밀 키워드 탐지
5. Rule result schema 정의

테스트 케이스:

1. 주민등록번호가 포함되면 `BLOCK`
2. 기밀 키워드가 포함되면 `WARN` 또는 `BLOCK`
3. 일반 텍스트는 `PASS`
4. 고객 명단처럼 주민등록번호가 없는 데이터는 Rule만으로는 `PASS`
5. 사내 함수명만 있는 코드 조각은 Rule만으로는 `PASS`

완료 조건:

```bash
pytest tests/test_rule_dlp.py
```

명령이 성공해야 한다.

## Phase 3: Mock sLM AI Judge

목표:

- 실제 LLM 없이 Case A/B/C를 문맥 기반으로 판단하는 mock AI Judge를 만든다.

작업:

1. AI result schema 정의
2. Case A 문맥 판단
3. Case B 고객 DB 판단
4. Case C 내부 IP 식별자 판단
5. evidence와 reason 생성

테스트 케이스:

1. 이력서와 본인 PII 문맥이면 `PASS` 또는 `WARN`
2. 고객/리드/회사명/연락처가 반복되면 `BLOCK`
3. 내부 함수명과 프로젝트명이 있으면 `BLOCK`
4. 일반 질문은 `PASS`
5. AI reason과 evidence가 비어 있지 않다.

완료 조건:

```bash
pytest tests/test_ai_judge.py
```

명령이 성공해야 한다.

## Phase 4: Policy Decision Engine

목표:

- Rule DLP와 AI Judge 결과를 합쳐 최종 `PASS`, `WARN`, `BLOCK`을 결정한다.

작업:

1. decision matrix 구현
2. risk level 계산
3. productivity impact 계산
4. final reason 생성
5. Case A/B/C end-to-end 판단 연결

테스트 케이스:

1. Rule `BLOCK`, AI `PASS`는 최종 `PASS` 또는 `WARN`
2. Rule `PASS`, AI `BLOCK`은 최종 `BLOCK`
3. Rule `BLOCK`, AI `BLOCK`은 최종 `BLOCK`
4. Rule `PASS`, AI `PASS`는 최종 `PASS`
5. Case A impact는 `prevented_false_positive`
6. Case B/C impact는 `prevented_false_negative`

완료 조건:

```bash
pytest tests/test_policy.py
```

명령이 성공해야 한다.

## Phase 5: Incident Store

목표:

- 분석 결과를 Dashboard에서 볼 수 있도록 사건으로 저장한다.

작업:

1. 파일 기반 JSON store 구현
2. incident ID 생성
3. raw content redaction
4. 사건 목록 조회
5. metric 집계

테스트 케이스:

1. `BLOCK` 또는 `WARN` decision은 incident로 저장된다.
2. `PASS`도 데모 metric을 위해 저장할지 정책을 명확히 한다.
3. raw content는 전체 원문이 아니라 redacted sample로 저장된다.
4. incident list가 최신순으로 반환된다.
5. metrics가 PASS/WARN/BLOCK 카운트를 정확히 계산한다.

완료 조건:

```bash
pytest tests/test_incidents.py
pytest tests/test_api.py
```

명령이 성공해야 한다.

## Phase 6: Demo Samples

목표:

- 영상 촬영에 바로 사용할 Case A/B/C 샘플 데이터를 만든다.

작업:

1. `demo/samples/case_a_resume.txt`
2. `demo/samples/case_b_customer_leads.csv`
3. `demo/samples/case_c_internal_code.txt`
4. sample loader 또는 테스트 fixture 작성

테스트 케이스:

1. Case A sample은 기대 결과와 일치한다.
2. Case B sample은 기대 결과와 일치한다.
3. Case C sample은 기대 결과와 일치한다.
4. sample 파일에 실제 개인정보나 실제 기업 기밀이 없다.

완료 조건:

```bash
pytest tests/test_demo_cases.py
```

명령이 성공해야 한다.

## Phase 7: Chrome Extension

목표:

- 사용자의 paste 행동을 감지하고 Local Agent 판단에 따라 허용/경고/차단한다.

작업:

1. `manifest.json` 생성
2. content script 작성
3. paste 이벤트 감지
4. Local Agent `/analyze` 호출
5. `BLOCK`이면 paste 취소
6. `WARN`이면 사용자 경고
7. `PASS`이면 정상 진행

테스트 케이스:

1. content script의 URL surface 분류 함수 테스트
2. decision이 `BLOCK`일 때 paste 기본 동작을 막는지 테스트
3. decision이 `PASS`일 때 paste를 허용하는지 테스트
4. Local Agent가 꺼져 있으면 사용자에게 오류 메시지를 표시하는지 테스트

완료 조건:

```bash
npm test
```

또는 JS 테스트 환경이 없으면 최소한 핵심 함수 단위 테스트와 수동 검증 체크리스트를 남긴다.

## Phase 8: Demo Upload Page

목표:

- 실제 ChatGPT/Gmail 의존도를 낮추고 영상 촬영용 통제된 페이지를 만든다.

작업:

1. `demo/upload_page.html` 생성
2. paste 영역 생성
3. file upload input 생성
4. extension이 감지할 수 있는 URL 또는 DOM marker 추가
5. 시연용 안내는 최소화하고 실제 동작 중심으로 구성

테스트 케이스:

1. demo page에서 paste 이벤트가 발생한다.
2. extension이 demo page를 `demo_upload` surface로 분류한다.
3. Case A/B/C를 demo page에서 재현할 수 있다.

완료 조건:

- 브라우저에서 demo page를 열고 세 케이스를 수동 검증한다.

## Phase 9: Security Dashboard

목표:

- 보안 담당자가 incident timeline과 AI 판단 근거를 확인할 수 있게 한다.

작업:

1. Streamlit 또는 React 선택
2. incident list 표시
3. incident detail 표시
4. Rule result vs AI result 표시
5. productivity impact metric 표시
6. timeline 표시

테스트 케이스:

1. incident API 응답을 화면에 표시할 수 있다.
2. PASS/WARN/BLOCK 카운트가 표시된다.
3. rule decision과 AI decision이 다르면 명확히 표시된다.
4. evidence와 reason이 표시된다.

완료 조건:

- Case A/B/C 실행 후 Dashboard에서 세 사건을 확인할 수 있다.

## Phase 10: macOS Watcher

목표:

- Chrome Extension 외에 로컬 OS 행동 감시도 보여준다.

작업:

1. clipboard watcher 구현
2. `ExternalUpload` 폴더 watcher 구현
3. 위험 파일 분석
4. `BLOCK` 파일 Quarantine 이동
5. watcher 상태 로그 출력

테스트 케이스:

1. clipboard 변경이 감지된다.
2. `ExternalUpload` 폴더에 파일을 넣으면 감지된다.
3. 위험 파일은 Quarantine으로 이동된다.
4. 안전 파일은 이동되지 않는다.
5. 같은 파일을 반복 감지하지 않는다.

완료 조건:

```bash
pytest tests/test_watchers.py
```

명령이 성공하고, 수동으로 폴더 이동 데모가 가능해야 한다.

## Phase 11: Optional Ollama Provider

목표:

- mock sLM 대신 로컬 LLM Provider를 붙일 수 있는 구조를 만든다.

작업:

1. AI Judge provider interface 정의
2. Mock provider 유지
3. Ollama provider 추가
4. timeout과 fallback 처리
5. 환경 변수로 provider 선택

테스트 케이스:

1. provider가 `mock`이면 mock judge를 사용한다.
2. provider가 `ollama`이고 Ollama가 꺼져 있으면 fallback 또는 명확한 오류를 반환한다.
3. Ollama 응답이 잘못된 JSON이면 안전하게 fallback한다.
4. Case A/B/C는 mock provider에서 항상 재현 가능하다.

완료 조건:

```bash
pytest tests/test_ai_provider.py
```

명령이 성공해야 한다.

## Phase 12: Optional 파일 위험도 분류

목표:

- 파일 자체의 위험도를 행동 분석에 가중치로 반영한다.

작업:

1. 파일명/확장자/content sample 기반 분류
2. `critical`, `high`, `medium`, `low` 등급 부여
3. 위험도별 recommended policy 생성
4. upload 분석 시 파일 위험도 반영

테스트 케이스:

1. 고객 DB CSV는 `critical` 또는 `high`
2. 내부 코드 파일은 `high`
3. 일반 메모 파일은 `low`
4. critical 파일 업로드는 최종 decision 위험도를 높인다.

완료 조건:

```bash
pytest tests/test_file_classifier.py
```

명령이 성공해야 한다.

## 5. 매 작업 시작 전 체크리스트

개발을 시작할 때마다 아래를 확인한다.

1. `MVP.md`에서 현재 범위를 확인한다.
2. 이 문서에서 현재 Phase와 작업 번호를 확인한다.
3. 구현 전에 해당 작업의 테스트 케이스를 먼저 확인한다.
4. 테스트 파일을 만들거나 기존 테스트에 케이스를 추가한다.
5. 구현 후 관련 테스트를 실행한다.
6. 실패 테스트를 남겨둔 채 다음 기능으로 넘어가지 않는다.

## 6. 매 작업 완료 전 체크리스트

작업을 끝내기 전에 아래를 확인한다.

1. 새 기능에 대한 테스트가 있다.
2. 관련 테스트 명령이 성공했다.
3. Case A/B/C 중 영향받는 시나리오가 깨지지 않았다.
4. README 또는 문서 업데이트가 필요한 경우 반영했다.
5. git status를 확인했다.
6. 커밋 메시지는 작업 단위를 설명한다.

## 7. 현재 진행 상태

| Phase | 상태 | 비고 |
| --- | --- | --- |
| Phase 0: 프로젝트 기본 구조 | 대기 | 다음 작업 |
| Phase 1: Local Agent API Skeleton | 대기 |  |
| Phase 2: Rule DLP Baseline | 대기 |  |
| Phase 3: Mock sLM AI Judge | 대기 |  |
| Phase 4: Policy Decision Engine | 대기 |  |
| Phase 5: Incident Store | 대기 |  |
| Phase 6: Demo Samples | 대기 |  |
| Phase 7: Chrome Extension | 대기 |  |
| Phase 8: Demo Upload Page | 대기 |  |
| Phase 9: Security Dashboard | 대기 |  |
| Phase 10: macOS Watcher | 선택 | 시간 남으면 |
| Phase 11: Optional Ollama Provider | 선택 | 시간 남으면 |
| Phase 12: Optional 파일 위험도 분류 | 선택 | 시간 남으면 |

## 8. 다음 작업

다음 작업은 Phase 0이다.

Phase 0에서 할 일:

1. `agent/` Python 패키지 생성
2. `pytest` 설정
3. smoke test 작성
4. 기본 실행 명령 정리

Phase 0을 시작할 때 반드시 먼저 만들 테스트:

1. `tests/test_smoke.py`
2. `agent/app` 모듈 import 테스트
3. test runner 동작 확인

