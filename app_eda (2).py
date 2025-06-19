import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io

st.set_page_config(page_title="Population Trends EDA", layout="wide")

# ---------------------
# Home 화면
# ---------------------
def Home():
    st.title("🏠 Home")
    st.markdown("""
    분석은 **탭(Tab) 구조**로 구성됩니다.  
    *(예: \"기초 통계\", \"연도별 추이\", \"지역별 분석\", \"변화량 분석\", \"시각화\")*

    분석에는 다음이 포함되어야 합니다:

    - 🔍 **결측치 및 중복 확인**
    - 📈 **연도별 전체 인구 추이 그래프**
    - 🗺️ **지역별 인구 변화량 순위**
    - 🔼 **증감률 상위 지역 및 연도 도출**
    - 🧩 **누적영역그래프 등 적절한 시각화**
    """)

    st.info("""
    📁 사용 파일: `population_trends.csv`

    연도별·지역별 인구, 출생아 수, 사망자 수 등 포함된 대한민국 인구 동향 데이터
    """)

# ---------------------
# EDA 화면
# ---------------------
def PopulationTrendsEDA():
    st.title("📊 Population Trends EDA")
    uploaded_file = st.file_uploader("population_trends.csv 파일 업로드", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        # 전처리
        df.loc[df['지역'] == '세종'] = df.loc[df['지역'] == '세종'].replace('-', 0)
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        tabs = st.tabs([
            "📌 기초 통계", "📈 연도별 추이", "📍 지역별 분석", "📊 변화량 분석", "🧩 시각화"
        ])

        # Tab 1: 기초 통계
        with tabs[0]:
            st.subheader("결측치 및 중복 확인")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.write("🔎 Describe")
            st.dataframe(df.describe())
            st.write("❗ 결측치 수")
            st.dataframe(df.isnull().sum())
            st.write("📎 중복 행 수: ", df.duplicated().sum())

        # Tab 2: 연도별 전체 인구 추이
        with tabs[1]:
            st.subheader("Total Population by Year")
            df_nation = df[df['지역'] == '전국']
            fig, ax = plt.subplots()
            sns.lineplot(x='연도', y='인구', data=df_nation, marker='o', ax=ax)
            recent = df_nation.sort_values('연도').tail(3)
            delta = recent['출생아수(명)'].mean() - recent['사망자수(명)'].mean()
            pred = recent['인구'].iloc[-1] + delta * (2035 - recent['연도'].iloc[-1])
            ax.axhline(pred, ls='--', color='gray')
            ax.text(2034, pred, f"Predicted 2035: {int(pred):,}")
            ax.set_title("Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)

        # Tab 3: 지역별 인구 변화량 순위
        with tabs[2]:
            st.subheader("Regional Change in Population (Last 5 years)")
            pivot = df.pivot(index='연도', columns='지역', values='인구')
            delta = pivot.iloc[-1] - pivot.iloc[-6]
            rate = (delta / pivot.iloc[-6]) * 100

            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            df_delta = pd.DataFrame({
                'Region': [region_map.get(r, r) for r in delta.index],
                'Change (K)': delta.values / 1000,
                'Change Rate (%)': rate.values
            }).query("Region != '전국'").sort_values("Change (K)", ascending=False)

            fig, ax = plt.subplots()
            sns.barplot(data=df_delta, x='Change (K)', y='Region', ax=ax)
            for i, v in enumerate(df_delta['Change (K)']):
                ax.text(v, i, f"{v:,.1f}", va='center')
            ax.set_title("Population Change")
            ax.set_xlabel("Change in Thousands")
            st.pyplot(fig)

            fig2, ax2 = plt.subplots()
            sns.barplot(data=df_delta, x='Change Rate (%)', y='Region', ax=ax2)
            for i, v in enumerate(df_delta['Change Rate (%)']):
                ax2.text(v, i, f"{v:.1f}%", va='center')
            ax2.set_title("Population Change Rate")
            ax2.set_xlabel("Percent Change")
            st.pyplot(fig2)

            st.markdown("""
            **Interpretation:** The top-growing regions are likely urban centers like Gyeonggi and Seoul. Declining regions may face aging and migration issues.
            """)

        # Tab 4: 증감률 상위 지역 및 연도
        with tabs[3]:
            st.subheader("Top 100 Increase/Decrease Cases")
            df_temp = df[df['지역'] != '전국'].copy()
            df_temp.sort_values(['지역', '연도'], inplace=True)
            df_temp['증감'] = df_temp.groupby('지역')['인구'].diff()
            top = df_temp.nlargest(100, '증감')

            def highlight(val):
                color = '#a8dadc' if val > 0 else '#f4a261'
                return f'background-color: {color}'

            st.dataframe(
                top[['연도', '지역', '인구', '증감']].style
                    .format({'인구': '{:,.0f}', '증감': '{:,.0f}'})
                    .applymap(highlight, subset=['증감'])
            )

        # Tab 5: 누적 영역 그래프
        with tabs[4]:
            st.subheader("Stacked Area by Region")
            df_area = df.pivot(index='연도', columns='지역', values='인구')
            if '전국' in df_area.columns:
                df_area.drop(columns='전국', inplace=True)

            df_area.columns = [region_map.get(c, c) for c in df_area.columns]
            fig, ax = plt.subplots(figsize=(12, 6))
            df_area.plot.area(ax=ax, cmap='tab20')
            ax.set_title("Regional Population Area Chart")
            st.pyplot(fig)
    else:
        st.info("population_trends.csv 파일을 먼저 업로드해주세요.")

# ---------------------
# 로그인/회원가입/비밀번호찾기 화면
# ---------------------
def Login():
    st.title("🔐 로그인")
    st.text_input("이메일")
    st.text_input("비밀번호", type="password")
    st.button("로그인")

def Register():
    st.title("📄 회원가입")
    st.text_input("이메일")
    st.text_input("비밀번호", type="password")
    st.text_input("성명")
    st.selectbox("성별", ["선택 안함", "남성", "여성"])
    st.text_input("휴대전화번호")
    st.button("회원가입")

def FindPW():
    st.title("🔍 비밀번호 찾기")
    st.text_input("이메일")
    st.button("비밀번호 재설정 메일 전송")

# ---------------------
# 메인 라우터 메뉴 (고정 사이드바 형태로 변경)
# ---------------------
menu = st.sidebar.radio(
    "페이지 선택",
    ["Home", "Login", "Register", "Find PW", "EDA"],
    format_func=lambda x: {
        "Home": "🏠 Home",
        "Login": "🔐 Login",
        "Register": "📄 Register",
        "Find PW": "🔍 Find PW",
        "EDA": "📊 EDA"
    }[x]
)

if menu == "Home":
    Home()
elif menu == "EDA":
    PopulationTrendsEDA()
elif menu == "Login":
    Login()
elif menu == "Register":
    Register()
elif menu == "Find PW":
    FindPW()