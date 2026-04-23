"""
frontend/streamlit_app.py
Streamlit UI для предсказания качества воздуха в Алматы.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Almaty Air Quality",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;600;700&family=JetBrains+Mono:wght@300;400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
    background-color: #080c14;
    color: #c8d6e5;
}
h1, h2, h3 { font-family: 'Rajdhani', sans-serif; letter-spacing: 0.05em; }

/* Header */
.header {
    background: linear-gradient(135deg, #080c14 0%, #0d1b2a 60%, #0a1628 100%);
    border-bottom: 1px solid #1a2a3a;
    padding: 1.5rem 2rem;
    margin: -1rem -1rem 2rem -1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.header-title { font-size: 1.8rem; font-weight: 700; color: #e2f0ff; margin: 0; }
.header-sub   { font-size: 0.9rem; color: #4a6a8a; font-family: 'JetBrains Mono'; margin: 0; }

/* AQI Big indicator */
.aqi-card {
    background: #0d1b2a;
    border: 1px solid #1a2a3a;
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.aqi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--aqi-color, #00e400);
}
.aqi-number {
    font-size: 5rem;
    font-weight: 700;
    line-height: 1;
    font-family: 'JetBrains Mono';
    color: var(--aqi-color, #00e400);
    text-shadow: 0 0 40px var(--aqi-color, #00e400);
}
.aqi-label  { font-size: 1.3rem; font-weight: 600; color: #e2f0ff; margin-top: 0.5rem; }
.aqi-advice { font-size: 0.9rem; color: #4a6a8a; margin-top: 0.5rem; }

/* Metric cards */
.metric-row { display: flex; gap: 1rem; margin-top: 1rem; }
.metric-card {
    flex: 1;
    background: #0d1b2a;
    border: 1px solid #1a2a3a;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}
.metric-val  { font-size: 1.6rem; font-weight: 700; color: #5ba3f5; font-family: 'JetBrains Mono'; }
.metric-name { font-size: 0.8rem; color: #4a6a8a; margin-top: 0.2rem; }

/* Predict form */
.predict-card {
    background: #0d1b2a;
    border: 1px solid #1a2a3a;
    border-radius: 16px;
    padding: 1.5rem;
}

/* Status */
.status-ok  { color: #00e400; font-weight: 600; font-size: 0.85rem; }
.status-err { color: #ff4444; font-weight: 600; font-size: 0.85rem; }

/* AQI scale */
.scale-bar {
    height: 8px;
    border-radius: 4px;
    background: linear-gradient(to right, #00e400, #ffff00, #ff7e00, #ff0000, #8f3f97, #7e0023);
    margin: 0.5rem 0;
    position: relative;
}
.scale-labels { display: flex; justify-content: space-between; font-size: 0.7rem; color: #4a6a8a; font-family: 'JetBrains Mono'; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header">
    <div>
        <p class="header-title">🌫️ ALMATY AIR QUALITY</p>
        <p class="header-sub">ML-powered forecast · PM2.5 · PM10 · AQI</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── API status ────────────────────────────────────────────────────────────────
try:
    r = requests.get(f"{API_URL}/", timeout=3)
    api_ok = r.status_code == 200
except Exception:
    api_ok = False

if not api_ok:
    st.error("❌ API недоступен. Убедитесь что FastAPI запущен на порту 8000.")
    st.stop()

# ── Load current data ─────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_current():
    return requests.get(f"{API_URL}/current", timeout=5).json()

@st.cache_data(ttl=60)
def get_history():
    return requests.get(f"{API_URL}/history", timeout=5).json()

current = get_current()
history = get_history()

aqi     = current["aqi"]
color   = current["color"]
cat     = current["category"]
advice  = current["advice"]
pm25    = current["pm25"]
pm10    = current["pm10"]
temp    = current["temperature"]
hum     = current["humidity"]

# ── Layout ────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 2], gap="large")

# ── Left: AQI Indicator + metrics ─────────────────────────────────────────────
with col_left:
    st.markdown(f"""
    <div class="aqi-card" style="--aqi-color: {color}">
        <div style="font-size:0.8rem;color:#4a6a8a;font-family:'JetBrains Mono';margin-bottom:0.5rem">
            ТЕКУЩИЙ AQI · {datetime.now().strftime('%H:%M')}
        </div>
        <div class="aqi-number">{aqi}</div>
        <div class="aqi-label">{cat}</div>
        <div class="aqi-advice">{advice}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:1rem">
        <div style="font-size:0.75rem;color:#4a6a8a;font-family:'JetBrains Mono';margin-bottom:0.3rem">ШКАЛА AQI</div>
        <div class="scale-bar"></div>
        <div class="scale-labels">
            <span>0</span><span>50</span><span>100</span><span>150</span><span>200</span><span>300+</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-val">{pm25}</div>
            <div class="metric-name">PM2.5 μg/m³</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">{pm10}</div>
            <div class="metric-name">PM10 μg/m³</div>
        </div>
    </div>
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-val">{temp}°</div>
            <div class="metric-name">Температура</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">{hum}%</div>
            <div class="metric-name">Влажность</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Right: Graph + Predict ─────────────────────────────────────────────────────
