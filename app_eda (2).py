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

    st.info("📁 사용 파일: `population_trends.csv`\n\n- 연도별·지역별 인구, 출생아 수, 사망자 수 등 포함된 대한민국 인구 동향 데이터")

# ---------------------
# EDA 화면
# ---------------------
def PopulationTrendsEDA():
    st.title("📊 Population Trends EDA")
    uploaded_file = st.file_uploader("population_trends.csv 파일 업로드", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        df.replace("-", 0, inplace=True)
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        tabs = st.tabs([
            "📌 기초 통계", "📈 연도별 추이", "📍 지역별 분석", "📊 변화량 분석", "🧩 시각화"
        ])

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

        with tabs[1]:
            st.subheader("전국 인구 추이 (연도별)")
            df_nation = df[df['지역'] == '전국']
            fig, ax = plt.subplots()
            sns.lineplot(x='연도', y='인구', data=df_nation, marker='o', ax=ax)
            recent = df_nation.sort_values('연도').tail(3)
            delta = recent['출생아수(명)'].mean() - recent['사망자수(명)'].mean()
            pred = recent['인구'].iloc[-1] + delta * (2035 - recent['연도'].iloc[-1])
            ax.axhline(pred, ls='--', color='gray')
            ax.text(2034, pred, f"2035 예측: {int(pred):,}")
            st.pyplot(fig)

        with tabs[2]:
            st.subheader("지역별 인구 변화량 순위")
            pivot = df.pivot(index='연도', columns='지역', values='인구')
            delta = pivot.iloc[-1] - pivot.iloc[-6]
            rate = (delta / pivot.iloc[-6]) * 100
            df_delta = pd.DataFrame({
                '지역': delta.index,
                '증감량(천)': delta.values / 1000,
                '증감률(%)': rate.values
            }).query("지역 != '전국'").sort_values("증감량(천)", ascending=False)

            st.dataframe(df_delta.reset_index(drop=True))
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.barplot(data=df_delta, y='지역', x='증감량(천)', ax=ax)
            ax.set_title("최근 5년간 지역별 인구 증감량")
            st.pyplot(fig)

        with tabs[3]:
            st.subheader("증감률 상위 지역 및 연도")
            df_temp = df[df['지역'] != '전국'].copy()
            df_temp.sort_values(['지역', '연도'], inplace=True)
            df_temp['증감'] = df_temp.groupby('지역')['인구'].diff()
            top = df_temp.nlargest(100, '증감')

            def highlight(val):
                return 'background-color: #a8dadc' if val > 0 else 'background-color: #f4a261'

            st.dataframe(
                top[['연도', '지역', '인구', '증감']].style
                    .format({'인구': '{:,.0f}', '증감': '{:,.0f}'})
                    .applymap(highlight, subset=['증감'])
            )

        with tabs[4]:
            st.subheader("누적 영역 그래프")
            df_area = df.pivot(index='연도', columns='지역', values='인구')
            if '전국' in df_area.columns:
                df_area.drop(columns='전국', inplace=True)
            fig, ax = plt.subplots(figsize=(12, 6))
            df_area.plot.area(ax=ax, cmap='tab20')
            ax.set_title("지역별 누적 인구 영역 그래프")
            st.pyplot(fig)
    else:
        st.info("population_trends.csv 파일을 먼저 업로드해주세요.")

# ---------------------
# 메인 라우터
# ---------------------
menu = st.sidebar.radio("페이지 선택", ["Home", "EDA"])

if menu == "Home":
    Home()
elif menu == "EDA":
    PopulationTrendsEDA()