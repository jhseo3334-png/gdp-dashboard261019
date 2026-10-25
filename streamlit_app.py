import html
import re
import unicodedata

import pandas as pd
import streamlit as st

st.set_page_config(page_title="5형식 문장 어렵지 않아요", page_icon="🧩", layout="wide")

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

# (대표 뜻과 품사, 짧은 예문, 예문 해석). 수업에 필요한 단어를 여기에 추가할 수 있습니다.
WORD_DICTIONARY = {
    "apple": ("사과 · 명사", "I eat an apple.", "나는 사과 하나를 먹어요."),
    "banana": ("바나나 · 명사", "I like bananas.", "나는 바나나를 좋아해요."),
    "bird": ("새 · 명사", "Birds sing.", "새들이 노래해요."),
    "book": ("책 · 명사 / 예약하다 · 동사", "I read a book.", "나는 책 한 권을 읽어요."),
    "student": ("학생 · 명사", "Students read books.", "학생들이 책을 읽어요."),
    "teacher": ("선생님 · 명사", "She is a teacher.", "그녀는 선생님이에요."),
    "school": ("학교 · 명사", "I go to school.", "나는 학교에 가요."),
    "friend": ("친구 · 명사", "He is my friend.", "그는 내 친구예요."),
    "cat": ("고양이 · 명사", "The cat sleeps.", "고양이가 자요."),
    "dog": ("개 · 명사", "The dog runs.", "개가 달려요."),
    "music": ("음악 · 명사", "I like music.", "나는 음악을 좋아해요."),
    "water": ("물 · 명사 / 물을 주다 · 동사", "I drink water.", "나는 물을 마셔요."),
    "food": ("음식 · 명사", "We need food.", "우리는 음식이 필요해요."),
    "milk": ("우유 · 명사", "She drinks milk.", "그녀는 우유를 마셔요."),
    "ball": ("공 · 명사", "I have a ball.", "나는 공 하나를 가지고 있어요."),
    "flower": ("꽃 · 명사", "The flower is pretty.", "그 꽃은 예뻐요."),
    "house": ("집 · 명사", "This is my house.", "이곳은 내 집이에요."),
    "home": ("집 · 명사 / 집으로 · 부사", "I go home.", "나는 집으로 가요."),
    "mother": ("어머니 · 명사", "My mother sings.", "우리 어머니는 노래해요."),
    "father": ("아버지 · 명사", "My father cooks.", "우리 아버지는 요리해요."),
    "sister": ("여자 형제(언니·누나·여동생) · 명사", "My sister reads.", "내 여자 형제는 독서해요."),
    "brother": ("남자 형제(형·오빠·남동생) · 명사", "My brother runs.", "내 남자 형제는 달려요."),
    "name": ("이름 · 명사 / 이름을 짓다 · 동사", "My name is Mina.", "내 이름은 미나예요."),
    "weather": ("날씨 · 명사", "The weather is nice.", "날씨가 좋아요."),
    "lunch": ("점심 · 명사", "We eat lunch.", "우리는 점심을 먹어요."),
    "read": ("읽다 · 동사", "Students read books.", "학생들이 책을 읽어요."),
    "sing": ("노래하다 · 동사", "Birds sing.", "새들이 노래해요."),
    "like": ("좋아하다 · 동사 / ~처럼 · 전치사", "I like music.", "나는 음악을 좋아해요."),
    "love": ("사랑하다 · 동사 / 사랑 · 명사", "I love my family.", "나는 내 가족을 사랑해요."),
    "give": ("주다 · 동사", "He gave me a book.", "그는 나에게 책 한 권을 주었어요."),
    "make": ("만들다, ~하게 하다 · 동사", "We made him happy.", "우리는 그를 행복하게 했어요."),
    "eat": ("먹다 · 동사", "I eat an apple.", "나는 사과 하나를 먹어요."),
    "drink": ("마시다 · 동사 / 음료 · 명사", "I drink water.", "나는 물을 마셔요."),
    "run": ("달리다 · 동사", "Dogs run.", "개들이 달려요."),
    "walk": ("걷다 · 동사", "We walk together.", "우리는 함께 걸어요."),
    "sleep": ("자다 · 동사 / 잠 · 명사", "The baby sleeps.", "아기가 자요."),
    "play": ("놀다, 경기하다, 연주하다 · 동사", "I play the piano.", "나는 피아노를 연주해요."),
    "study": ("공부하다 · 동사 / 공부 · 명사", "I study English.", "나는 영어를 공부해요."),
    "learn": ("배우다 · 동사", "We learn English.", "우리는 영어를 배워요."),
    "teach": ("가르치다 · 동사", "They teach English.", "그들은 영어를 가르쳐요."),
    "write": ("쓰다 · 동사", "I write a letter.", "나는 편지를 써요."),
    "speak": ("말하다 · 동사", "I speak English.", "나는 영어를 말해요."),
    "listen": ("듣다, 귀 기울이다 · 동사", "I listen to music.", "나는 음악을 들어요."),
    "see": ("보다 · 동사", "I see a bird.", "나는 새 한 마리를 봐요."),
    "watch": ("지켜보다 · 동사 / 손목시계 · 명사", "We watch TV.", "우리는 텔레비전을 봐요."),
    "go": ("가다 · 동사", "I go to school.", "나는 학교에 가요."),
    "come": ("오다 · 동사", "They come here.", "그들이 여기로 와요."),
    "have": ("가지다, 먹다 · 동사", "I have a book.", "나는 책 한 권을 가지고 있어요."),
    "want": ("원하다 · 동사", "I want a book.", "나는 책 한 권을 원해요."),
    "need": ("필요로 하다 · 동사", "We need water.", "우리는 물이 필요해요."),
    "enjoy": ("즐기다 · 동사", "I enjoy music.", "나는 음악을 즐겨요."),
    "help": ("돕다 · 동사 / 도움 · 명사", "I help my friend.", "나는 친구를 도와요."),
    "open": ("열다 · 동사 / 열린 · 형용사", "I open the door.", "나는 문을 열어요."),
    "close": ("닫다 · 동사 / 가까운 · 형용사", "I close the door.", "나는 문을 닫아요."),
    "be": ("~이다, ~한 상태이다, 있다 · 동사", "She is happy.", "그녀는 행복해요."),
    "become": ("~이 되다 · 동사", "He became a teacher.", "그는 선생님이 되었어요."),
    "seem": ("~인 것처럼 보이다 · 동사", "She seems happy.", "그녀는 행복해 보여요."),
    "happy": ("행복한 · 형용사", "She is happy.", "그녀는 행복해요."),
    "sad": ("슬픈 · 형용사", "He is sad.", "그는 슬퍼요."),
    "good": ("좋은 · 형용사", "This book is good.", "이 책은 좋아요."),
    "bad": ("나쁜 · 형용사", "The weather is bad.", "날씨가 나빠요."),
    "big": ("큰 · 형용사", "The dog is big.", "그 개는 커요."),
    "small": ("작은 · 형용사", "The cat is small.", "그 고양이는 작아요."),
    "cute": ("귀여운 · 형용사", "The cat is cute.", "그 고양이는 귀여워요."),
    "pretty": ("예쁜 · 형용사", "The flower is pretty.", "그 꽃은 예뻐요."),
    "hungry": ("배고픈 · 형용사", "I am hungry.", "나는 배고파요."),
    "tired": ("피곤한 · 형용사", "He is tired.", "그는 피곤해요."),
    "kind": ("친절한 · 형용사 / 종류 · 명사", "She is kind.", "그녀는 친절해요."),
    "i": ("나(는/가) · 대명사", "I read books.", "나는 책을 읽어요."),
    "you": ("너, 당신, 너희 · 대명사", "You are kind.", "너는 친절해요."),
    "he": ("그(는/가) · 대명사", "He sings.", "그는 노래해요."),
    "she": ("그녀(는/가) · 대명사", "She reads.", "그녀는 독서해요."),
    "it": ("그것 · 대명사", "It is small.", "그것은 작아요."),
    "we": ("우리(는/가) · 대명사", "We study English.", "우리는 영어를 공부해요."),
    "they": ("그들, 그것들 · 대명사", "They sing.", "그들은 노래해요."),
    "me": ("나를, 나에게 · 대명사", "He gave me a book.", "그는 나에게 책을 주었어요."),
    "him": ("그를, 그에게 · 대명사", "We made him happy.", "우리는 그를 행복하게 했어요."),
    "her": ("그녀를, 그녀에게 · 대명사 / 그녀의 · 소유 한정사", "I like her.", "나는 그녀를 좋아해요."),
    "us": ("우리를, 우리에게 · 대명사", "She helps us.", "그녀는 우리를 도와요."),
    "them": ("그들을, 그들에게 · 대명사", "I help them.", "나는 그들을 도와요."),
    "my": ("나의 · 소유 한정사", "This is my book.", "이것은 내 책이에요."),
    "a": ("하나의, 어떤 · 부정관사", "I have a book.", "나는 책 한 권을 가지고 있어요."),
    "an": ("하나의, 어떤 · 모음 소리 앞의 부정관사", "I eat an apple.", "나는 사과 하나를 먹어요."),
    "the": ("그, 특정한 대상을 가리키는 정관사", "The bird sings.", "그 새가 노래해요."),
    "english": ("영어 · 명사 / 영어의 · 형용사", "I study English.", "나는 영어를 공부해요."),
}
# 불규칙 변화와 자주 쓰는 복수형을 명시해서 잘못된 어근 추측을 피합니다.
WORD_FORMS = {
    "birds": ("bird", "bird의 복수형: 새들"), "books": ("book", "book의 복수형: 책들"),
    "students": ("student", "student의 복수형: 학생들"), "apples": ("apple", "apple의 복수형: 사과들"),
    "bananas": ("banana", "banana의 복수형: 바나나들"), "cats": ("cat", "cat의 복수형: 고양이들"),
    "dogs": ("dog", "dog의 복수형: 개들"), "friends": ("friend", "friend의 복수형: 친구들"),
    "sings": ("sing", "sing의 현재형(주어가 3인칭 단수일 때)"),
    "reads": ("read", "read의 현재형(주어가 3인칭 단수일 때)"),
    "likes": ("like", "like의 현재형(주어가 3인칭 단수일 때)"),
    "gave": ("give", "give의 과거형: 주었다"), "made": ("make", "make의 과거형·과거분사형"),
    "went": ("go", "go의 과거형: 갔다"), "ate": ("eat", "eat의 과거형: 먹었다"),
    "ran": ("run", "run의 과거형: 달렸다"), "wrote": ("write", "write의 과거형: 썼다"),
    "is": ("be", "be동사의 현재형: he, she, it 등과 사용"),
    "am": ("be", "be동사의 현재형: I와 사용"),
    "are": ("be", "be동사의 현재형: you, we, they 등과 사용"),
    "was": ("be", "be동사의 과거형: I, he, she, it 등과 사용"),
    "were": ("be", "be동사의 과거형: you, we, they 등과 사용"),
}


