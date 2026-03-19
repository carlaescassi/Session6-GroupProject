import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random

st.set_page_config(page_title="A/B Chart App", page_icon="📊")

st.title("📊 A/B Chart App")

@st.cache_data
def load_data(file):
    return pd.read_csv(file)

# Default dataset + upload option
uploaded_file = st.sidebar.file_uploader("Upload another CSV file", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.sidebar.success("Custom dataset loaded.")
else:
    df = load_data("titanic.csv")
    st.sidebar.info("Using default dataset: titanic.csv")

# Detect columns
categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

for col in numeric_cols:
    if df[col].nunique() <= 10 and col not in categorical_cols:
        categorical_cols.append(col)

binary_cols = []
for col in df.columns:
    if df[col].dropna().nunique() == 2:
        binary_cols.append(col)

if not categorical_cols or not binary_cols:
    st.error("The dataset needs at least one categorical column and one binary column.")
    st.stop()

# Remove bad grouping variables
excluded_group_cols = ["Survived", "Ticket", "Cabin", "Name"]
categorical_cols = [col for col in categorical_cols if col not in excluded_group_cols]

if not categorical_cols:
    st.error("No suitable grouping columns found.")
    st.stop()

# Defaults
default_a = "Sex" if "Sex" in categorical_cols else categorical_cols[0]
default_b = "Pclass" if "Pclass" in categorical_cols else categorical_cols[min(1, len(categorical_cols) - 1)]
default_target = "Survived" if "Survived" in binary_cols else binary_cols[0]

# Sidebar settings
st.sidebar.header("Settings")

palette = st.sidebar.selectbox(
    "Choose a color palette",
    ["deep", "dark", "pastel", "muted", "colorblind"]
)

question = st.text_input(
    "Business question",
    "Which passenger group had the highest survival rate?"
)

chart_a_col = st.sidebar.selectbox(
    "Chart A variable",
    categorical_cols,
    index=categorical_cols.index(default_a)
)

chart_b_options = [col for col in categorical_cols if col != chart_a_col]
if not chart_b_options:
    chart_b_options = categorical_cols

chart_b_col = st.sidebar.selectbox(
    "Chart B variable",
    chart_b_options,
    index=chart_b_options.index(default_b) if default_b in chart_b_options else 0
)

target_col = st.sidebar.selectbox(
    "Target variable",
    binary_cols,
    index=binary_cols.index(default_target)
)

# Session state
if "chart_shown" not in st.session_state:
    st.session_state.chart_shown = None

if "results" not in st.session_state:
    st.session_state.results = []

# Main question
st.subheader("Business Question")
st.write(question)

# Helpers
def prepare_data(dataframe, group_col, target_col):
    temp = dataframe[[group_col, target_col]].dropna().copy()
    temp[target_col] = pd.to_numeric(temp[target_col], errors="coerce")
    temp = temp.dropna()

    result = (
        temp.groupby(group_col)[target_col]
        .mean()
        .reset_index()
        .sort_values(by=target_col, ascending=False)
    )
    return result

def show_bar_chart(dataframe, group_col, target_col, title):
    plot_df = prepare_data(dataframe, group_col, target_col)

    fig, ax = plt.subplots()
    sns.barplot(
        data=plot_df,
        x=group_col,
        y=target_col,
        hue=group_col,
        palette=palette,
        legend=False,
        ax=ax
    )
    ax.set_title(title)
    ax.set_ylabel(f"Average {target_col}")
    ax.set_xlabel(group_col)
    plt.xticks(rotation=20)
    st.pyplot(fig)

    st.write("Top category:", plot_df.iloc[0][group_col])

def show_point_chart(dataframe, group_col, target_col, title):
    plot_df = prepare_data(dataframe, group_col, target_col)

    fig, ax = plt.subplots()
    sns.pointplot(
        data=plot_df,
        x=group_col,
        y=target_col,
        palette=palette,
        ax=ax
    )
    ax.set_title(title)
    ax.set_ylabel(f"Average {target_col}")
    ax.set_xlabel(group_col)
    plt.xticks(rotation=20)
    st.pyplot(fig)

    st.write("Top category:", plot_df.iloc[0][group_col])

# Buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("Show random chart"):
        st.session_state.chart_shown = random.choice(["A", "B"])

with col2:
    if st.button("Reset"):
        st.session_state.chart_shown = None

# Show chart
if st.session_state.chart_shown == "A":
    st.success("Chart A selected")
    show_bar_chart(df, chart_a_col, target_col, f"Chart A: {target_col} by {chart_a_col}")

elif st.session_state.chart_shown == "B":
    st.success("Chart B selected")
    show_point_chart(df, chart_b_col, target_col, f"Chart B: {target_col} by {chart_b_col}")

# Answer buttons
if st.session_state.chart_shown is not None:
    st.write("### Did I answer your question?")

    yes_col, no_col = st.columns(2)

    with yes_col:
        if st.button("Yes"):
            st.session_state.results.append({
                "chart": st.session_state.chart_shown,
                "answer": "Yes"
            })
            st.success("Great!")
            st.balloons()

    with no_col:
        if st.button("No"):
            st.session_state.results.append({
                "chart": st.session_state.chart_shown,
                "answer": "No"
            })
            st.warning("Thanks for the feedback!")

# Extra sections
with st.expander("See results"):
    if st.session_state.results:
        results_df = pd.DataFrame(st.session_state.results)
        st.dataframe(results_df)

with st.expander("See dataset preview"):
    st.dataframe(df.head())