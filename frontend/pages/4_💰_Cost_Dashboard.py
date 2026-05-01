"""Cost dashboard — show OpenAI API spend."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import sqlite3
import streamlit as st
import pandas as pd
st.set_page_config(page_title="Cost Dashboard", page_icon="💰", layout="wide")
st.title("💰 Cost Dashboard")
st.caption("Track every OpenAI API call and what it cost you.")
DB_PATH = os.getenv("APP_DB_PATH", "data/app.db")
if not os.path.exists(DB_PATH):
    st.error(f"Database not found at `{DB_PATH}`.")
    st.stop()
conn = sqlite3.connect(DB_PATH)
try:
    df = pd.read_sql_query(
        """
        SELECT id, user_id, post_id, model, operation,
               tokens_input, tokens_output, cost_usd, created_at
        FROM token_usage
        ORDER BY created_at DESC
        """,
        conn,
    )
finally:
    conn.close()
if df.empty:
    st.info("No API calls recorded yet. Generate a post to see data here.")
    st.stop()
total_cost = df["cost_usd"].sum()
total_calls = len(df)
total_tokens_in = df["tokens_input"].sum()
total_tokens_out = df["tokens_output"].sum()
BUDGET = 6.00
remaining = BUDGET - total_cost
percent_used = (total_cost / BUDGET) * 100
col1, col2, col3, col4 = st.columns(4)
col1.metric("💸 Total Spent", f"${total_cost:.4f}")
col2.metric("📞 API Calls", f"{total_calls:,}")
col3.metric("🔤 Tokens In", f"{int(total_tokens_in):,}")
col4.metric("✍️ Tokens Out", f"{int(total_tokens_out):,}")
st.divider()
st.subheader("📊 $6 Budget Tracker")
st.progress(min(percent_used / 100, 1.0))
st.caption(f"Used: **${total_cost:.4f}** of **${BUDGET:.2f}** "
           f"({percent_used:.2f}%) — Remaining: **${remaining:.4f}**")
if percent_used > 80:
    st.warning("⚠️ You've used over 80% of your budget!")
elif percent_used > 50:
    st.info("💡 You're past halfway.")
else:
    st.success(f"💚 Plenty of budget left.")
st.divider()
st.subheader("🔍 By Operation")
by_op = (
    df.groupby("operation")
    .agg(
        calls=("id", "count"),
        total_cost=("cost_usd", "sum"),
        total_tokens=("tokens_input", lambda x: x.sum() + df.loc[x.index, "tokens_output"].sum()),
    )
    .sort_values("total_cost", ascending=False)
    .reset_index()
)
by_op["total_cost"] = by_op["total_cost"].round(6)
st.dataframe(by_op, use_container_width=True, hide_index=True)
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("🤖 By Model")
    by_model = (
        df.groupby("model")
        .agg(calls=("id", "count"), cost=("cost_usd", "sum"))
        .sort_values("cost", ascending=False)
        .reset_index()
    )
    by_model["cost"] = by_model["cost"].round(6)
    st.dataframe(by_model, use_container_width=True, hide_index=True)
with col_b:
    st.subheader("📅 Recent Activity")
    df["created_at"] = pd.to_datetime(df["created_at"])
    recent = df.head(20)[["created_at", "operation", "model", "cost_usd"]]
    recent["created_at"] = recent["created_at"].dt.strftime("%m/%d %H:%M")
    recent["cost_usd"] = recent["cost_usd"].apply(lambda x: f"${x:.6f}")
    st.dataframe(recent, use_container_width=True, hide_index=True)
st.divider()
st.subheader("📝 Cost Per Post")
post_costs = (
    df[df["post_id"].notna()]
    .groupby("post_id")
    .agg(
        api_calls=("id", "count"),
        total_cost=("cost_usd", "sum"),
        operations=("operation", lambda x: ", ".join(sorted(set(x)))),
    )
    .sort_values("total_cost", ascending=False)
    .reset_index()
)
post_costs["total_cost"] = post_costs["total_cost"].round(6)
post_costs["post_id"] = post_costs["post_id"].astype(int)
st.dataframe(post_costs.head(20), use_container_width=True, hide_index=True)
with st.expander("🗄️ Raw token_usage table"):
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "📥 Download CSV", df.to_csv(index=False),
        file_name="token_usage.csv", mime="text/csv",
    )