def dictionary_answer(question):
    """단어 뜻 질문만 처리하고 문장 구조 질문은 기존 도움말로 넘깁니다."""
    tokens = re.findall(r"[a-z]+(?:'[a-z]+)?", question)
    bare = bool(re.fullmatch(r"[a-z]+[?!.,\s]*", question))
    meaning_intent = any(marker in question for marker in ("뜻", "의미", "무슨 말", "무슨말", "뭐야", "뭐예요", "뭔가요", "meaning", "mean", "define"))
    if not bare and not meaning_intent:
        return None
    # 성분/형식 자체에 대한 질문은 문법 도움말에서 설명합니다.
    if any(term in question for term in ("주어", "동사", "목적어", "보어", "형식")):
        if not tokens or all(token in {"s", "v", "o", "c"} for token in tokens):
            return None
    if bare and tokens[0] in {"s", "v", "o", "c"}:
        return None
    if not bare:
        stop_words = {"what", "does", "do", "mean", "means", "meaning", "of", "define", "please", "tell", "the", "word", "is", "in", "korean"}
        # 따옴표 안의 단어는 영어 질문의 기능어와 같아도 찾아줍니다.
        quoted = re.findall(r"['\"‘“]([a-z]+)['\"’”]", question)
        if quoted:
            tokens = quoted
        elif re.search(r"[가-힣]", question):
            tokens = [token for token in tokens if token not in {"meaning", "mean", "define"}]
        else:
            tokens = [token for token in tokens if token not in stop_words]
    if not tokens:
        return "어떤 영어 단어의 뜻이 궁금한가요? **apple 뜻**, **read는 무슨 뜻이야?**처럼 영어 단어를 함께 적어 주세요. 📖"
    if len(tokens) != 1:
        return "기초 사전에서는 한 번에 영어 단어 하나씩 찾아볼 수 있어요. **books 뜻**처럼 다시 질문해 주세요. 문장 전체 번역은 제공하지 않아요. 📖"
    word = tokens[0]
    base, form_note = WORD_FORMS.get(word, (word, ""))
    entry = WORD_DICTIONARY.get(base)
    if entry is None:
        from difflib import get_close_matches
        matches = get_close_matches(word, list(WORD_DICTIONARY) + list(WORD_FORMS), n=3, cutoff=0.75)
        suggestion = " 혹시 **" + ", ".join(matches) + "** 중 하나인가요?" if matches else " **apple**, **read**, **happy** 같은 기초 단어를 질문해 보세요."
        return "아직 기초 사전에 등록되지 않은 단어예요. 철자를 확인해 주세요." + suggestion
    meaning, example, translation = entry
    note = f"\n\n단어 형태: {form_note}" if form_note else ""
    return f"📖 **{word}** — {meaning}{note}\n\n**예문:** {example}\n\n**해석:** {translation}\n\n단어는 문장에 따라 뜻과 역할이 달라질 수 있어요. 위 내용은 대표 뜻과 예문이에요."


