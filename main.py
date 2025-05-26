import streamlit as st
import pandas as pd
import plotly.graph_objects as go

@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df.columns = [col.strip() for col in df.columns]
    df = df[df['Fuel'].notnull()]
    df = df[df['Year'].notnull()]
    df['Year'] = df['Year'].astype(int)
    return df

df = load_data()

# st.title("해운 연료별 연도별 탄소비용 계산기")

fuels = df['Fuel'].unique()
selected_fuel = st.selectbox("연료(Fuel)를 선택하세요:", fuels)

fuel_df = df[df['Fuel'] == selected_fuel].sort_values("Year").reset_index(drop=True)
editable_cols = ["LCV", "Fuel GFI", "Tier1 GFI", "Tier2 GFI"]

# ---- 입력값 표 transpose ----
st.markdown("연도별 입력값 (행/열 전치, 직접 수정)")
input_t_df = round(fuel_df[["Year"] + editable_cols], 3).set_index("Year").T
edited_t_df = st.data_editor(
    input_t_df,
    num_rows="fixed",
    use_container_width=True
)

# transpose된 입력값을 다시 Year별로 복원
edited_df = edited_t_df.T.reset_index()
edited_df = edited_df.rename(columns={"index": "Year"})
edited_df["Year"] = edited_df["Year"].astype(int)
for col in editable_cols:
    edited_df[col] = pd.to_numeric(edited_df[col], errors="coerce")

def calculate_tier1(fuel_gfi, tier1_gfi, tier2_gfi, lcv):
    if fuel_gfi > tier1_gfi:
        return (min(fuel_gfi, tier2_gfi) - tier1_gfi) * lcv * 100
    else:
        return 0

def calculate_tier2(fuel_gfi, tier2_gfi, lcv):
    if fuel_gfi > tier2_gfi:
        return (fuel_gfi - tier2_gfi) * lcv * 380
    else:
        return 0

calc_results = []
for _, row in edited_df.iterrows():
    tier1 = calculate_tier1(float(row['Fuel GFI']), float(row['Tier1 GFI']), float(row['Tier2 GFI']), float(row['LCV']))
    tier2 = calculate_tier2(float(row['Fuel GFI']), float(row['Tier2 GFI']), float(row['LCV']))
    total = tier1 + tier2
    calc_results.append({
        "Year": int(row['Year']),
        "Tier1 Cost": round(tier1, 1),
        "Tier2 Cost": round(tier2, 1),
        "Total Cost": round(total, 1)
    })

calc_df = pd.DataFrame(calc_results)

# ---- 출력값 표도 transpose ----
st.markdown("계산 결과 ($/ton-fuel, 행/열 전치)")
output_t_df = calc_df.set_index("Year").T
st.dataframe(output_t_df, use_container_width=True)

# ---- 그래프(그대로, 연도별 선 그래프) ----
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=calc_df["Year"], y=calc_df["Tier1 Cost"], mode="lines+markers", name="Tier1 Cost"
))
fig.add_trace(go.Scatter(
    x=calc_df["Year"], y=calc_df["Tier2 Cost"], mode="lines+markers", name="Tier2 Cost"
))
fig.add_trace(go.Scatter(
    x=calc_df["Year"], y=calc_df["Total Cost"], mode="lines+markers", name="Total Cost"
))
fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Cost ($/ton-fuel)",
    legend=dict(x=0, y=1.1, orientation="h")
)
st.plotly_chart(fig, use_container_width=True)
