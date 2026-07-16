# 데모 영상 촬영 계획안 — 2분 25초 몰입형 (최종, Acrobat 장면 포함)

- 총 길이: **~2:25** (2:30 상한 딱 안쪽 — 길어지면 장면 8 리포트 훑기를 줄일 것)
- 클립 2개로 촬영: **클립 A** (장면 1–5, ~1:30) → 에이전트 기다림(녹화 X) → **클립 B** (장면 6–8, ~55초)
- 몰입 설계: 퀴즈 콜드오픈 → 스테이크 → 지옥 → 해결 예고("you'll see") → 라이브 실행 → 반전("거부했다, 왜?") → 회수
- 내레이션 전부 영어. 속도는 "약간 빠르게, 끊어치기". 아래 대본 그대로 읽으면 됨.

---

## 촬영 전 준비 (녹화 안 함)

1. Claude에게 "촬영 준비해줘" → 카탈로그 unscanned 22건 리셋 + 헬스체크
2. 터미널: `cd ~/Desktop/hackathon && source .venv/bin/activate`, 글자 크게(`Cmd +`)
3. **미리 스캔 2개 돌려놓기** (장면 2에서 스크롤로 보여줄 것):
   ```
   accesscatalog scan corpus/pdfs/pw-snow-plan.pdf
   accesscatalog scan corpus/pdfs/pr-summer-programs.pdf
   ```
4. **Adobe Acrobat으로 PDF 2개 열어두기** (장면 1–2용):
   `corpus/pdfs/pw-snow-plan.pdf` + `corpus/pdfs/pr-summer-programs.pdf`
   - 각 문서에서 **태그 패널** 열기: 메뉴 **View > Show/Hide >
     Navigation Panes > Accessibility Tags** (구버전 UI면 `Tags`)
     — 왼쪽에 트리 패널이 붙음
   - `pr-summer-programs.pdf` → **트리가 펼쳐짐** (Document 아래 H1, H2, P, Table…)
     ← 미리 ▸ 눌러서 몇 단계 펼쳐두기 (녹화 중 허둥대지 않게)
   - `pw-snow-plan.pdf` → **"No Tags Available"** 한 줄만 뜸
   - 두 창을 `Cmd + \`` 로 전환하는 것 연습해두기
5. 크롬: `localhost:9002` 로그인(datahub/datahub) 해두기
6. 방해금지 모드 ON

---

# 클립 A (~1:20)

## 장면 1 — 콜드오픈: 퀴즈 (0:00–0:14) 🎣 궁금증 발사

**화면**: Acrobat으로 연 PDF 2개 나란히 (태그 패널은 아직 닫아두거나 가려둠 —
정답을 미리 흘리지 않기). 마우스로 번갈아 가리키기.

**대본**:
> "Here are two government documents. They look identical. But one of them
> is completely invisible to a blind person using a screen reader.
> Can you tell which? ... Neither can anyone else. Not by looking."

**연출**: "Can you tell which?" 뒤에 1초 멈춤 (시청자가 진짜 고민하게).

## 장면 2 — 정답 공개: Acrobat 태그 패널 + 스캐너 (0:14–0:45) 💥 첫 페이오프

**화면**:
1. `pr-summer-programs.pdf`의 **Accessibility Tags 패널** 보여주기 —
   트리 펼쳐진 상태 (Document → H1, P, Table…) 마우스로 훑기 (5초)
2. `Cmd + \``로 `pw-snow-plan.pdf` 전환 → 태그 패널에 **"No Tags Available"**
   덩그러니 (5초, 이게 정답 공개 순간)
3. 터미널 전환 → 미리 돌려둔 스캔 결과 스크롤:
   snow-plan **score 0 / NON-COMPLIANT** → summer-programs **100 / COMPLIANT** (8초)

**대본**:
> "The difference is buried inside the file. Open them in Acrobat — this one
> has a full structure tree: headings, paragraphs, tables. That's what a
> screen reader actually walks through. And this one? 'No tags available.'
> Literally nothing to read. That's the manual check — and it's
> machine-detectable too: our scanner scores them zero… and one hundred.
> And this is now law: the DOJ's ADA Title II rule requires every US state
> and local government to make its documents accessible, with deadlines from
> April 2027 — deadlines the DOJ just extended a full year, for one reason:
> nobody is ready. Meanwhile, publish one broken file — complaints, even
> lawsuits. Advocates are already suing over the delay."

**연출**: "No tags available" 화면에서 반 박자 멈춤 — 텅 빈 패널이 말하게 두기.
Acrobat(사람이 손으로 확인하는 방식) → 스캐너(기계로 잡는 방식) 순서가 포인트:
다음 장면의 "수천 개를 손으로?"가 자연스럽게 이어진다.

## 장면 3 — 무한루프 지옥 (0:45–1:00) 😱 스케일 업