def answer_question(question, activity_key):
    """외부 AI 없이 학습 주제별 규칙과 현재 조립 상태로 답합니다."""
    q = unicodedata.normalize("NFKC", question).strip().lower()
    compact = re.sub(r"\s+", "", q)
    if not q:
        return "궁금한 점을 한 문장으로 적어 주세요. 예: ‘목적어와 보어는 어떻게 달라요?’ 🐣"
    if len(q) > 500:
        return "질문이 조금 길어요. 가장 어려운 부분 하나를 500자 이내로 다시 질문해 주세요. 🐣"
    dictionary_reply = dictionary_answer(q)
    if dictionary_reply is not None:
        return dictionary_reply
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
    if any(word in compact for word in ("모르", "어려", "막혔", "힌트", "도와", "왜", "틀렸", "맞아", "맞나요", "빈칸", "부족", "예시", "예제", "형식", "문장")):
        if activity_key == "practice":
            level = st.session_state.get("practice_level", 1)
            number = st.session_state.get(f"practice_number_{level}", 1)
            prompt, instruction, choices, correct, explanation = PRACTICE[level]["questions"][number - 1]
            return f"현재는 LEVEL {level}의 {number}번 문제예요. **{prompt}**\n\n{instruction}\n\n먼저 누가(S), 무엇을 하거나 어떤 상태인지(V)를 찾아보세요. 빈칸 문제는 한국어 뜻을, 형식 문제는 O와 C의 역할을 확인해 보세요."
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
            st.caption("문장 성분·1~5형식·기초 단어 뜻을 물어보세요. 예: ‘apple 뜻’, ‘목적어와 보어의 차이는?’")
            with st.form(f"help_form_{key}"):
                question = st.text_input("어떤 점이 어렵나요?", placeholder="예: read는 무슨 뜻이야? / Students read는 틀렸나요?", max_chars=500, key=f"help_question_{key}")
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
if "student_info" not in st.session_state:
    st.session_state.student_info = {}