with col_right:
    # AQI по времени
    st.markdown("#### 📈 AQI за последние 24 часа")

    df = pd.DataFrame({
        "time": history["labels"],
        "aqi":  history["aqi_values"],
        "pm25": history["pm25_values"],
    })

    fig = go.Figure()

    # Фоновые зоны
    for y0, y1, fill_color in [
        (0, 50, "rgba(0,228,0,0.05)"),
        (50, 100, "rgba(255,255,0,0.05)"),
        (100, 150, "rgba(255,126,0,0.05)"),
        (150, 250, "rgba(255,0,0,0.05)"),
    ]:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=fill_color, line_width=0)

    fig.add_trace(go.Scatter(
        x=df["time"], y=df["aqi"],
        mode="lines",
        name="AQI",
        line=dict(color="#5ba3f5", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(91,163,245,0.08)",
    ))

    fig.update_layout(
        plot_bgcolor="#080c14",
        paper_bgcolor="#0d1b2a",
        font=dict(color="#c8d6e5", family="JetBrains Mono"),
        xaxis=dict(gridcolor="#1a2a3a", tickangle=-45),
        yaxis=dict(gridcolor="#1a2a3a", range=[0, max(df["aqi"]) + 30]),
        margin=dict(t=10, b=10, l=10, r=10),
        height=260,
        showlegend=False,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Predict form ──────────────────────────────────────────────────────────
    st.markdown("#### 🔮 Прогноз на дату и время")

    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            pred_date = st.date_input(
                "Дата",
                value=datetime.now().date(),
                min_value=datetime.now().date(),
                max_value=(datetime.now() + timedelta(days=7)).date(),
            )
        with c2:
            pred_hour = st.slider("Час", 0, 23, datetime.now().hour)

        pred_btn = st.button("🔮 Получить прогноз", use_container_width=True, type="primary")

        if pred_btn:
            dt_str = f"{pred_date} {pred_hour:02d}:00"
            try:
                resp = requests.post(
                    f"{API_URL}/predict",
                    json={"datetime_str": dt_str},
                    timeout=5,
                ).json()

                p_aqi   = resp["aqi"]
                p_color = resp["color"]
                p_cat   = resp["category"]
                p_adv   = resp["advice"]

                st.markdown(f"""
                <div class="aqi-card" style="--aqi-color:{p_color};margin-top:1rem">
                    <div style="font-size:0.75rem;color:#4a6a8a;font-family:'JetBrains Mono'">
                        ПРОГНОЗ · {dt_str}
                    </div>
                    <div class="aqi-number" style="font-size:3rem">{p_aqi}</div>
                    <div class="aqi-label">{p_cat}</div>
                    <div class="aqi-advice">{p_adv}</div>
                </div>
                """, unsafe_allow_html=True)

                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    st.metric("PM2.5", f"{resp['pm25']} μg/m³")
                with mc2:
                    st.metric("PM10", f"{resp['pm10']} μg/m³")
                with mc3:
                    st.metric("Влажность", f"{resp['humidity']}%")

            except Exception as e:
                st.error(f"Ошибка: {e}")