**화면**: 터미널 `ls corpus/pdfs/` → 파일명 목록 쭉 (Finder 클릭 장면은 생략,
시간 절약 — 파일명 목록만으로 충분).

**대본**:
> "Now scale that up. A city publishes thousands of PDFs. Filenames tell you
> nothing — so someone opens every file in Acrobat, one by one, by hand.
> And there's nowhere to write the answer down. Next month, a new batch —
> start over. Opening, squinting, forgetting, re-checking. Forever."

**연출**: "Forever."에서 뚝 끊기. (다음 장면의 해결책이 극적으로 들리게)

## 장면 4 — 해결책: DataHub + 반전 예고 (1:00–1:18) 🧠 "you'll see"

**화면**: 크롬 DataHub → **Adopted Budget Fiscal Year 2026** 문서 페이지:
Owner(susan.chen)·Domain(Finance) 짚기 → **Lineage 탭** 클릭 → 그래프 3초.

**대본**:
> "So we gave every document a memory: DataHub. Each PDF becomes a catalog
> entity — with an owner, a department, and lineage. And it has to be
> DataHub: the catalog is shared memory that agents and people inherit,
> lineage powers the agent's smartest decision — you'll see it in a moment —
> and the MCP Server is how an agent reads this entire graph."

**연출**: "you'll see it in a moment" ← 복선. 시청자를 장면 7까지 끌고 간다.

## 장면 5 — 에이전트 발사 (1:18–1:30) 🚀 클립 A 마무리

**화면**: 터미널 → `accesscatalog agent` 입력+엔터 → 로그 흐르는 것 6~7초.

**대본**:
> "Now watch the agent work. It searches the catalog through MCP for
> everything unscanned — twenty-two documents — and runs a real
> accessibility scan on every single one."

**⏹ 녹화 정지.** 터미널에 `Done. Scanned 22 documents, queued 10...` 뜰 때까지
4~5분 대기 (녹화 안 함).

---

# 클립 B (~55초)

## 장면 6 — 페이오프: 그래프에 되쓰기 (1:30–1:55) ✅ 루프 회수

**화면**:
1. 터미널 "Done. Scanned 22 documents, queued 10" 보여주기 (2초)
2. 크롬: `tags:unscanned` 재검색 → **0건**
3. 문서 하나 클릭 (Snow and Ice Response Plan) → Properties 스크롤:
   `accessibilityScore: 0`, `failedChecks`, `remediationQueuePosition`

**대본**:
> "Four minutes later: every document scanned, and the verdicts written back
> into DataHub as tags — with evidence. The score. Exactly which checks
> failed. When. Remember that infinite loop? Gone. Nothing unscanned is
> left — this knowledge is permanent now, for the next person or the next
> agent."

## 장면 7 — 반전: 거부하는 에이전트 (1:55–2:12) 🤯 복선 회수 (하이라이트)

**화면**: `open reports/compliance_report.html` → **Redirect recommendations**
섹션으로 스크롤 (Adopted Budget FY2026 항목).

**대본**:
> "But here's the clever part. This budget PDF failed its scan — yet the
> agent refused to queue it for repair. Why? Lineage. The graph knows an
> accessible edition already exists. So instead of paying to fix it twice:
> just redirect the link. A spreadsheet could never make that call."

**연출**: "refused" 강조. "Why?" 뒤 반 박자 쉬기. 장면 4의 복선이 여기서 터짐.

## 장면 8 — 클로즈 (2:12–2:25) 🎬

**화면**: 리포트 위로 스크롤 — KPI 타일 → 부서표 → 큐(1~10) 훑기 →
마지막에 README 상단(제목+아키텍처) 또는 repo URL 텍스트 3초.

**대본**:
> "What's left is a prioritized queue — public documents first, routed to
> real owners — and a compliance report built from live catalog state.
> Read through MCP. Act. Write back. The loop only closes because it's
> built on DataHub. AccessCatalog Agent."

---

## 편집 (iMovie)

1. 클립 A + 클립 B 순서로 타임라인에
2. 총 길이 2:10~2:20 확인 (2:30 넘으면 장면 3의 Finder 부분부터 컷)
3. 내보내기 1080p → YouTube **공개(Public)** 업로드
4. YouTube 설명란에 GitHub repo URL 넣기

## 채점 기준 커버 확인

| 기준 | 장면 |
|---|---|
| ① Use of DataHub (그래프 기여) | 4 (모델링·필수성) + 6 (write-back 라이브) |
| ② Technical Execution | 2 (진짜 스캔) + 5–6 (end-to-end 라이브) |
| ③ Originality | 4 (문서=엔티티) + 7 (리니지 리다이렉트) |
| ④ Real-World Usefulness | 1–3 (법·무한루프) + 8 (큐·오너·리포트) |
| ⑤ Submission Quality | 전체 구성 + 클로즈 |
| ⑥ OSS 기여 (보너스) | 영상 밖 — 제출 텍스트에서 |