if "app_started" not in st.session_state:
    st.session_state.app_started = False


def render_student_info_form():
    st.title("🧩 영어 문법 학습 시작")
    st.markdown("<div class='mascot'><b>학생 정보를 입력하고 학습을 시작해 보세요.</b><br>입력한 정보는 학습 결과 페이지에서 함께 보여집니다.</div>", unsafe_allow_html=True)

    with st.form("student_info_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("학생 이름", placeholder="예: 김민지")
            grade = st.selectbox("학년", ["1학년", "2학년", "3학년", "중학교 1학년", "중학교 2학년", "중학교 3학년"], index=0)
        with col2:
            class_name = st.text_input("반", placeholder="예: 1반")
            learning_goal = st.selectbox("학습 목표", ["기초 문법 익히기", "문장 구조 이해하기", "5형식 완벽 정복", "다시 복습하기"], index=0)

        st.text_area("한 줄 소개", placeholder="예: 5형식을 더 잘 알고 싶어요.", height=100)
        submit = st.form_submit_button("학습 시작하기 🚀", use_container_width=True)

    if submit:
        if not name.strip():
            st.warning("학생 이름을 입력해 주세요.")
        else:
            st.session_state.student_info = {
                "name": name.strip(),
                "grade": grade,
                "class_name": class_name.strip(),
                "learning_goal": learning_goal,
            }
            st.session_state.app_started = True
            st.rerun()


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


# LEVEL은 형식 번호가 아니라 학습 난이도입니다. 각 레벨에 5문제가 있습니다.
PRACTICE = {
    1: {"title": "성분 찾기", "description": "누가, 무엇을 하는지부터 찾아봐요!", "questions": [
        ("Birds sing.", "Birds의 문장 성분은 무엇일까요?", ["S · 주어", "V · 동사", "O · 목적어", "C · 보어"], "S · 주어", "노래하는 주체인 Birds가 주어(S)예요."),
        ("Students read books.", "read의 문장 성분은 무엇일까요?", ["S · 주어", "V · 동사", "O · 목적어", "C · 보어"], "V · 동사", "read는 ‘읽다’라는 동작을 나타내는 동사(V)예요."),
        ("I like music.", "music의 문장 성분은 무엇일까요?", ["S · 주어", "V · 동사", "O · 목적어", "C · 보어"], "O · 목적어", "무엇을 좋아하는지 알려 주는 music이 목적어(O)예요."),
        ("She is happy.", "happy의 문장 성분은 무엇일까요?", ["S · 주어", "V · 동사", "O · 목적어", "C · 보어"], "C · 보어", "happy는 주어 She의 상태를 설명하는 보어(C)예요."),
        ("We made him happy.", "him의 문장 성분은 무엇일까요?", ["S · 주어", "V · 동사", "O · 목적어", "C · 보어"], "O · 목적어", "행복하게 만든 대상인 him이 목적어(O)이고, happy는 그 상태를 설명해요."),
    ]},
    2: {"title": "빈칸 채우기", "description": "뜻과 성분에 맞는 단어를 골라요!", "questions": [
        ("___ sing. (새들이 노래해요.)", "주어 자리에 알맞은 단어는?", ["Birds", "Happy", "Read", "Gave"], "Birds", "Birds는 ‘새들’이라는 명사로, 노래하는 주어가 돼요."),
        ("She ___ happy. (그녀는 행복해요.)", "현재의 상태를 나타내는 동사는?", ["are", "is", "am", "like"], "is", "주어 She에는 be동사 is를 써요. happy는 상태를 설명하는 보어예요."),
        ("Students read ___. (학생들이 책을 읽어요.)", "목적어 자리에 알맞은 단어는?", ["happy", "sing", "books", "are"], "books", "읽는 대상인 books가 목적어예요. S + V + O인 3형식이에요."),
        ("He gave ___ a book. (그는 나에게 책을 주었어요.)", "‘나에게’에 해당하는 말은?", ["I", "my", "me", "mine"], "me", "동사 뒤에서 ‘나에게’를 나타내는 목적격 me를 써요. me와 a book은 두 목적어예요."),
        ("We made him ___. (우리는 그를 행복하게 했어요.)", "목적어의 상태를 설명할 말은?", ["happily", "happy", "happiness", "happier than"], "happy", "형용사 happy가 him의 상태를 설명하는 목적격 보어예요."),
    ]},
    3: {"title": "문장 형식 찾기", "description": "문장의 뼈대를 보고 1~5형식을 구별해요!", "questions": [
        ("Dogs run.", "이 문장은 몇 형식일까요?", ["1형식", "2형식", "3형식", "4형식", "5형식"], "1형식", "Dogs(S) + run(V). 주어와 동사만으로 뜻이 완성되는 1형식이에요."),
        ("He became a teacher.", "이 문장은 몇 형식일까요?", ["1형식", "2형식", "3형식", "4형식", "5형식"], "2형식", "He(S) + became(V) + a teacher(C). a teacher가 주어의 정체를 설명해요."),
        ("I enjoy music.", "이 문장은 몇 형식일까요?", ["1형식", "2형식", "3형식", "4형식", "5형식"], "3형식", "I(S) + enjoy(V) + music(O). music은 즐기는 대상이에요."),
        ("She gave him a flower.", "이 문장은 몇 형식일까요?", ["1형식", "2형식", "3형식", "4형식", "5형식"], "4형식", "She(S) + gave(V) + him(O) + a flower(O). 누구에게 무엇을 주는지 나타내요."),
        ("They made me happy.", "이 문장은 몇 형식일까요?", ["1형식", "2형식", "3형식", "4형식", "5형식"], "5형식", "They(S) + made(V) + me(O) + happy(C). happy는 me의 상태를 설명해요."),
    ]},
    4: {"title": "헷갈리는 구조 비교", "description": "목적어와 보어의 차이를 살펴봐요!", "questions": [
        ("He gave me a book.", "마지막 두 성분의 관계는?", ["O + O · 서로 다른 두 대상", "O + C · 목적어의 상태 설명"], "O + O · 서로 다른 두 대상", "me는 받는 사람, a book은 주는 물건이에요. 따라서 4형식이에요."),
        ("We made him happy.", "마지막 두 성분의 관계는?", ["O + O · 서로 다른 두 대상", "O + C · 목적어의 상태 설명"], "O + C · 목적어의 상태 설명", "happy는 him이 어떤 상태인지 설명해요. 따라서 5형식이에요."),
        ("She is a teacher. / She likes a teacher.", "두 문장의 a teacher는 각각 어떤 성분일까요?", ["둘 다 O", "둘 다 C", "첫 문장 C, 둘째 문장 O", "첫 문장 O, 둘째 문장 C"], "첫 문장 C, 둘째 문장 O", "is 뒤에서는 주어의 정체를 설명하고, likes 뒤에서는 좋아하는 대상을 나타내요."),
        ("Students read. / Students read books.", "두 문장에 대한 설명으로 알맞은 것은?", ["첫 문장은 무조건 틀리다", "둘 다 가능하며, 둘째 문장은 읽는 대상을 구체화한다", "둘 다 2형식이다"], "둘 다 가능하며, 둘째 문장은 읽는 대상을 구체화한다", "read는 목적어 없이도 쓸 수 있어요. books를 더하면 1형식에서 3형식으로 바뀌어요."),
        ("They named the baby Mina.", "Mina는 어떤 성분일까요?", ["간접 목적어", "직접 목적어", "목적격 보어"], "목적격 보어", "Mina는 the baby에게 붙인 이름으로 목적어의 정체를 설명해요. S + V + O + C예요."),
    ]},
    5: {"title": "직접 문장 완성", "description": "주어진 단어·구를 모두 한 번씩 써서 문장을 완성해요!", "questions": [
        ("sing / Birds", "‘새들이 노래해요.’를 영어로 쓰세요.", None, "Birds sing.", "Birds(S) + sing(V), 1형식이에요."),
        ("happy / is / She", "‘그녀는 행복해요.’를 영어로 쓰세요.", None, "She is happy.", "She(S) + is(V) + happy(C), 2형식이에요."),
        ("books / read / Students", "‘학생들이 책을 읽어요.’를 영어로 쓰세요.", None, "Students read books.", "Students(S) + read(V) + books(O), 3형식이에요."),
        ("a book / me / gave / He", "‘그는 나에게 책 한 권을 주었어요.’를 영어로 쓰세요.", None, "He gave me a book.", "He(S) + gave(V) + me(O) + a book(O), 4형식이에요."),
        ("him / happy / We / made", "‘우리는 그를 행복하게 했어요.’를 영어로 쓰세요.", None, "We made him happy.", "We(S) + made(V) + him(O) + happy(C), 5형식이에요."),
    ]},
}


def normalize_practice_answer(value):
    # 대소문자, 연속 공백, 문장 끝 마침표 등은 정오답에 영향을 주지 않습니다.
    value = unicodedata.normalize("NFKC", value).strip().casefold()
    return " ".join(value.rstrip(".!? ").split())


def get_problem_id(level, question_number):
    return f"{level}_{question_number}"


def get_question_detail(problem_id):
    level, question_number = map(int, problem_id.split("_"))
    prompt, instruction, choices, correct, explanation = PRACTICE[level]["questions"][question_number - 1]
    return level, question_number, prompt, instruction, choices, correct, explanation


def get_learning_summary():
    results = st.session_state.setdefault("practice_results", {})
    total_questions = sum(len(info["questions"]) for info in PRACTICE.values())
    total_correct = sum(1 for record in results.values() if record.get("correct") is True)
    attempted = len(results)
    incorrect = attempted - total_correct
    unanswered = total_questions - attempted
    overall_rate = (total_correct / attempted * 100) if attempted else 0.0

    stage_data = {}
    for level in PRACTICE:
        q_count = len(PRACTICE[level]["questions"])
        stage_correct = 0
        stage_attempted = 0
        for index in range(1, q_count + 1):
            problem_id = get_problem_id(level, index)
            record = results.get(problem_id)
            if record is not None:
                stage_attempted += 1
                if record.get("correct") is True:
                    stage_correct += 1
        stage_incorrect = stage_attempted - stage_correct
        stage_unanswered = q_count - stage_attempted
        stage_rate = (stage_correct / stage_attempted * 100) if stage_attempted else 0.0
        stage_data[level] = {
            "level": level,
            "title": PRACTICE[level]["title"],
            "total": q_count,
            "correct": stage_correct,
            "incorrect": stage_incorrect,
            "unanswered": stage_unanswered,
            "attempted": stage_attempted,
            "rate": round(stage_rate, 1),
        }

    highest_stage = max(stage_data.items(), key=lambda item: item[1]["rate"])[0] if stage_data else 1
    lowest_stage = min(stage_data.items(), key=lambda item: item[1]["rate"])[0] if stage_data else 1

    return {
        "total_questions": total_questions,
        "correct": total_correct,
        "incorrect": incorrect,
        "unanswered": unanswered,
        "attempted": attempted,
        "overall_rate": round(overall_rate, 1),
        "progress": round((attempted / total_questions) * 100, 1) if total_questions else 0.0,
        "stage_data": stage_data,
        "highest_stage": highest_stage,
        "lowest_stage": lowest_stage,
    }


def get_achievement_label(rate):
    if rate >= 90:
        return "매우 우수 – 문장 구조를 정확하게 이해하고 있어요!"
    if rate >= 70:
        return "우수 – 대부분의 문장 구조를 잘 이해하고 있어요."
    if rate >= 50:
        return "보통 – 일부 문장 형식에 대한 추가 연습이 필요해요."
    return "보충 학습 필요 – 기초 개념을 다시 확인하고 천천히 연습해 보세요."


def get_stage_guidance(level):
    guidance = {
        1: "1단계에서는 문장 속에서 주어와 동사를 먼저 찾는 연습이 중요해요. 누가 무엇을 하는지부터 확인해 보세요.",
        2: "2단계에서는 주어의 상태나 정체를 설명하는 보어를 다시 살펴보세요. be동사와 보어의 관계를 익히면 도움이 돼요.",
        3: "3단계에서는 동사 뒤에 오는 목적어를 찾는 연습이 필요해요. 어떤 대상을 말하는지 확인해 보세요.",
        4: "4단계에서는 간접목적어와 직접목적어의 차이를 확인해 보세요. 누구에게 무엇을 주는지 구분하면 쉬워져요.",
        5: "5단계에서는 목적어가 어떤 상태인지 설명하는 보어를 찾는 연습이 필요해요. 목적어와 보어의 연결을 다시 확인해 보세요.",
    }
    return guidance.get(level, "문장 구조를 다시 천천히 확인하면서 기본형을 익혀 보세요.")


def get_retry_summary():
    retry_results = st.session_state.setdefault("retry_results", {})
    retry_total = len(retry_results)
    retry_correct = sum(1 for record in retry_results.values() if record.get("retry_correct") is True)
    retry_rate = (retry_correct / retry_total * 100) if retry_total else 0.0
    return {
        "total": retry_total,
        "correct": retry_correct,
        "rate": round(retry_rate, 1),
    }


def reset_learning_state():
    st.session_state.practice_results = {}
    st.session_state.retry_results = {}
    st.session_state.reset_confirm = False


def render_practice():
    activity_heading("🌈 차근차근 연습하기", "practice")
    st.write("레벨과 문제 번호를 고르고 도전해 보세요. 틀려도 괜찮아요, 다시 하면 되니까요! 🐣")
    level_column, question_column = st.columns(2)
    level = level_column.selectbox("레벨 선택", list(PRACTICE), format_func=lambda n: f"LEVEL {n} · {PRACTICE[n]['title']}", key="practice_level")
    question_number = question_column.selectbox("문제 번호", range(1, len(PRACTICE[level]["questions"]) + 1), format_func=lambda n: f"{n}번 문제", key=f"practice_number_{level}")
    st.caption(PRACTICE[level]["description"])
    prompt, instruction, choices, correct, explanation = PRACTICE[level]["questions"][question_number - 1]
    problem_id = get_problem_id(level, question_number)
    results = st.session_state.setdefault("practice_results", {})
    summary = get_learning_summary()
    st.progress(summary["progress"] / 100, text=f"🌱 학습 진행률 {summary['attempted']} / {summary['total_questions']} 문항 완료 ({summary['progress']}%)")
    with st.container(border=True):
        st.markdown(f"### 🐾 LEVEL {level} · {question_number}번")
        st.markdown("**" + prompt + "**")
        st.write(instruction)
        with st.form(f"practice_form_{problem_id}"):
            if choices is None:
                answer = st.text_input("영어 문장 입력", placeholder="주어진 단어를 순서대로 써 보세요", key=f"practice_answer_{problem_id}", max_chars=200)
                st.caption("주어진 단어를 모두 사용하세요. 대소문자·여러 칸의 공백·끝의 마침표는 채점에 영향을 주지 않아요.")
            else:
                answer = st.radio("답을 골라 주세요", choices, index=None, key=f"practice_answer_{problem_id}")
            submitted = st.form_submit_button("답 제출하기 🐥")
        if submitted:
            if answer is None or not str(answer).strip():
                st.warning("🐣 아직 답이 비어 있어요. 답을 고르거나 적은 뒤 함께 도전해 봐요!")
            else:
                is_correct = normalize_practice_answer(answer) == normalize_practice_answer(correct)
                results[problem_id] = {"answer": answer, "correct": is_correct}
                st.rerun()
        if problem_id in results:
            result = results[problem_id]
            st.write("**제출한 답:** " + str(result["answer"]))
            if result["correct"]:
                st.success("🎉 딩동댕! 정답이에요! 한 걸음 더 성장했어요. 정말 잘했어요! 🐥✨")
            else:
                st.warning("🌷 아깝지만 아직 정답은 아니에요! 도전한 너, 멋져요. 설명을 보고 한 번 더 해 봐요! 💪🐣")
                st.write("**정답:** " + correct)
            st.info("💡 " + explanation)
            st.caption("답을 바꾸었다면 ‘답 제출하기’를 다시 눌러 주세요. 위 결과는 마지막으로 제출한 답의 결과예요.")
    st.caption("연습 결과는 현재 접속 세션에서만 유지돼요. LEVEL은 난이도를 뜻하며 문장 형식 번호와는 달라요.")


def render_analysis_dashboard():
    st.title("📊 나의 학습 분석")
    summary = get_learning_summary()
    total_questions = summary["total_questions"]
    overall_rate = summary["overall_rate"]
    achievement = get_achievement_label(overall_rate)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 정답 개수", summary["correct"])
    col2.metric("전체 정답률", f"{overall_rate:.1f}%")
    col3.metric("학습 완료 문항 수", summary["attempted"])
    col4.metric("학습 성취 수준", achievement[:8] + "..." if len(achievement) > 8 else achievement)

    if total_questions:
        progress_pct = summary["progress"]
        st.progress(progress_pct / 100, text=f"진행률: {summary['attempted']} / {total_questions} 문항 ({progress_pct:.1f}%)")
    else:
        st.info("아직 문제를 풀지 않았어요. 학습을 시작해 보세요. 🐣")

    st.markdown("### 📈 단계별 학습 성취도 그래프")
    chart_data = pd.DataFrame([
        {"단계": f"{level}단계", "정답률": info["rate"]}
        for level, info in summary["stage_data"].items()
    ])
    if not chart_data.empty:
        st.bar_chart(chart_data.set_index("단계")["정답률"], use_container_width=True)
    else:
        st.info("아직 단계별 결과가 없어요.")

    st.markdown("### 📋 단계별 학습 결과표")
    table_data = []
    for level, info in summary["stage_data"].items():
        table_data.append({
            "단계": f"{level}단계",
            "전체 문항": info["total"],
            "정답": info["correct"],
            "오답": info["incorrect"],
            "미응답": info["unanswered"],
            "정답률": f"{info['rate']:.1f}%",
        })
    table_df = pd.DataFrame(table_data)
    st.dataframe(table_df, use_container_width=True)

    st.markdown("### 🧠 학생 맞춤형 학습 분석 및 피드백")
    st.success(achievement)
    lowest_level = min(summary["stage_data"].items(), key=lambda item: item[1]["rate"])[0]
    st.info(f"현재 가장 보충 학습이 필요한 영역은 {lowest_level}단계입니다. {get_stage_guidance(lowest_level)}")

    st.markdown("### ❌ 틀린 문제 다시 보기")
    results = st.session_state.get("practice_results", {})
    wrong_ids = [problem_id for problem_id, record in results.items() if record.get("correct") is False]
    if wrong_ids:
        selected_wrong = st.selectbox("틀린 문제 선택", wrong_ids, format_func=lambda pid: f"{pid.split('_')[0]}단계 {pid.split('_')[1]}번 문제")
        level, question_number, prompt, instruction, choices, correct, explanation = get_question_detail(selected_wrong)
        selected_answer = results[selected_wrong].get("answer")
        st.write(f"**문제:** {prompt}")
        st.write(f"**선택한 답:** {selected_answer}")
        st.write(f"**정답:** {correct}")
        st.info(f"**문법 설명:** {explanation}")

        retry_results = st.session_state.setdefault("retry_results", {})
        with st.form(f"retry_form_{selected_wrong}"):
            if choices is None:
                retry_answer = st.text_input("다시 풀어 보세요", key=f"retry_answer_{selected_wrong}", placeholder="정답을 입력해 보세요")
            else:
                retry_answer = st.radio("다시 선택해 보세요", choices, index=None, key=f"retry_answer_{selected_wrong}")
            retry_submit = st.form_submit_button("재도전하기")

        if retry_submit:
            if retry_answer is None or not str(retry_answer).strip():
                st.warning("재도전할 답을 입력해 주세요.")
            else:
                retry_correct = normalize_practice_answer(retry_answer) == normalize_practice_answer(correct)
                retry_results[selected_wrong] = {
                    "initial_answer": selected_answer,
                    "initial_correct": False,
                    "retry_answer": retry_answer,
                    "retry_correct": retry_correct,
                }
                st.rerun()

        if selected_wrong in retry_results:
            retry_record = retry_results[selected_wrong]
            retry_rate = get_retry_summary()["rate"]
            if retry_record.get("retry_correct"):
                st.success("재도전 성공! 정답을 맞혔어요. 꾸준히 연습하고 있어요! ✨")
            else:
                st.warning("재도전 결과는 아직 부족하지만, 정답을 확인하고 다시 연습해 보세요.")
            st.caption(f"재도전 전: 0% / 재도전 후: {retry_rate}% (틀린 문제 기준)")
    else:
        st.info("틀린 문제가 아직 없어요. 지금처럼 꾸준히 학습하면 더 높은 성취도를 기대할 수 있어요! 🌟")

    st.markdown("### 🔄 학습 결과 초기화")
    if st.button("처음부터 다시 학습하기"):
        st.session_state.reset_confirm = True

    if st.session_state.get("reset_confirm"):
        st.warning("정말로 지금까지의 학습 결과를 모두 지우시겠어요? 이 작업은 되돌릴 수 없어요.")
        col_reset_yes, col_reset_no = st.columns(2)
        if col_reset_yes.button("네, 초기화할게요"):
            reset_learning_state()
            st.success("학습 결과를 초기화했습니다. 새로 시작해 보세요! 🚀")
            st.rerun()
        if col_reset_no.button("취소"):
            st.session_state.reset_confirm = False
            st.rerun()


if not st.session_state.app_started:
    render_student_info_form()
    st.stop()

student_info = st.session_state.get("student_info", {})
student_name = student_info.get("name", "학생")

profile_col, edit_col = st.columns([5, 1])
with profile_col:
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#f4f8ff,#fff7e6);border:1px solid #dfe9ff;border-radius:22px;padding:18px 22px;margin:0 0 18px 0;box-shadow:0 8px 20px rgba(44,76,126,0.08);">
          <div style="display:flex;flex-wrap:wrap;gap:18px;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-size:0.8rem;color:#5d6c86;letter-spacing:0.12em;font-weight:800;">STUDENT PROFILE</div>
              <div style="font-size:1.9rem;font-weight:800;color:#264a7f;margin-top:8px;">{student_name} 학생</div>
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:10px;">
              <span style="background:#e0ebff;border-radius:999px;padding:9px 14px;font-size:0.9rem;color:#243b70;font-weight:700;">학년: {student_info.get('grade', '-')}</span>
              <span style="background:#e7f9ef;border-radius:999px;padding:9px 14px;font-size:0.9rem;color:#215b4a;font-weight:700;">반: {student_info.get('class_name', '-')}</span>
              <span style="background:#fff0d6;border-radius:999px;padding:9px 14px;font-size:0.9rem;color:#81581a;font-weight:700;">목표: {student_info.get('learning_goal', '-')}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with edit_col:
    if st.button("학생 정보 수정", use_container_width=True):
        st.session_state.app_started = False
        st.rerun()

st.title("5형식 문장 어렵지 않아요")
st.markdown('<div class="mascot"><span style="font-size:2rem" aria-hidden="true">🐣 🌱 🧩</span><br><b>삐약 선생님과 한 문장씩, 차근차근!</b><br>틀려도 괜찮아요. 헷갈리는 순간에는 활동 옆 ‘도와줘’를 눌러 보세요.</div>', unsafe_allow_html=True)
st.write("성분 블록을 고르고, 단어를 넣고, 순서를 바꾸며 영어 문장의 뼈대를 살펴보세요.")
st.caption("① 블록 추가 → ② 단어 또는 구 입력 → ③ ↑ ↓로 순서 변경 → ④ 형식 확인")

with st.sidebar:
    st.markdown("### 👤 학생 정보")
    st.write(f"이름: **{student_name}**")
    st.write(f"학년: **{student_info.get('grade', '-')}**")
    st.write(f"반: **{student_info.get('class_name', '-')}**")
    st.write(f"목표: **{student_info.get('learning_goal', '-')}**")
    st.divider()
    activity_heading("📖 형식별 예제", "examples", sidebar=True)
    st.caption("예제를 누르면 현재 조립 내용이 예제로 바뀝니다.")
    for number, roles in enumerate(PATTERNS, start=1):
        st.button(f"{number}형식 · {' + '.join(roles)}", key=f"example_{number}", on_click=load_example, args=(number,), use_container_width=True)
    st.divider()
    st.markdown("**성분 도움말**")
    for role, meaning in ROLES.items():
        st.write(f"**{role}** — {meaning}")
    st.info("4형식에는 O 블록이 두 개 필요해요. 한 블록에는 ‘a book’처럼 여러 단어를 넣어도 됩니다.")

assembly_tab, practice_tab, analysis_tab = st.tabs(["🧩 문장 조립소", "🌈 연습하기", "📊 나의 학습 분석"])
with assembly_tab:
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

with practice_tab:
    render_practice()

with analysis_tab:
    render_analysis_dashboard()
