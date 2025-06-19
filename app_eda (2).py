# EDA 클래스의 마지막에 아래 블록 추가
# 기존 "로그 변환" 탭 코드 아래에 바로 붙이면 됨

        # -------------------------
        # 🔍 Population Trends 추가 분석
        # -------------------------
        st.title("📈 Population Trends 분석")
        pop_file = st.file_uploader("population_trends.csv 업로드", type="csv", key="pop")
        if pop_file:
            df_pop = pd.read_csv(pop_file)

            # 전처리
            df_pop.replace("-", 0, inplace=True)
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df_pop[col] = pd.to_numeric(df_pop[col], errors='coerce')

            tab_option = st.radio("🔍 Population 분석 항목", [
                "기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"
            ], horizontal=True)

            # 1. 기초 통계
            if tab_option == "기초 통계":
                st.subheader("📊 기초 통계 및 결측치")
                buffer = io.StringIO()
                df_pop.info(buf=buffer)
                st.text(buffer.getvalue())
                st.dataframe(df_pop.describe())
                st.write("결측치:")
                st.dataframe(df_pop.isnull().sum())
                st.write("중복 행 개수:", df_pop.duplicated().sum())

            # 2. 연도별 추이
            elif tab_option == "연도별 추이":
                st.subheader("📈 연도별 전체 인구 추이")
                df_nation = df_pop[df_pop['지역'] == '전국']
                fig, ax = plt.subplots()
                sns.lineplot(x='연도', y='인구', data=df_nation, marker='o', ax=ax)
                ax.set_title("Population Trend by Year")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")

                # 인구 예측 (2035)
                recent = df_nation.sort_values('연도').tail(3)
                delta = (recent['출생아수(명)'].mean() - recent['사망자수(명)'].mean())
                last_year = recent['연도'].iloc[-1]
                pred_2035 = recent['인구'].iloc[-1] + delta * (2035 - last_year)
                ax.axhline(pred_2035, color='gray', linestyle='--')
                ax.text(2034, pred_2035, f'Predicted: {int(pred_2035):,}')
                st.pyplot(fig)

            # 3. 지역별 분석
            elif tab_option == "지역별 분석":
                st.subheader("📌 최근 5년 지역별 인구 변화")
                pivot = df_pop.pivot(index='연도', columns='지역', values='인구')
                diff_5y = pivot.iloc[-1] - pivot.iloc[-6]
                rate_5y = (diff_5y / pivot.iloc[-6]) * 100

                df_change = pd.DataFrame({
                    '지역': diff_5y.index,
                    '증감량(천명)': diff_5y.values / 1000,
                    '증감률(%)': rate_5y.values
                }).sort_values('증감량(천명)', ascending=False)

                fig1, ax1 = plt.subplots(figsize=(10, 6))
                sns.barplot(data=df_change, y='지역', x='증감량(천명)', ax=ax1)
                ax1.set_title("Change (k)")
                st.pyplot(fig1)

                fig2, ax2 = plt.subplots(figsize=(10, 6))
                sns.barplot(data=df_change, y='지역', x='증감률(%)', ax=ax2)
                ax2.set_title("Change Rate (%)")
                st.pyplot(fig2)

            # 4. 증감량 분석
            elif tab_option == "변화량 분석":
                st.subheader("📈 증감률 상위 사례")
                df_temp = df_pop[df_pop['지역'] != '전국'].copy()
                df_temp.sort_values(['지역', '연도'], inplace=True)
                df_temp['증감'] = df_temp.groupby('지역')['인구'].diff()
                top100 = df_temp.nlargest(100, '증감')

                def highlight(val):
                    color = '#a8dadc' if val > 0 else '#f4a261'
                    return f'background-color: {color}'

                st.dataframe(top100.style
                    .format({"인구": "{:,}", "증감": "{:,}"})
                    .applymap(highlight, subset=['증감']))

            # 5. 누적영역 시각화
            elif tab_option == "시각화":
                st.subheader("📊 누적 영역 그래프")
                df_area = df_pop.pivot(index='연도', columns='지역', values='인구')
                df_area = df_area.drop(columns=['전국'])

                fig, ax = plt.subplots(figsize=(12, 6))
                df_area.plot.area(ax=ax, cmap='tab20')
                ax.set_title("Stacked Area by Region")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                st.pyplot(fig)