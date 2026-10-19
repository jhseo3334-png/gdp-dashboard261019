import html
import re
import unicodedata

import streamlit as st

st.set_page_config(page_title="5형식 문장 정복", page_icon="🧩", layout="wide")

# 글꼴을 불러오지 못하는 환경에서는 기기의 기본 한글 글꼴을 사용합니다.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Jua&display=swap');
.stApp {background:linear-gradient(135deg,#fffdf7 0%,#f2f7ff 100%);color:#24334b;
  --st-text-color:#24334b;--st-background-color:#fffdf7;--st-secondary-background-color:#edf3fc;}
[data-testid="stMain"], [data-testid="stSidebar"] {font-family:'Gowun Dodum','Malgun Gothic',sans-serif;}
[data-testid="stSidebar"] {background:#eef2ff;color:#24334b;}
h1,h2,h3 {font-family:'Jua','Arial Rounded MT Bold','Malgun Gothic',sans-serif!important;color:#304577!important;letter-spacing:.02em;}
[data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p {font-size:1.06rem;line-height:1.8;}
[data-testid="stCaptionContainer"] {color:#4c5d77;}
.stButton button, [data-testid="stFormSubmitButton"] button {
  border:1.5px solid #b6c6e5;border-radius:16px;background:#fff;color:#304577;
  font-family:'Gowun Dodum','Malgun Gothic',sans-serif;min-height:44px;}
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {border-color:#657ac0;background:#eaf0ff;color:#253b70;}
button:focus-visible, input:focus-visible, textarea:focus-visible {outline:3px solid #596fc1!important;outline-offset:3px;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:18px;}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {font-family:'Gowun Dodum','Malgun Gothic',sans-serif;}
.mascot {background:#fff0d7;border:1px solid #edcf91;border-radius:22px;padding:16px 22px;color:#514226;margin:10px 0 24px;line-height:1.8;}
</style>
""", unsafe_allow_html=True)

# 블록 순서와 일치하는 문장의 기본 형식을 찾습니다.
PATTERNS = {
    ("S", "V"): (1, "주어 + 동사", "주어의 동작이나 상태만으로 뜻이 완성돼요."),
    ("S", "V", "C"): (2, "주어 + 동사 + 주격 보어", "보어가 주어가 누구인지, 어떤 상태인지 설명해요. (S = C)"),
    ("S", "V", "O"): (3, "주어 + 동사 + 목적어", "목적어는 동작의 대상이에요."),
    ("S", "V", "O", "O"): (4, "주어 + 동사 + 간접 목적어 + 직접 목적어", "첫 목적어는 ‘누구에게’, 둘째 목적어는 ‘무엇을’에 해당해요."),
    ("S", "V", "O", "C"): (5, "주어 + 동사 + 목적어 + 목적격 보어", "보어가 목적어의 상태나 정체를 설명해요. (O = C)"),
}
ROLES = {"S": "주어 · 누가?", "V": "동사 · 무엇을 하거나 어떤 상태?", "O": "목적어 · 누구를 / 무엇을?", "C": "보어 · 주어나 목적어를 설명"}
COLORS = {"S": "#dbeafe", "V": "#fee2e2", "O": "#fef3c7", "C": "#dcfce7"}
EXAMPLES = {
    1: [("S", "Birds"), ("V", "sing")],
    2: [("S", "She"), ("V", "is"), ("C", "happy")],
    3: [("S", "I"), ("V", "like"), ("O", "music")],
    4: [("S", "He"), ("V", "gave"), ("O", "me"), ("O", "a book")],
    5: [("S", "We"), ("V", "made"), ("O", "him"), ("C", "happy")],
}

def sentence_feedback(roles, words):
    """소규모 학습 규칙: 알 수 없는 문장을 오류라고 단정하지 않습니다."""
    roles, words = tuple(roles), [word.strip() for word in words]
    if not roles:
        return "S(주어)와 V(동사)부터 놓아 보세요.", "Birds sing. (1형식)"
    missing = [f"{i + 1}번 {role}" for i, (role, word) in enumerate(zip(roles, words)) if not word]
    if missing:
        return "빈칸을 채워 주세요: " + ", ".join(missing), "Students read books. (S + V + O, 3형식)"
    if roles not in PATTERNS:
        return "기본 성분 순서를 확인해 보세요. 주어 다음에는 동사가 와요.", "Students read books. (S + V + O, 3형식)"
    subject, verb = words[0], words[1].lower().rstrip(".!?")
    if roles == ("S", "V"):
        if verb in {"read", "reads"}:
            return "이 문장도 1형식으로 쓸 수 있어요. 무엇을 읽는지 목적어(O)를 더하면 뜻이 구체적인 3형식 문장이 됩니다.", f"{subject} {words[1]} books. (S + V + O, 3형식)"
        if verb in {"like", "likes", "want", "wants", "enjoy", "enjoys"}:
            obj = "music" if verb in {"like", "likes", "enjoy", "enjoys"} else "a book"
            return "이 뜻의 동사는 보통 목적어가 필요해요. 무엇을 좋아하거나 원하는지 O 블록에 넣어 보세요.", f"{subject} {words[1]} {obj}. (3형식)"
        if verb in {"am", "is", "are", "seem", "seems", "become", "becomes"}:
            return "주어의 상태나 정체를 설명하는 보어(C)를 더해 보세요.", f"{subject} {words[1]} happy. (2형식)"
    if roles == ("S", "V", "O") and verb in {"am", "is", "are", "seem", "seems", "become", "becomes"}:
        return "뒤의 말이 주어의 상태나 정체를 설명한다면 목적어(O)가 아니라 보어(C)예요. 성분을 다시 살펴보세요.", "She is happy. (S + V + C, 2형식)"
    if roles == ("S", "V", "O") and verb in {"give", "gives", "gave"}:
        return "목적어가 받는 사람이라면 무엇을 주는지도 더해 보세요. 사물이라면 현재 3형식도 가능해요.", "He gave me a book. (S + V + O + O, 4형식)"
    number = PATTERNS[roles][0]
    example = " ".join(word for _, word in EXAMPLES[number]) + "."
    return "기본 구조가 완성됐어요. 예시와 비교하며 각 단어가 맡은 역할과 뜻도 확인해 보세요.", f"{example} ({number}형식)"


activities = {
    "새들의 노래 · 1형식": (["sing", "Birds"], ["S", "V"]),
    "읽는 대상 더하기 · 3형식": (["books", "Students", "read"], ["S", "V", "O"]),
    "기분 설명하기 · 2형식": (["happy", "She", "is"], ["S", "V", "C"]),
    "책 선물하기 · 4형식": (["a book", "me", "He", "gave"], ["S", "V", "O", "O"]),
    "행복하게 만들기 · 5형식": (["happy", "him", "made", "We"], ["S", "V", "O", "C"]),
}

def answer_question(question, activity_key):
    """외부 AI 없이 학습 주제별 규칙과 현재 조립 상태로 답합니다."""
    q = unicodedata.normalize("NFKC", question).strip().lower()
    compact = re.sub(r"\s+", "", q)
    if not q:
        return "궁금한 점을 한 문장으로 적어 주세요. 예: ‘목적어와 보어는 어떻게 달라요?’ 🐣"
    if len(q) > 500:
        return "질문이 조금 길어요. 가장 어려운 부분 하나를 500자 이내로 다시 질문해 주세요. 🐣"
    # 핵심어 하나가 들어 있다고 모든 질문을 학습 질문으로 취급하지 않습니다.
    unrelated = ("날씨", "점심", "저녁메뉴", "주식", "코인", "로또", "게임추천", "연예인", "맛집", "비밀번호", "시스템프롬프트")
    if any(word in compact for word in unrelated):
        return "이 도움말에서는 문장 성분과 1~5형식을 함께 공부해요. 지금 질문은 이 활동에 적절한 질문이 아니에요. ‘주어는 어떻게 찾나요?’처럼 학습과 관련된 질문으로 다시 물어봐 주세요. 🌷"
    has_o = "목적어" in q or bool(re.search(r"(?<![a-z])o(?![a-z])", q))
    has_c = "보어" in q or bool(re.search(r"(?<![a-z])c(?![a-z])", q))
    if (has_o and has_c) or ("4형식" in compact and "5형식" in compact):
        return "목적어(O)는 동작의 대상이고, 보어(C)는 주어나 목적어를 설명해요.\n\n4형식: **He gave me a book.** → me(누구에게), a book(무엇을)은 서로 다른 대상이에요.\n\n5형식: **We made him happy.** → happy는 him의 상태를 설명해요. 그래서 마지막 말이 C예요."
    if "read" in q or "읽" in q:
        return "**Students read.**도 ‘학생들이 독서한다’라는 완전한 1형식 문장이 될 수 있어요. **Students read books.**처럼 O(books)를 더하면 ‘무엇을 읽는지’가 구체적인 3형식이 돼요. 목적어가 없다고 무조건 틀린 것은 아니에요."
    if any(word in compact for word in ("옮", "이동", "드래그", "끌", "클릭", "삭제", "비우", "추가", "사용법")):
        return "**카드 활동:** 카드를 칸으로 끌어 놓거나, 카드를 클릭한 뒤 칸의 ‘여기에 놓기’를 누르세요. 새 카드가 들어가면 기존 카드는 보관함으로 돌아가요.\n\n**자유 조립:** S·V·O·C 버튼으로 블록을 추가하고, ↑·↓로 순서를 바꾸고, ✕로 삭제하세요. 입력 후 Enter를 누르면 결과가 갱신돼요."
    numbers = list(dict.fromkeys(re.findall(r"([1-5])\s*형식", q)))
    if len(numbers) > 1:
        comparisons = []
        for value in numbers:
            n = int(value)
            roles = next(roles for roles, info in PATTERNS.items() if info[0] == n)
            example = " ".join(word for _, word in EXAMPLES[n])
            comparisons.append(f"**{n}형식: {' + '.join(roles)}** — {example}. {PATTERNS[roles][2]}")
        return "\n\n".join(comparisons)
    number = re.search(r"([1-5])\s*형식", q)
    if number:
        n = int(number.group(1))
        roles = next(roles for roles, info in PATTERNS.items() if info[0] == n)
        example = " ".join(word for _, word in EXAMPLES[n])
        return f"**{n}형식 = {' + '.join(roles)}**\n\n{PATTERNS[roles][2]}\n\n예: **{example}.**\n\n" + " / ".join(f"{role}: {word}" for role, word in EXAMPLES[n])
    for role, keyword, explanation in (
        ("S", "주어", "‘누가?’에 답하는 말이에요. Birds sing.에서 노래하는 **Birds**가 S예요."),
        ("V", "동사", "무엇을 하는지, 어떤 상태인지를 나타내요. Birds sing.에서 **sing**이 V예요. She is happy.에서는 **is**가 V예요."),
        ("O", "목적어", "동작의 대상이에요. Students read books.에서 ‘무엇을 읽나요?’의 답인 **books**가 O예요."),
        ("C", "보어", "주어나 목적어가 누구인지, 어떤 상태인지 설명해요. She is happy.의 **happy**는 주어를, We made him happy.의 **happy**는 목적어를 설명해요."),
    ):
        if keyword in q or re.search(rf"(?<![a-z]){role.lower()}(?![a-z])", q):
            return explanation
    vocabulary = {
        "birds": "Birds는 ‘새들’이라는 뜻이에요. Birds sing.에서는 노래하는 대상이므로 주어(S)예요.",
        "sing": "sing은 ‘노래하다’라는 동사(V)예요. Birds sing.은 S + V, 1형식이에요.",
        "books": "books는 ‘책들’이에요. Students read books.에서는 읽는 대상이므로 목적어(O)예요.",
        "happy": "happy는 ‘행복한’이라는 형용사예요. She is happy.에서는 주어를 설명하는 C, We made him happy.에서는 목적어를 설명하는 C예요.",
    }
    for word, explanation in vocabulary.items():
        if re.search(rf"(?<![a-z]){word}(?![a-z])", q):
            return explanation
    if any(word in compact for word in ("모르", "어려", "막혔", "힌트", "도와", "왜", "틀렸", "맞아", "맞나요", "빈칸", "부족", "예시", "예제", "형식", "문장")):
        if activity_key == "cards":
            activity = st.session_state.get("card_activity", "새들의 노래 · 1형식")
            card_words, roles = activities[activity]
            placements = st.session_state.get("placements", {})
            empty = [f"{i+1}번 {role}" for i, role in enumerate(roles) if i not in placements.values()]
            guidance = "아직 비어 있는 칸: " + ", ".join(empty) if empty else "칸이 모두 찼네요. 단어의 역할도 맞는지 살펴보세요."
            n = PATTERNS[tuple(roles)][0]
            return f"현재 활동은 **{activity}**예요. {guidance}\n\n먼저 ‘누가?’에 답하는 S를 찾고, 동작이나 상태를 나타내는 V를 찾아보세요.\n\n비교 예시: **{' '.join(word for _, word in EXAMPLES[n])}.**\n\n어떤 단어가 헷갈리는지도 구체적으로 물어봐 주세요."
        blocks = st.session_state.get("blocks", [])
        roles = [block["role"] for block in blocks]
        words = [st.session_state.get(f"word_{block['id']}", "") for block in blocks]
        feedback, example = sentence_feedback(roles, words)
        return f"{feedback}\n\n참고 예시: **{example}**\n\n주어 → 동사 순서로 시작해 보세요. 어느 성분이 어려운지도 알려 주세요."
    return "지금 질문은 이 활동에 관한 질문인지 알아보기 어려워요. 학습과 관련 없는 질문이라면 이곳에 적절하지 않아요. 괜찮아요! ‘보어가 뭐예요?’, ‘2형식과 3형식은 어떻게 달라요?’처럼 어려운 점을 구체적으로 다시 질문해 주세요. 🐣"


def activity_heading(title, key, sidebar=False):
    """활동별로 독립적인 질문 상자를 열고 답변을 보관합니다."""
    heading, button = st.columns([3, 2] if sidebar else [5, 1])
    heading.subheader(title)
    if button.button("🐣 도와줘", key=f"help_toggle_{key}", use_container_width=True):
        st.session_state[f"help_open_{key}"] = not st.session_state.get(f"help_open_{key}", False)
    if st.session_state.get(f"help_open_{key}", False):
        with st.container(border=True):
            st.markdown("**🐣 삐약 선생님에게 물어봐!**")
            st.caption("문장 성분·1~5형식·활동 방법을 설명하는 규칙 기반 도움말이에요. 예: ‘목적어와 보어의 차이는?’")
            with st.form(f"help_form_{key}"):
                question = st.text_input("어떤 점이 어렵나요?", placeholder="예: Students read는 틀린 문장인가요?", max_chars=500, key=f"help_question_{key}")
                submitted = st.form_submit_button("질문하기 🌱")
            if submitted:
                st.session_state[f"help_answer_{key}"] = answer_question(question, key)
            if f"help_answer_{key}" in st.session_state:
                st.markdown(st.session_state[f"help_answer_{key}"])


# 설치된 Streamlit의 기본 컴포넌트 기능으로 단어 카드를 만듭니다.
word_board = st.components.v2.component(
    "sentence_word_board",
    html='<div id="board"></div>',
    css="""
    #board {font-family:'Gowun Dodum','Malgun Gothic',sans-serif;color:#24334b;}
    .zones {display:flex;flex-wrap:wrap;gap:12px;margin:12px 0}
    .zone {border:2px dashed #9aadd2;border-radius:20px;background:#f4f7ff;padding:14px;min-width:110px;min-height:80px;flex:1}
    .zone.over {border-color:#2563eb;background:#dbeafe;color:#172033}
    .token {display:inline-block;margin:6px;padding:10px 16px;border:1px solid #8594a8;border-radius:16px;cursor:grab;background:#fff0cc;color:#172033;font:inherit}
    .token:focus-visible,.target:focus-visible {outline:3px solid #596fc1;outline-offset:3px;}
    .token.selected {outline:3px solid #2563eb}
    .target {display:block;background:transparent;color:inherit;border:0;cursor:pointer;font:inherit;font-weight:bold;width:100%;text-align:left}
    """,
    js=r"""
    export default function({data, parentElement, setTriggerValue}) {
      const root = parentElement.querySelector('#board');
      root.replaceChildren();
      let selected = null;
      const move = (target, token) => {
        if (Number.isInteger(token) && token >= 0 && token < data.words.length)
          setTriggerValue('moved', {token, target});
      };
      const zones = document.createElement('div'); zones.className = 'zones';
      root.append(zones);
      const labels = ['단어 보관함', ...data.roles.map((r, i) => `${i+1}. ${r}`)];
      labels.forEach((label, zoneIndex) => {
        const target = zoneIndex - 1;
        const zone = document.createElement('section'); zone.className = 'zone';
        const heading = document.createElement('button'); heading.className = 'target';
        heading.textContent = label + ' · 여기에 놓기';
        heading.onclick = () => { if (selected !== null) move(target, selected); };
        zone.append(heading);
        zone.ondragover = e => { e.preventDefault(); zone.classList.add('over'); };
        zone.ondragleave = () => zone.classList.remove('over');
        zone.ondrop = e => { e.preventDefault(); zone.classList.remove('over');
          const value = e.dataTransfer.getData('text/plain');
          if (/^\d+$/.test(value)) move(target, Number(value));
        };
        data.words.forEach((word, token) => {
          if ((data.placements[String(token)] ?? -1) !== target) return;
          const card = document.createElement('button'); card.className = 'token';
          card.textContent = word; card.draggable = true;
          card.ondragstart = e => e.dataTransfer.setData('text/plain', String(token));
          card.onclick = () => { selected = token;
            root.querySelectorAll('.token').forEach(el => el.classList.remove('selected'));
            card.classList.add('selected');
          };
          zone.append(card);
        });
        zones.append(zone);
      });
    }
    """,
)

if "blocks" not in st.session_state:
    st.session_state.blocks = []
    st.session_state.next_id = 0


def add_block(role, word=""):
    block_id = st.session_state.next_id
    st.session_state.next_id += 1
    st.session_state.blocks.append({"id": block_id, "role": role})
    st.session_state[f"word_{block_id}"] = word


def clear_blocks():
    for block in st.session_state.blocks:
        st.session_state.pop(f"word_{block['id']}", None)
    st.session_state.blocks = []


def load_example(number):
    clear_blocks()
    for role, word in EXAMPLES[number]:
        add_block(role, word)


def move_block(index, direction):
    blocks = st.session_state.blocks
    other = index + direction
    if 0 <= other < len(blocks):
        blocks[index], blocks[other] = blocks[other], blocks[index]


def remove_block(index):
    block = st.session_state.blocks.pop(index)
    st.session_state.pop(f"word_{block['id']}", None)


st.title("5형식 문장 정복")
st.markdown('<div class="mascot"><span style="font-size:2rem" aria-hidden="true">🐣 🌱 🧩</span><br><b>삐약 선생님과 한 문장씩, 차근차근!</b><br>틀려도 괜찮아요. 헷갈리는 순간에는 활동 옆 ‘도와줘’를 눌러 보세요.</div>', unsafe_allow_html=True)
st.write("성분 블록을 고르고, 단어를 넣고, 순서를 바꾸며 영어 문장의 뼈대를 살펴보세요.")
st.caption("① 블록 추가 → ② 단어 또는 구 입력 → ③ ↑ ↓로 순서 변경 → ④ 형식 확인")

with st.sidebar:
    activity_heading("📖 형식별 예제", "examples", sidebar=True)
    st.caption("예제를 누르면 현재 조립 내용이 예제로 바뀝니다.")
    for number, roles in enumerate(PATTERNS, start=1):
        st.button(f"{number}형식 · {' + '.join(roles)}", key=f"example_{number}", on_click=load_example, args=(number,), use_container_width=True)
    st.divider()
    st.markdown("**성분 도움말**")
    for role, meaning in ROLES.items():
        st.write(f"**{role}** — {meaning}")
    st.info("4형식에는 O 블록이 두 개 필요해요. 한 블록에는 ‘a book’처럼 여러 단어를 넣어도 됩니다.")

activity_heading("🎯 단어 카드 끌어 놓기", "cards")
st.caption("카드를 성분 칸으로 끌어 놓으세요. 클릭으로도 가능해요: 카드 선택 → ‘여기에 놓기’. 보관함으로 돌려놓을 수도 있어요.")

activity = st.selectbox("카드 활동 선택", list(activities))
if st.session_state.get("card_activity") != activity:
    st.session_state.card_activity = activity
    st.session_state.placements = {}
    st.session_state.board_version = st.session_state.get("board_version", 0) + 1
if st.button("카드 활동 다시 시작"):
    st.session_state.placements = {}
    st.session_state.board_version += 1
card_words, card_roles = activities[activity]
result = word_board(
    data={"words": card_words, "roles": card_roles, "placements": st.session_state.placements},
    key=f"word_board_{st.session_state.board_version}",
    on_moved_change=lambda: None,
)
if result.moved:
    token, target = result.moved.get("token"), result.moved.get("target")
    if isinstance(token, int) and isinstance(target, int) and 0 <= token < len(card_words) and -1 <= target < len(card_roles):
        placements = st.session_state.placements
        # 한 칸에는 카드 하나. 기존 카드는 보관함으로 돌려놓습니다.
        for old_token in list(placements):
            if placements[old_token] == target and target != -1:
                placements.pop(old_token)
        placements[str(token)] = target
        st.rerun()
placed_words = [next((card_words[int(t)] for t, place in st.session_state.placements.items() if place == i), "") for i in range(len(card_roles))]
if any(placed_words):
    st.write("**카드 문장:** " + " / ".join(word or "___" for word in placed_words))
    expected = {
        "새들의 노래 · 1형식": ["Birds", "sing"],
        "읽는 대상 더하기 · 3형식": ["Students", "read", "books"],
        "기분 설명하기 · 2형식": ["She", "is", "happy"],
        "책 선물하기 · 4형식": ["He", "gave", "me", "a book"],
        "행복하게 만들기 · 5형식": ["We", "made", "him", "happy"],
    }[activity]
    if all(placed_words) and placed_words == expected:
        st.success("잘 조립했어요! " + " ".join(placed_words) + ".")
    elif all(placed_words):
        st.warning("단어의 역할을 다시 살펴보세요. 누가(S), 무엇을 하거나 어떤 상태인지(V)부터 찾아보세요.")
    else:
        st.info("아직 비어 있는 성분 칸이 있어요. 남은 카드를 놓아 보세요.")
    with st.expander("힌트와 완성 예시"):
        st.write(" → ".join(f"{role}: {word}" for role, word in zip(card_roles, expected)))
        st.write(" ".join(expected) + ".")
st.divider()

activity_heading("1. 성분 블록 고르기", "roles")
columns = st.columns(4)
for column, (role, meaning) in zip(columns, ROLES.items()):
    column.button(f"＋ {role} · {meaning.split(' · ')[0]}", key=f"add_{role}", on_click=add_block, args=(role,), use_container_width=True)

activity_heading("2. 문장 조립하기", "assembly")
st.caption("입력 후 Enter를 누르거나 입력 칸 밖을 클릭하면 결과가 바로 갱신됩니다.")
if not st.session_state.blocks:
    st.info("위에서 S와 V 블록을 추가해 보세요. 왼쪽 예제로 시작해도 좋아요.")

for index, block in enumerate(st.session_state.blocks):
    role, block_id = block["role"], block["id"]
    with st.container(border=True):
        label, field, up, down, delete = st.columns([2, 5, 1, 1, 1], vertical_alignment="center")
        label.markdown(f"**{index + 1}. {role} · {ROLES[role].split(' · ')[0]}**")
        field.text_input(f"{index + 1}번 {role} 블록의 단어 또는 구", key=f"word_{block_id}", placeholder="단어 또는 구를 입력하세요", label_visibility="collapsed")
        up.button("↑", key=f"up_{block_id}", help="앞으로 이동", disabled=index == 0, on_click=move_block, args=(index, -1))
        down.button("↓", key=f"down_{block_id}", help="뒤로 이동", disabled=index == len(st.session_state.blocks) - 1, on_click=move_block, args=(index, 1))
        delete.button("✕", key=f"delete_{block_id}", help="블록 삭제", on_click=remove_block, args=(index,))

st.button("전체 비우기", on_click=clear_blocks, disabled=not st.session_state.blocks)
activity_heading("3. 조립 결과", "results")
blocks = st.session_state.blocks
if blocks:
    cards = []
    for block in blocks:
        role = block["role"]
        word = st.session_state.get(f"word_{block['id']}", "").strip()
        cards.append(f'<div style="background:{COLORS[role]};color:#172033;padding:14px 22px;border-radius:12px;text-align:center"><b>{role}</b><br>{html.escape(word or "(빈칸)")}</div>')
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px">' + ''.join(cards) + '</div>', unsafe_allow_html=True)
    signature = tuple(block["role"] for block in blocks)
    st.write("**성분 순서:** " + " → ".join(signature))
    words = [st.session_state.get(f"word_{block['id']}", "").strip() for block in blocks]
    pattern = PATTERNS.get(signature)
    if pattern:
        number, structure, explanation = pattern
        st.success(f"블록 구조 판별: {number}형식 · {structure}")
        st.write(explanation)
        if all(words):
            st.write("**조립한 문장:** " + " ".join(words))
        else:
            st.warning("구조가 완성됐어요! 빈 블록에 단어를 입력해 문장도 완성해 보세요.")
    else:
        st.warning("아직 1~5형식의 기본 구조와 일치하지 않아요.")
        if signature[0] != "S":
            st.write("주어(S)를 맨 앞으로 옮겨 보세요.")
        elif len(signature) < 2 or signature[1] != "V":
            st.write("주어(S) 다음에 동사(V)를 놓아 보세요.")
        else:
            st.write("S + V 다음에 아무것도 놓지 않거나, C / O / O + O / O + C를 놓아 보세요.")
    st.markdown("**💡 더 나은 문장 만들기**")
    feedback, better_example = sentence_feedback(signature, words)
    st.info(feedback)
    st.write("**참고 예시:** " + better_example)
else:
    st.caption("블록을 추가하면 이곳에 구조와 판별 결과가 표시됩니다.")

st.divider()
st.caption("학습용 초안: 선택한 성분의 순서로 기본 형식을 판별합니다. 일부 동사에는 학습 규칙에 따른 보완 제안을 제공합니다. 모든 영어 문장의 품사·시제·문법을 검사하는 기능은 아닙니다.")
