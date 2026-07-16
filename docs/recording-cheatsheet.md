# 데모 영상 촬영 치트시트 (완전 초보용)

목표: 3분 이하 영상 1개. 클립 2개를 찍어서 iMovie로 붙인다.

---

## 0. 촬영 전 준비 (5분)

1. **Claude한테 "촬영 준비해줘"라고 말하기** → 카탈로그를 unscanned 초기 상태로 리셋해줌
2. **터미널 열기** (Spotlight에서 "터미널" 검색)
   - 글자 크게: `Cmd` + `+` 를 4~5번 눌러서 큼직하게
   - 아래 두 줄 미리 실행 (이건 녹화에 안 들어감):
     ```
     cd ~/Desktop/hackathon
     source .venv/bin/activate
     ```
3. **크롬(또는 사파리) 열기** → 주소창에 `localhost:9002`
   - 아이디 `datahub` / 비밀번호 `datahub` 로그인 (미리 해두기)
4. **화면 배치**: 왼쪽 절반 터미널, 오른쪽 절반 브라우저
   (창을 화면 왼쪽 끝으로 드래그하면 반반 배치됨)
5. 알림 끄기: 화면 오른쪽 위에서 아래로 쓸어내려 제어센터 → 집중 모드 → 방해금지 ON
   (녹화 중 카톡 알림 뜨면 대참사)

---

## 1. 녹화 방법 (Mac 내장 기능)

- **`Cmd + Shift + 5`** 누르면 화면 아래에 녹화 도구가 뜸
- "**전체 화면 기록**" 아이콘 선택 (점선 네모 + ⏺ 모양)
- **옵션** 클릭:
  - 내레이션 할 거면 → 마이크: **내장 마이크** 선택
  - 안 할 거면 → 마이크: 끔 (무음도 규정상 OK)
- **기록** 버튼 클릭 → 녹화 시작
- **끝낼 때**: 화면 맨 위 메뉴바의 ⏹(정지) 버튼 클릭
- 파일은 데스크탑에 `.mov`로 자동 저장됨

---

## 2. 클립 1 촬영 (~90초)

녹화 시작하고, 아래 순서대로:

| 순서 | 하는 것 | 말할 것 (선택, 영어) |
|---|---|---|
| 1 | 터미널에 `accesscatalog status` 입력+엔터 → 표에 Unscanned 22 보임 | "A city publishes thousands of PDFs. Since April 2026, US law requires them to be accessible. Nobody knows which ones are — until now." |
| 2 | 브라우저: DataHub 검색창에 `tags:unscanned` 입력+엔터 → 22건 | "Every document is a first-class entity in DataHub — with owners, departments, and lineage." |
| 3 | 검색결과에서 **Adopted Budget Fiscal Year 2026** 클릭 → **Lineage** 탭 클릭 → 그래프 보여주기 (3초 머물기) | "This budget PDF already has an accessible edition — that's lineage." |
| 4 | 터미널로 돌아와서 `accesscatalog agent` 입력+엔터 → 로그 흐르기 시작 → 5초 정도 보여주기 | "Now the agent takes over: it reads the catalog through DataHub's MCP server and runs real PDF accessibility scans." |
| 5 | **녹화 정지** (메뉴바 ⏹) | |

→ 이제 에이전트가 끝날 때까지 4~5분 기다림 (녹화 안 함).
   터미널에 "Done. Scanned 22 documents, queued 10..." 뜨면 끝난 것.

## 3. 클립 2 촬영 (~90초)

다시 `Cmd+Shift+5` → 기록, 아래 순서대로:

| 순서 | 하는 것 | 말할 것 (선택) |
|---|---|---|
| 1 | 터미널 스크롤해서 "Done. Scanned 22 documents, queued 10 for remediation" 보여주기 | "22 documents scanned, verdicts written back to DataHub." |
| 2 | 브라우저: `tags:unscanned` 재검색 → **0건**. 이어서 `tags:in-remediation` 검색 → 10건 | "The catalog updated live — nothing unscanned left." |
| 3 | 목록에서 문서 하나 클릭 (예: Snow and Ice Response Plan) → 아래 **Properties** 쪽에 `accessibilityScore`, `failedChecks`, `remediationQueuePosition` 보여주기 | "Every verdict comes with evidence — and a queue position, prioritized by public impact. Documents with an accessible edition get a redirect recommendation instead — no duplicate work." |
| 4 | 터미널: `accesscatalog status` → 색깔 표 | "Department-level posture, with named owners." |
| 5 | 터미널: `open reports/compliance_report.html` → 리포트 천천히 스크롤 (KPI → 부서표 → 큐 → 리다이렉트 권고) | "And a compliance report generated entirely from live catalog state. Read through MCP, act, write back — that's the loop. AccessCatalog Agent, built on DataHub." |
| 6 | **녹화 정지** | |

---

## 4. iMovie로 합치기 (10분)

1. **iMovie** 열기 (Spotlight에서 검색, Mac에 기본 설치)
2. **새로 만들기 → 동영상**
3. 데스크탑의 `.mov` 파일 2개를 iMovie 창 안으로 **드래그**
4. 클립 1 → 클립 2 순서로 아래 **타임라인**에 드래그
5. (선택) 클립 앞뒤 어색한 부분: 타임라인에서 클립 경계를 드래그하면 잘림
6. 오른쪽 위 **공유(⬆️) → 파일 내보내기** → 해상도 1080p → 저장
7. 총 길이가 **3:00 미만**인지 확인!

## 5. YouTube 업로드 (5분)

1. [youtube.com](https://youtube.com) 로그인 → 오른쪽 위 **카메라(+) → 동영상 업로드**
2. iMovie에서 내보낸 파일 선택
3. 제목: `AccessCatalog Agent — DataHub Agent Hackathon Demo`
4. 아동용 아님 선택
5. 공개 범위: **공개(Public)** ← 꼭! (일부공개/비공개면 실격 사유)
6. 업로드 완료 후 **링크 복사** → Devpost 제출 폼에 붙여넣기

---

## 자주 하는 실수

- ❌ 녹화 전에 카탈로그 리셋 안 함 → "before" 장면이 안 나옴
- ❌ 터미널 글자가 작아서 안 보임 → `Cmd +` 로 크게
- ❌ 유튜브 "일부공개(Unlisted)"로 올림 → **공개(Public)** 필수
- ❌ 3분 초과 → iMovie에서 잘라내기
- ❌ OrbStack 꺼놓고 촬영 시작 → DataHub 안 떠서 에러
