import streamlit as st
from openai import OpenAI
from fpdf import FPDF
from PIL import Image
import pytesseract
import re, json, os
from datetime import datetime
import tempfile

# ✅ OCR 설정
import os

# 클라우드 환경에서는 OCR 꺼두기
if not os.environ.get("STREAMLIT_SERVER"):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if not os.environ.get("STREAMLIT_SERVER"):
    st.markdown("### 📸 손글씨 사진 업로드 (OCR)")
    ocr_image = st.file_uploader("👉 손글씨 이미지 업로드", type=["jpg", "png"])

    if ocr_image:
        try:
            img = Image.open(ocr_image)
            ocr_text = pytesseract.image_to_string(img, lang="kor")
            st.success("✅ 인식 완료!")
        except Exception as e:
            st.error(f"❌ OCR 오류: {e}")

# OpenAI 연결
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 저장 파일
HISTORY_FILE = "history.json"

# 페이지 설정
st.set_page_config(page_title="나의 이야기를 쌓는 15분", layout="centered")

# 스타일
st.markdown("""
    <style>
    body { background-color: #f0fbf9 !important; }
    html, body, [class*="css"] {
        font-size: 17px !important;
        font-family: 'Pretendard', sans-serif;
        line-height: 1.6;
        color: #2e2e2e;
    }
    h3 { font-size: 26px !important; font-weight: 600; margin-top: 1.5rem; }
    p { font-size: 18px !important; }
    </style>
""", unsafe_allow_html=True)

# 제목 + 로고
col1, col2 = st.columns([6, 2])
with col1:
    st.markdown("<h1 style='font-size: 32px;'>나의 이야기를 쌓는 15분</h1>", unsafe_allow_html=True)
with col2:
    st.image("letterbrick_logo.png", width=300)

# 히스토리 로드/저장
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(data):
    history = load_history()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history[now] = data
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# PDF 생성 함수
def generate_pdf(data: dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Nanum", "", "NanumGothic.ttf", uni=True)
    pdf.set_font("Nanum", size=12)
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.cell(0, 10, "레터브릭 필사 평가 리포트", ln=True, align="C")
    pdf.ln(10)

    for section, content in data.items():
        pdf.set_font("Nanum", 'B', 12)
        pdf.cell(0, 10, f"■ {section}", ln=True)
        pdf.set_font("Nanum", size=12)
        for line in content.split("\n"):
            pdf.multi_cell(0, 8, line)
        pdf.ln(5)

    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_path.name)
    return tmp_path.name

# 히스토리 보기
with st.expander("📚 나의 필사 히스토리 보기"):
    history = load_history()
    if history:
        for date, item in sorted(history.items(), reverse=True):
            st.markdown(f"### 📅 {date}")
            for key, value in item.items():
                st.markdown(f"**{key}**:\n\n{value}")
            st.markdown("---")
    else:
        st.info("아직 저장된 히스토리가 없습니다.")

# ✅ OCR 업로드
st.markdown("<h3>📸 손글씨 사진 업로드 (OCR)</h3>", unsafe_allow_html=True)
ocr_image = st.file_uploader("👉 필사한 손글씨 이미지를 업로드하세요 (jpg, png)", type=["jpg", "jpeg", "png"], key="ocr_upload")

ocr_text = ""
if ocr_image:
    try:
        img = Image.open(ocr_image)
        ocr_text = pytesseract.image_to_string(img, lang="kor")
        st.success("✅ 텍스트 인식 완료!")
        st.text_area("📝 인식된 문장", value=ocr_text, height=120, disabled=True)
    except Exception as e:
        st.error(f"❌ OCR 오류 발생: {e}")

# 📝 문장 필사
st.markdown("<h3>📝 오늘의 문장 필사</h3>", unsafe_allow_html=True)
st.markdown("<p>오늘의 문장을 직접 필사해보세요.</p>", unsafe_allow_html=True)
original_text = st.text_area("", key="original")

if st.button("📋 문장 분석 요청", key="analyze_btn") and original_text:
    with st.spinner("문장 분석 중입니다..."):
        prompt = f"""
        문예창작 교수처럼 아래 문장을 분석해 주세요.
        각 항목은 Markdown 형식으로 출력하고, 중요한 단어는 **굵게** 표시해 주세요.

        ✅ 형태소 분석: 단어(품사) + 조사
        ✅ 의미 분석: 주요 단어 → 의미 설명 (표 형식)
        ✅ 수사법 분석: 어떤 수사법을 사용했고 어떤 효과가 있는지 설명

        문장: "{original_text}"
        """
        res = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
        st.markdown("<h3>🔎 문장 분석 결과</h3>", unsafe_allow_html=True)
        st.markdown(res.choices[0].message.content)

