# 데모 영상 스크립트 (3분 이내)

> 촬영: 화면 녹화(QuickTime/OBS) + 마이크 내레이션. 1080p 이상.
> 화면 구성: 왼쪽 터미널, 오른쪽 브라우저(DataHub UI) 추천.

## 0:00–0:25 — 문제 제기 (후킹)

**화면**: DataHub UI에 `tags:unscanned` 검색 결과 22건.

**내레이션(예시)**:
"Since April 2026, US state and local governments are legally required to make
their web content accessible. But a typical city publishes thousands of PDFs
across dozens of departments — and nobody knows which ones are compliant,
who owns them, or what to fix first. This is AccessCatalog Agent: it turns
DataHub into the compliance system of record, and lets an agent do the work."

## 0:25–0:50 — 카탈로그 모델 (DataHub가 왜 필수인지)

**화면**: 문서 하나 클릭 (예: Adopted Budget FY2026) →
- Domain(Finance), Owner(susan.chen) 표시
- **Lineage 탭**: 원본 → Accessible Edition 리니지 그래프
- Properties: publicFacing, monthlyViews

**내레이션**:
"Every PDF is a first-class DataHub entity. Departments are domains with real
owners. And here's the key: remediation history is lineage — this budget PDF
already has an accessible edition downstream."

## 0:50–1:50 — 에이전트 실행 (메인)

**화면**: 터미널에서 `accesscatalog agent` 실행. 로그가 흐르는 동안
DataHub UI를 새로고침하며 태그가 바뀌는 걸 보여줌:
`unscanned` → `508-non-compliant` / `508-compliant` → `in-remediation`

**내레이션**:
"The agent reads the catalog through DataHub's MCP server, finds everything
unscanned, and runs real PDF accessibility checks — tag structure, document
title, language, image-only scans. Verdicts are written straight back to
DataHub as tags and evidence properties. Watch the catalog update live.
Then it prioritizes: public-facing documents first, ranked by traffic and
severity. And because it reads lineage, it catches something a spreadsheet
never would — this budget PDF is inaccessible, but an accessible edition
already exists. So instead of paying to remediate it twice, the agent
recommends a URL redirect. The guardrails in its tools enforce this: compliant,
internal, or already-remediated documents are rejected from the queue."

**포인트 샷**: 문서 상세 페이지에서 Properties에 accessibilityScore,
failedChecks, lastScannedAt 찍힌 것 클로즈업.

## 1:50–2:30 — 산출물

**화면**:
1. `reports/remediation_queue.json` 잠깐 보여주고
2. `compliance_report.html` 열어서 스크롤 (부서별 표, 큐, 리다이렉트 권고)
3. `accesscatalog status` 터미널 표

**내레이션**:
"The output: a prioritized remediation queue with rationale for every position,
and department-level compliance reports — with named owners, generated entirely
from live catalog state. Not a snapshot in a spreadsheet: a view over metadata
that stays current."

## 2:30–2:55 — 마무리

**화면**: README 아키텍처 다이어그램 → DataHub UI 전경.

**내레이션**:
"Read through MCP, act with real scans, write back so the next person — or the
next agent — inherits verified knowledge. That's the loop. AccessCatalog Agent,
built on DataHub. Thanks for watching."

---

## 촬영 전 체크리스트

- [ ] `bootstrap` 리셋 → 카탈로그가 unscanned 22건 상태인지
- [ ] DataHub UI 로그인 상태, 다크모드 여부 통일
- [ ] `.env` 준비, 터미널 폰트 크게 (시청자 가독성)
- [ ] 에이전트 실행은 실시간이 길면 편집으로 점프컷
- [ ] 업로드: YouTube 공개(Public) — 링크 제출
