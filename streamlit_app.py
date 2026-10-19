import html

import streamlit as st

st.set_page_config(page_title="5형식 문장 구조 조립소", page_icon="🧩", layout="wide")

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


st.title("🧩 5형식 문장 구조 조립소")
st.write("성분 블록을 고르고, 단어를 넣고, 순서를 바꾸며 영어 문장의 뼈대를 살펴보세요.")
st.caption("① 블록 추가 → ② 단어 또는 구 입력 → ③ ↑ ↓로 순서 변경 → ④ 형식 확인")

with st.sidebar:
    st.header("📖 형식별 예제")
    st.caption("예제를 누르면 현재 조립 내용이 예제로 바뀝니다.")
    for number, roles in enumerate(PATTERNS, start=1):
        st.button(f"{number}형식 · {' + '.join(roles)}", key=f"example_{number}", on_click=load_example, args=(number,), use_container_width=True)
    st.divider()
    st.markdown("**성분 도움말**")
    for role, meaning in ROLES.items():
        st.write(f"**{role}** — {meaning}")
    st.info("4형식에는 O 블록이 두 개 필요해요. 한 블록에는 ‘a book’처럼 여러 단어를 넣어도 됩니다.")

st.subheader("1. 성분 블록 고르기")
columns = st.columns(4)
for column, (role, meaning) in zip(columns, ROLES.items()):
    column.button(f"＋ {role} · {meaning.split(' · ')[0]}", key=f"add_{role}", on_click=add_block, args=(role,), use_container_width=True)

st.subheader("2. 문장 조립하기")
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
st.subheader("3. 조립 결과")
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
else:
    st.caption("블록을 추가하면 이곳에 구조와 판별 결과가 표시됩니다.")

st.divider()
st.caption("학습용 초안: 선택한 성분의 순서로 기본 형식을 판별합니다. 입력한 단어의 실제 품사, 동사 용법, 문법적 정확성은 자동 검사하지 않습니다.")