# 🔧 형태변형 필사
st.markdown("<h3>🔧 형태변형 필사</h3>", unsafe_allow_html=True)
st.markdown("<p>원문의 구조나 어순을 바꿔 표현해보세요.</p>", unsafe_allow_html=True)
form1 = st.text_area("", key="form1")

if st.button("🤖 AI 피드백 받기 (형태변형)", key="form1_btn"):
    with st.spinner("AI가 평가 중입니다..."):

        # 평가
        p1 = f"""
        아래 문장은 사용자의 형태변형 필사입니다.
        아래 기준으로 엄격하게 평가해 주세요:
        - 구조적 변형도 (30점)
        - 의미 보존 (30점)
        - 문법 정확성 (20점)
        - 표현력 (20점)

        항목별 점수 + 총점 + 개선 예시 포함 (Markdown 형식)

        문장: "{form1}"
        """
        r1 = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": p1}])
        st.markdown("<h3>📊 형태변형 필사 평가</h3>", unsafe_allow_html=True)
        st.markdown(r1.choices[0].message.content)

        # 교수 평가
        prof1 = f"""
        아래 문장을 **AI 문창과 교수**처럼 평가해 주세요.
        - 작법적으로 한 문장으로 피드백
        - 어미는 모두 존댓말(~입니다 / ~합니다 등)로 통일해 주세요.

        문장: "{form1}"
        """
        rp1 = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prof1}])
        st.markdown("<h3>🎓 AI 문창과 교수의 한 줄 평 (형태변형)</h3>", unsafe_allow_html=True)
        st.markdown(rp1.choices[0].message.content)

# 🖌️ 창의적 필사
st.markdown("<h3>🖌️ 창의적 필사</h3>", unsafe_allow_html=True)
st.markdown("<p>자유롭게 상상력과 감성을 담아 창의적으로 표현해보세요.</p>", unsafe_allow_html=True)
form2 = st.text_area("", key="form2")

if st.button("🤖 AI 피드백 받기 (창의적)", key="form2_btn"):
    with st.spinner("AI가 평가 중입니다..."):

        # 평가
        p2 = f"""
        아래 문장은 사용자의 창의적 필사입니다.
        아래 기준으로 엄격하게 평가해 주세요:
        - 감성 전달력
        - 창의성
        - 문장 완성도
        - 스타일 적합성

        1. 별점 (숫자만, 1~5점)
        2. 장점
        3. 개선점
        4. 총평

        별점은 반드시 숫자만 표시하고, 나머지는 Markdown 형식으로 출력해 주세요.

        문장: "{form2}"
        """
        r2 = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": p2}])
        full_response = r2.choices[0].message.content

        # 별점 추출 (정확하게!)
        star_match = re.search(r"\b([1-5](?:\.5)?)\b", full_response)
        if star_match:
            score = float(star_match.group(1))
            fixed = round(score * 2) / 2
            full = int(fixed)
            half = 1 if fixed % 1 == 0.5 else 0
            stars = "⭐️" * full + "☆" * half
            st.markdown("<h3>🖌️ 창의적 필사 평가</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:24px'>{stars} ({fixed}점)</p>", unsafe_allow_html=True)

        # 피드백 전체 출력
        st.markdown(full_response)

        # 교수 평가
        prof2 = f"""
        아래 문장을 **AI 문창과 교수**처럼 평가해 주세요.
        - 작법적으로 한 문장으로
        - 어미는 모두 **존댓말**(~입니다 / ~합니다)로 작성해 주세요.

        문장: "{form2}"
        """
        rp2 = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prof2}])
        st.markdown("<h3>🎓 AI 문창과 교수의 한 줄 평 (창의적 필사)</h3>", unsafe_allow_html=True)
        st.markdown(rp2.choices[0].message.content)
        result = {
            "📝 원문": original_text,
            "🔧 형태변형": form1,
            "🖌️ 창의적": form2,
            "🔍 분석": analysis,
            "📊 형태변형 평가": f1_eval,
            "🎓 형태 한 줄 평": pf1_line,
            "🖌️ 창의 평가": f2_eval,
            "🎓 창의 한 줄 평": pf2_line
        }
        save_history(result)
        st.success("📥 저장 완료! 히스토리에 추가되었습니다.")

        pdf_file = generate_pdf(result)
        with open(pdf_file, "rb") as f:
            st.download_button(
                label="📄 PDF로 저장하기",
                data=f,
                file_name="letterbrick_report.pdf",
                mime="application/pdf"
            )
