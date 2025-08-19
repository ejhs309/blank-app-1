import streamlit as st
import sqlite3
from datetime import datetime

# --- 데이터베이스 설정 ---

# 데이터베이스 연결 및 테이블 생성 함수
def init_db():
    # 'students.db'라는 이름의 데이터베이스 파일에 연결합니다. 파일이 없으면 자동 생성됩니다.
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    # 'students' 테이블 (학생 이름 저장)
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    # 'records' 테이블 (학생별 기록 저장)
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

# --- 데이터베이스 CRUD 함수 (생성, 읽기, 수정, 삭제) ---

# 학생 추가
def add_student(name):
    try:
        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        c.execute("INSERT INTO students (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError: # 이름 중복 방지
        return False

# 모든 학생 조회
def get_students():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM students ORDER BY name ASC")
    students = c.fetchall()
    conn.close()
    return students

# 학생 삭제
def delete_student(student_id):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

# 기록 추가
def add_record(student_id, date, content):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("INSERT INTO records (student_id, date, content) VALUES (?, ?, ?)",
              (student_id, date, content))
    conn.commit()
    conn.close()

# 특정 학생의 모든 기록 조회
def get_records(student_id):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT id, date, content FROM records WHERE student_id = ? ORDER BY date DESC", (student_id,))
    records = c.fetchall()
    conn.close()
    return records
    
# 특정 기록 삭제
def delete_record(record_id):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("DELETE FROM records WHERE id=?", (record_id,))
    conn.commit()
    conn.close()


# --- Streamlit 앱 UI 구성 ---

# 페이지 기본 설정
st.set_page_config(page_title="학생 기록 앱", page_icon="📝", layout="wide")

# 앱 시작 시 데이터베이스 초기화
init_db()

st.title("📝 학급 학생 특이사항 기록부")
st.write("학생별 관찰 및 상담 내용을 안전하게 기록하고 관리하세요.")
st.write("---")

# --- 사이드바: 학생 관리 ---
st.sidebar.header("🎓 학생 관리")

# 학생 추가 섹션
with st.sidebar.expander("➕ 새 학생 추가"):
    new_student_name = st.text_input("학생 이름", key="new_student_name")
    if st.button("추가하기"):
        if new_student_name:
            if add_student(new_student_name):
                st.sidebar.success(f"'{new_student_name}' 학생을 추가했습니다.")
                st.rerun() # 학생 목록을 즉시 새로고침
            else:
                st.sidebar.error("이미 등록된 이름입니다.")
        else:
            st.sidebar.warning("학생 이름을 입력해주세요.")

# 학생 선택 및 삭제 섹션
students = get_students()
student_dict = {name: id for id, name in students} # 이름으로 id를 찾기 위한 딕셔너리

if not students:
    st.warning("먼저 사이드바에서 학생을 추가해주세요.")
else:
    selected_student_name = st.sidebar.selectbox("기록을 볼 학생 선택", options=student_dict.keys())
    selected_student_id = student_dict[selected_student_name]

    if st.sidebar.button("🗑️ 선택한 학생 삭제", type="primary"):
        delete_student(selected_student_id)
        st.sidebar.success(f"'{selected_student_name}' 학생 정보를 모두 삭제했습니다.")
        st.rerun()

    # --- 메인 화면: 기록 관리 ---
    st.header(f"📜 '{selected_student_name}' 학생의 기록")

    # 새 기록 추가 폼
    with st.expander("✍️ 새 기록 추가하기", expanded=True):
        record_date = st.date_input("날짜", datetime.now())
        record_content = st.text_area("내용", height=150, placeholder="관찰 내용, 상담 기록 등을 입력하세요.")
        if st.button("기록 저장"):
            if record_content:
                add_record(selected_student_id, record_date.strftime("%Y-%m-%d"), record_content)
                st.success("기록이 성공적으로 저장되었습니다.")
                st.rerun()
            else:
                st.warning("기록할 내용을 입력해주세요.")
    
    st.write("---")

    # 기존 기록 조회
    st.subheader("📚 전체 기록 보기")
    records = get_records(selected_student_id)

    if not records:
        st.info("아직 작성된 기록이 없습니다.")
    else:
        for record in records:
            record_id, record_date, record_content = record
            with st.container(border=True):
                st.markdown(f"**🗓️ 날짜: {record_date}**")
                st.markdown(record_content.replace("\n", "<br>"), unsafe_allow_html=True)
                # 각 기록마다 고유한 키를 가진 삭제 버튼 생성
                if st.button("이 기록 삭제", key=f"delete_record_{record_id}", type="secondary"):
                    delete_record(record_id)
                    st.rerun()