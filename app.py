import os
from typing import Optional

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import requests

load_dotenv()


class DataAnalystAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoints = [
            ("GitHub Models", "https://models.inference.ai.azure.com/chat/completions"),
            ("OpenAI", "https://api.openai.com/v1/chat/completions"),
        ]

    def load_csv(self, uploaded_file) -> Optional[pd.DataFrame]:
        try:
            uploaded_file.seek(0)
            raw_bytes = uploaded_file.read()
            uploaded_file.seek(0)

            for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                try:
                    text = raw_bytes.decode(encoding)
                    df = pd.read_csv(pd.io.common.StringIO(text))
                    return df
                except UnicodeDecodeError:
                    continue

            df = pd.read_csv(uploaded_file, encoding="utf-8", engine="python", on_bad_lines="skip")
            return df
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")
            return None

    def get_profile(self, df: pd.DataFrame) -> str:
        summary = []
        summary.append(f"Rows: {len(df)}")
        summary.append(f"Columns: {list(df.columns)}")
        for col in df.columns:
            dtype = str(df[col].dtype)
            missing = int(df[col].isna().sum())
            summary.append(f"- {col}: {dtype}, missing={missing}")
        return "\n".join(summary)

    def generate_insights(self, df: pd.DataFrame, business_case: str) -> str:
        if not self.api_key:
            return "Please provide a GitHub Copilot/OpenAI API token to continue."

        if df is None or df.empty:
            return "The uploaded file is empty or could not be parsed."

        profile = self.get_profile(df)
        sample = df.head(10).to_string(index=False)

        prompt = (
            "You are an expert data analyst. Analyze this dataset and produce a concise executive summary.\n\n"
            f"Business case:\n{business_case}\n\n"
            f"Dataset profile:\n{profile}\n\n"
            f"Data sample:\n{sample}\n\n"
            "Return:\n"
            "1. Executive summary\n"
            "2. Key findings\n"
            "3. Recommended actions\n"
            "4. Risks or caveats\n"
        )

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a helpful data analyst."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 700,
        }

        last_error = None
        for name, url in self.endpoints:
            headers = {
                "Content-Type": "application/json",
            }
            if name == "GitHub Models":
                headers["Authorization"] = f"Bearer {self.api_key}"
                headers["X-GitHub-Api-Version"] = "2024-05-01"
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"

            try:
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except requests.RequestException as exc:
                last_error = exc

        return f"Analysis failed: {last_error}"

    def create_visualizations(self, df: pd.DataFrame):
        charts = []
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = [col for col in df.columns if col not in numeric_cols and df[col].nunique() <= 20]

        if numeric_cols:
            summary_df = pd.DataFrame(
                {
                    "column": numeric_cols,
                    "mean": [df[col].mean(skipna=True) for col in numeric_cols],
                }
            )
            chart = (
                alt.Chart(summary_df)
                .mark_bar()
                .encode(
                    x=alt.X("column:N", title="Column"),
                    y=alt.Y("mean:Q", title="Average value"),
                    color=alt.Color("column:N", legend=None),
                )
                .properties(title="Numeric column summary")
            )
            charts.append(chart)

        if len(numeric_cols) >= 2:
            scatter_df = df[numeric_cols[:2]].dropna()
            if not scatter_df.empty:
                chart = (
                    alt.Chart(scatter_df)
                    .mark_circle(size=80)
                    .encode(
                        x=alt.X(f"{numeric_cols[0]}:Q", title=numeric_cols[0]),
                        y=alt.Y(f"{numeric_cols[1]}:Q", title=numeric_cols[1]),
                        tooltip=list(scatter_df.columns),
                    )
                    .properties(title=f"{numeric_cols[0]} vs {numeric_cols[1]}")
                )
                charts.append(chart)

        if numeric_cols and categorical_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            grouped_df = df[[cat_col, num_col]].dropna().groupby(cat_col, as_index=False)[num_col].mean()
            chart = (
                alt.Chart(grouped_df)
                .mark_bar()
                .encode(
                    x=alt.X(f"{cat_col}:N", title=cat_col),
                    y=alt.Y(f"{num_col}:Q", title=f"Average {num_col}"),
                    color=alt.Color(f"{cat_col}:N", legend=None),
                )
                .properties(title=f"Average {num_col} by {cat_col}")
            )
            charts.append(chart)

        return charts


def run_app():
    st.set_page_config(page_title="Data Analyst Agent", page_icon="📊", layout="wide")
    st.title("📊 Local Data Analyst Agent")
    st.caption("Upload a CSV, describe your business case, and generate a business-friendly analysis.")

    env_api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY", "")

    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("GitHub Copilot / OpenAI API token", type="password", value=env_api_key)
        st.info("For local use, enter your token or set GITHUB_TOKEN (or OPENAI_API_KEY) in a .env file.")

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    business_case = st.text_area(
        "Business case",
        height=120,
        placeholder="Example: Identify the top drivers of churn for our subscription customers.",
    )

    if st.button("Analyze dataset", type="primary"):
        if not uploaded_file:
            st.warning("Please upload a CSV file first.")
            return
        if not business_case.strip():
            st.warning("Please describe the business case.")
            return

        with st.spinner("Analyzing the dataset..."):
            agent = DataAnalystAgent(api_key)
            df = agent.load_csv(uploaded_file)
            if df is None:
                return

            insights = agent.generate_insights(df, business_case)
            st.subheader("Analysis results")
            st.write(insights)

            charts = agent.create_visualizations(df)
            if charts:
                st.subheader("Visual insights")
                for chart in charts:
                    st.altair_chart(chart, use_container_width=True)

            st.subheader("Dataset preview")
            st.dataframe(df.head(20), width="stretch")

            st.subheader("Quick stats")
            col1, col2, col3 = st.columns(3)
            col1.metric("Rows", len(df))
            col2.metric("Columns", len(df.columns))
            col3.metric("Missing values", int(df.isna().sum().sum()))


if __name__ == "__main__":
    run_app()
