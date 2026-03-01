# oh-my-linearmcp TODOs

## Phase 1: UX 핵심 개선 (Confirmed)

### 1. MCP Reconnect 시 캐시 자동 갱신
- **What:** `/mcp` 재연결 시 로컬 캐시를 자동으로 refresh하는 lifecycle handler 추가
- **Why:** 현재 reconnect 후 최대 5분간 stale 데이터가 반환됨. 사용자가 수동으로 `refresh_cache`를 호출해야 하는 문제
- **Context:**
  - `server.py`에 MCP `initialize` lifecycle hook 추가 (FastMCP 지원 확인 필요)
  - hook 미지원 시 `_force_next_refresh` 플래그로 대체 (1B 펴백)
  - `try/except`로 감싸서 refresh 실패 시 degraded로 시작 (서버 블로킹 방지)
  - 관련 코드: `server.py` (handler 추가), `reader.py:147` (`refresh_cache`)
- **Tests needed:**
  - reconnect → refresh → healthy 성공 케이스
  - reconnect → refresh 실패 → degraded 시작 케이스
- **Depends on:** 없음

### 2. failure_count 리셋
- **What:** `_set_healthy()` 호출 시 `failure_count = 0`으로 리셋
- **Why:** 현재 복구 후에도 failure_count가 계속 누적되어 health 지표가 실제 상태를 반영하지 않음. official MCP의 `_record_success()`는 이미 리셋하고 있어서 비대칭
- **Context:**
  - `reader.py:125-128`의 `_set_healthy()`에 1줄 추가: `self._health.failure_count = 0`
  - official MCP 참고: `official_session.py:253`
- **Tests needed:**
  - `_set_healthy()` 호출 후 `failure_count == 0` 검증
- **Depends on:** 없음

### 3. 21개 로컬 Tool Docstring 추가
- **What:** `server.py`의 21개 로컬 read tool에 개별 docstring 작성
- **Why:** docstring이 없으면 Claude가 파라미터 의미/허용값/응답 구조를 모름. 실제로 `get_project("agentspedia-engine")`이 null 반환된 사례 발생. FastMCP는 docstring을 MCP tool description으로 자동 노출
- **Context:**
  - 대상: `server.py:58-186`의 21개 `@mcp.tool()` 함수
  - 각 docstring에 포함할 내용: 파라미터 의미, 허용값 (이름 vs ID vs enum), 응답 구조
  - 모범 사례: `official_call_tool` docstring (server.py:189)
  - 파라미터 응답 구조는 `local_handlers.py`의 각 핸들러 반환값 참고
- **Tests needed:** 없음 (문서만)
- **Depends on:** 없음

---

## Phase 2: 안정성 개선 (Deferred)

### 4. Stale 데이터 메타데이터 플래그
- **What:** fallback으로 stale 데이터 반환 시 응답에 `_metadata.stale: true` 추가
- **Why:** 현재 stale 데이터가 fresh 데이터와 동일한 구조로 반환됨. 사용자/Claude가 데이터 신선도를 판단할 수 없음
- **Context:**
  - `router.py:110, 123`에서 `allow_degraded=True`로 stale 반환하는 2개 코드패스
  - `local_handlers.py`의 반환 dict에 `_metadata` 키 주입 방식 검토 필요
  - 응답 contract 변경이므로 하위 호환성 고려 필요
- **Depends on:** 없음

### 5. reader.py + store_detector.py 테스트 추가
- **What:** 코드의 41%를 차지하는 핵심 모듈(reader.py 1121줄, store_detector.py 210줄)에 단위 테스트 추가
- **Why:** IndexedDB 파싱, health 상태 전환, account scope 적용, store shape matching 등 핵심 로직이 미테스트. Linear.app 업데이트로 DB 포맷이 바뀌면 silent regression 발생 가능
- **Context:**
  - 현재 32개 테스트가 있지만 reader/store_detector는 미커버
  - Mock LevelDB 데이터로 테스트하거나, fixture 파일로 실제 DB 스냅샷 사용
  - `conftest.py`의 `MiniReader` fixture를 확장하여 reader 초기화 테스트 가능
  - 테스트 대상: `_reload_cache()`, `_load_from_store()`, `detect_stores()`, `_set_degraded()`/`_set_healthy()` 상태 전환, `_apply_account_scope()`
- **Depends on:** 없음

### 6. GitHub Actions CI 파이프라인
- **What:** PR/push 시 자동 pytest + ruff 실행하는 GitHub Actions workflow 추가
- **Why:** 현재 테스트/린팅이 수동 실행에 의존. Breaking change가 검증 없이 머지될 수 있음
- **Context:**
  - `.github/workflows/ci.yml` 신규 생성
  - `uv sync --group dev && uv run pytest && uv run ruff check` 실행
  - Python 3.10+ 매트릭스 테스트 권장
  - pre-commit hook도 함께 고려 가능 (`.pre-commit-config.yaml`)
- **Depends on:** #5 (테스트가 충분해야 CI가 의미 있음)
