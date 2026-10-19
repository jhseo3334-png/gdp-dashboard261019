# 🧩 5형식 문장 정복

S(주어)·V(동사)·O(목적어)·C(보어) 블록을 조립하며 영어 1~5형식의 기본 구조를 익히는 Streamlit 실습 앱입니다.

## 실행 방법

Codespaces의 기존 Python 환경에서 터미널에 입력하세요. 가상환경을 만들 필요가 없습니다.

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

실행 후 Codespaces의 포트 8501 미리보기를 여세요.

## 사용 방법

1. S·V·O·C 버튼을 눌러 블록을 추가합니다. 같은 성분도 여러 번 추가할 수 있습니다.
2. 각 블록에 단어 또는 구를 입력하고 Enter를 누르거나 입력 칸 밖을 클릭합니다.
3. ↑·↓ 버튼으로 순서를 바꾸고, ✕ 버튼으로 블록을 삭제합니다.
4. 아래에서 조립한 문장과 형식 판별 결과를 확인합니다.
5. 사이드바의 1~5형식 예제를 눌러 구조를 비교할 수 있습니다. 예제를 선택하면 현재 블록이 교체됩니다.

판별 기준은 S+V, S+V+C, S+V+O, S+V+O+O, S+V+O+C입니다.
선택한 성분 순서를 판별하며, 일부 동사에는 규칙 기반 보완 설명을 제공합니다. 전체 문법 검사 기능은 아닙니다.

메인 코드는 `streamlit_app.py`, 필요한 패키지는 `requirements.txt`에 있습니다.
기존 `data/gdp_data.csv`는 현재 앱에서 사용하지 않습니다.

## 단어 카드와 문장 보완 피드백

- 상단에서 1~5형식 카드 활동을 고르고 단어 카드를 성분 칸으로 끌어 놓으세요.
- 터치 화면이나 키보드에서는 카드를 선택한 뒤 해당 칸의 ‘여기에 놓기’ 버튼을 누를 수 있습니다.
- 칸에 새 카드를 놓으면 기존 카드는 보관함으로 돌아갑니다. ‘카드 활동 다시 시작’으로 초기화합니다.
- ‘힌트와 완성 예시’에서 단어별 역할과 완성 문장을 확인할 수 있습니다.
- 자유 조립에서는 일부 동사와 빈칸에 대해 보완 설명을 제공합니다. 예: `Students read`도 가능하지만 `Students read books`로 읽는 대상을 구체화할 수 있습니다.
- 규칙 기반 학습 피드백이며 모든 영어 문장을 문법 검사하지는 않습니다.

단어 카드는 Streamlit의 기본 컴포넌트 기능을 사용합니다. `requirements.txt`에 기록한 Streamlit 1.66 이상이 필요합니다. 현재 개발 환경에는 이미 설치되어 있으므로 추가 설치하지 않았습니다.

## 🐣 AI 도와줘 연결

모든 활동의 ‘도와줘’에서 단어 뜻, 영작, 번역, 문법, 문장 교정을 질문할 수 있습니다.
이전 답변에 이어 질문할 수 있고, ‘대화 새로 시작’으로 해당 활동의 기록을 비울 수 있습니다.
최근 10회 대화를 유지하며 새로고침 등으로 세션이 종료되면 기록이 사라질 수 있습니다.

### 1. API 키 준비

[OpenAI API 키 관리](https://platform.openai.com/api-keys)에서 본인의 키를 준비하세요.
API는 별도 사용 요금이 발생할 수 있으며 사용량과 결제 상태는 API 계정에서 확인하세요.

### 2. 키 설정 (둘 중 하나)

- **Codespaces:** Codespaces secret 이름을 `OPENAI_API_KEY`로 등록하고 이 저장소에 접근을 허용한 뒤 Codespace를 다시 시작하세요.
- **Streamlit secrets:** `.streamlit/secrets.toml` 파일을 직접 만들고 다음처럼 입력하세요. 이 파일은 이미 `.gitignore`에서 제외되어 있습니다.

```toml
OPENAI_API_KEY = "여기에_본인의_API_키"
OPENAI_MODEL = "gpt-4.1-mini"
```

`OPENAI_MODEL`은 선택 사항입니다. 설정하지 않으면 `gpt-4.1-mini`를 사용합니다.
환경변수와 secrets에 같은 설정이 있으면 환경변수를 우선합니다.
키를 코드, README, 학생 질문 칸에 적거나 GitHub에 커밋하지 마세요.
Streamlit Community Cloud에 배포할 때는 배포 앱의 Secrets에도 설정해야 합니다.

### 3. 실행

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

키가 없으면 기존 규칙 기반 기초 도움말과 내장 단어 사전으로 동작하며, AI 자유 질문은 사용할 수 없습니다.
키를 설정하면 실제 인증·모델 접근 권한은 첫 질문을 보낼 때 확인됩니다.
인증 오류, 사용 한도, 네트워크 오류는 화면에 안내합니다.

OpenAI 공식 Python SDK의 Responses API로 연결합니다.
질문과 최근 대화, 현재 활동 데이터가 OpenAI로 전송되며, 요청에는 `store=False`를 사용합니다.
전체 데이터 보관 정책을 이 옵션 하나로 보장하는 것은 아닙니다. API 응답은 서버에서만 처리하며 API 키는 브라우저로 전달하지 않습니다.
AI 답변은 틀릴 수 있으므로 중요한 학습 내용은 선생님과 확인하세요.

화면은 밝은 파스텔 색상과 둥근 글꼴, 병아리 이모지로 구성했습니다.
Google Fonts의 Jua(제목)·Gowun Dodum(본문)를 불러오며, 연결되지 않으면 기기의 기본 글꼴을 사용합니다.

공식 연결 예제: https://developers.openai.com/api/docs/quickstart
