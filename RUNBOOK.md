# ContextGuard Local MVP 실행 설명서

## 0. 주의사항

API key는 절대 git에 올리지 않는다.

- 실제 key는 `.env`에만 저장한다.
- `.env`는 `.gitignore`에 포함되어 있다.
- GitHub에는 `.env.example`만 올라간다.

확인 명령:

```bash
git check-ignore -v .env
git ls-files .env
```

정상 상태:

- 첫 번째 명령은 `.gitignore` 규칙을 출력한다.
- 두 번째 명령은 아무것도 출력하지 않아야 한다.

## 1. 최초 1회 설정

```bash
cd /Users/hyeokkiyaa/Drive/GoogleAIAgent/Demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` 파일을 열어서 Claude API key를 넣는다.

```env
CONTEXTGUARD_AI_PROVIDER=claude
ANTHROPIC_API_KEY=여기에_Claude_API_Key
CLAUDE_MODEL=claude-haiku-4-5-20251001
CLAUDE_API_BASE=https://api.anthropic.com/v1
CLAUDE_TIMEOUT_SECONDS=8
```

데모 비용을 낮추기 위해 기본 모델은 `Claude Haiku 4.5`로 둔다.

## 2. 테스트 실행

Python 테스트:

```bash
source .venv/bin/activate
pytest
```

JavaScript 테스트:

```bash
npm test
```

현재 기대 결과:

```text
pytest: 49 passed
npm test: 11 passed
```

테스트는 실제 Claude API를 호출하지 않는다. 테스트 환경에서는 mock provider를 사용하도록 고정되어 있다.

## 3. 서버 실행

터미널 1: Local Agent API

```bash
cd /Users/hyeokkiyaa/Drive/GoogleAIAgent/Demo
source .venv/bin/activate
uvicorn agent.app.main:app --reload --host 127.0.0.1 --port 8765
```

정상 확인:

```bash
curl http://127.0.0.1:8765/health
```

기대 결과:

```json
{"status":"ok"}
```

터미널 2: Demo/Dashboard 정적 서버

```bash
cd /Users/hyeokkiyaa/Drive/GoogleAIAgent/Demo
python3 -m http.server 8081
```

브라우저에서 연다:

```text
http://127.0.0.1:8081/demo/upload_page.html
http://127.0.0.1:8081/dashboard/index.html
```

## 4. Chrome Extension 로드

1. Chrome에서 `chrome://extensions`를 연다.
2. Developer mode를 켠다.
3. Load unpacked를 누른다.
4. 아래 폴더를 선택한다.

```text
/Users/hyeokkiyaa/Drive/GoogleAIAgent/Demo/extension
```

## 5. 데모 실행 순서

1. Local Agent API 서버를 켠다.
2. 정적 서버를 켠다.
3. Chrome Extension을 로드한다.
4. Upload Demo 페이지를 연다.
5. Dashboard 페이지를 옆에 연다.
6. Upload Demo에서 Case A/B/C 버튼을 눌러 샘플을 클립보드에 복사한다.
7. textarea에 붙여넣는다.
8. Dashboard에서 incident timeline과 Rule vs AI 결과를 확인한다.

## 6. 기대 시나리오

### Case A

개인 이력서에 본인 주민등록번호가 들어간 케이스.

```text
Rule DLP: BLOCK
Claude/AI Judge: PASS 또는 WARN
Final Decision: WARN
Impact: prevented_false_positive
```

영상 포인트:

- 룰만 쓰면 차단될 수 있는 개인 문맥을 AI가 완화한다.
- 최종 결과는 경고 후 사용자가 계속 진행할 수 있다.

### Case B

영업팀의 잠재 고객 명단을 외부 이메일 맥락에 붙여넣는 케이스.

```text
Rule DLP: PASS
Claude/AI Judge: BLOCK
Final Decision: BLOCK
Impact: prevented_false_negative
```

영상 포인트:

- 주민등록번호가 없어 룰은 놓친다.
- AI가 고객 DB/영업 리드 목록으로 판단해 차단한다.

### Case C

사내 코드 식별자와 내부 함수명을 ChatGPT 맥락에 붙여넣는 케이스.

```text
Rule DLP: PASS
Claude/AI Judge: BLOCK
Final Decision: BLOCK
Impact: prevented_false_negative
```

영상 포인트:

- 개인정보가 없어 룰은 놓친다.
- AI가 내부 IP 식별자와 코드 맥락을 근거로 차단한다.

## 7. Claude 실제 호출 확인

서버 실행 후 아래 명령으로 실제 Claude provider 경로를 확인할 수 있다.

```bash
curl -s http://127.0.0.1:8765/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "source": "chrome_extension",
    "surface": "chatgpt",
    "event_type": "browser_paste",
    "content_type": "text",
    "content": "Debug TraceForgePolicyResolver and customerRiskScorerV2 in hf_internal_pricing_engine."
  }'
```

응답의 `ai_result.evidence`에 `claude_fallback`이 없으면 Claude 호출이 정상 처리된 것이다.

만약 `claude_fallback`이 있으면 다음을 확인한다.

1. `.env`의 `ANTHROPIC_API_KEY`
2. 서버를 `.env` 수정 후 재시작했는지
3. 네트워크 연결
4. Anthropic billing 또는 API key 권한

## 8. 서버 종료

실행 중인 터미널에서 `Ctrl+C`.

포트로 강제 종료해야 할 때:

```bash
lsof -ti tcp:8765 | xargs kill
lsof -ti tcp:8081 | xargs kill
```

포트 확인:

```bash
lsof -ti tcp:8765 || true
lsof -ti tcp:8081 || true
```

아무것도 출력되지 않으면 종료된 상태다.

