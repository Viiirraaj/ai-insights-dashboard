import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import google.generativeai as genai
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Insights Dashboard", layout="wide")
st.title("📊 AI Insights Dashboard (Decision Support)")

genai.configure(api_key="YOUR GEMINI API KEY")
model = genai.GenerativeModel("models/gemini-2.5-flash")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader(
    "Upload a CSV file (required columns: date, orders, revenue)",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Please upload a CSV file to start analysis.")
    st.stop()

df = pd.read_csv(uploaded_file)

required_cols = {"date", "orders", "revenue"}
if not required_cols.issubset(df.columns):
    st.error("CSV must contain columns: date, orders, revenue")
    st.stop()

df["date"] = pd.to_datetime(df["date"])

# ---------------- KPIs ----------------
st.subheader("📌 Key KPIs")

col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"₹{df['revenue'].sum():,.0f}")
col2.metric("Average Orders", f"{df['orders'].mean():.1f}")
col3.metric("Max Orders", int(df["orders"].max()))

# ---------------- CHARTS ----------------
st.subheader("📈 Trends")

col4, col5 = st.columns(2)

fig1, ax1 = plt.subplots()
ax1.plot(df["date"], df["orders"], marker="o")
ax1.set_title("Orders Trend")
ax1.tick_params(axis="x", rotation=45)
col4.pyplot(fig1)

fig2, ax2 = plt.subplots()
ax2.plot(df["date"], df["revenue"], marker="o")
ax2.set_title("Revenue Trend")
ax2.tick_params(axis="x", rotation=45)
col5.pyplot(fig2)

# ---------------- ANOMALY DETECTION ----------------
df["orders_z"] = (df["orders"] - df["orders"].mean()) / df["orders"].std()
df["revenue_z"] = (df["revenue"] - df["revenue"].mean()) / df["revenue"].std()

anomalies = df[
    (df["orders_z"].abs() > 2) |
    (df["revenue_z"].abs() > 2)
]

st.subheader("🚨 Alerts & Anomalies")

latest = df.iloc[-1]

if latest["orders"] < df["orders"].mean() * 0.7:
    st.error("⚠️ Sudden drop in orders detected")

if latest["revenue"] > df["revenue"].mean() * 1.5:
    st.warning("📈 Revenue spike detected")

if not anomalies.empty:
    st.subheader("⚠️ Detected Anomalies")
    st.dataframe(anomalies[["date", "orders", "revenue"]])
else:
    st.success("No major anomalies detected")

# ---------------- PROMPT FROM UI ----------------
st.subheader("✍️ AI Insight Prompt")

default_prompt = """
You are a business analyst.

Based on the given business metrics:
1. Highlight key insights
2. Explain possible reasons
3. Suggest actionable recommendations
"""

user_prompt = st.text_area(
    "Edit the prompt used to generate AI insights:",
    value=default_prompt,
    height=180
)

# ---------------- AI INSIGHTS ----------------
st.subheader("🤖 AI Insights")

analysis_text = f"""
Total Revenue: {df['revenue'].sum()}
Average Orders: {df['orders'].mean():.1f}
Average Revenue: {df['revenue'].mean():.1f}
Max Orders: {df['orders'].max()}
Min Orders: {df['orders'].min()}
Anomalies Detected: {len(anomalies)}
"""

final_prompt = f"""
{user_prompt}

Business Metrics:
{analysis_text}
"""

ai_output = None

if st.button("Generate AI Insights"):
    with st.spinner("Generating insights..."):
        response = model.generate_content(final_prompt)
        ai_output = response.text
        st.text(ai_output)

# ---------------- EXPORT PDF ----------------
if ai_output:
    st.subheader("📄 Export Insights")

    def generate_pdf(text):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()
        story = []

        for line in text.split("\n"):
            story.append(Paragraph(line, styles["Normal"]))

        doc.build(story)
        buffer.seek(0)
        return buffer

    pdf_file = generate_pdf(ai_output)

    st.download_button(
        label="⬇️ Download Insights as PDF",
        data=pdf_file,
        file_name="ai_insights_report.pdf",
        mime="application/pdf"
    )
