import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx

from src.mda_loader import load_mda_files
from src.sec_scraper import scrape_and_save_mdas
from src.sentiment import compute_sentiment_by_year
from src.llm_graph import generate_graph_data
from src.graph_builder import build_networkx_graph


# --- PAGE CONFIG ---
st.set_page_config(
    page_title="10-K MD&A Knowledge Graph",
    layout="wide"
)

st.markdown("""
<div style="
    text-align: center;
    padding: 30px;
    border-radius: 14px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    margin-bottom: 25px;
">
    <h1 style='font-size: 44px; margin-bottom: 5px;'>
        <span style='color: #111827;'>MDA</span>
        <span style='color: #2563eb;'>Brief</span>
    </h1>
    <p style='color: #6b7280; font-size: 16px;'>
        AI-powered analysis of 10-K narratives
    </p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Company Selection")

    ticker = st.text_input("Ticker", placeholder="AAPL, MSFT, NVDA")

    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Your key is used only for this session."
    )

    generate_graph = st.button("Generate Knowledge Graph")


# --- MAIN LOGIC ---
if ticker:
    ticker = ticker.upper()

    with st.spinner(f"Loading MD&A filings for {ticker}..."):
        try:
            records = load_mda_files(ticker)
            st.success(f"Loaded {len(records)} existing MD&A filings for {ticker}")

        except FileNotFoundError:
            st.warning(f"No saved MD&A files found for {ticker}. Scraping now...")

            scrape_results = scrape_and_save_mdas(ticker)

            if len(scrape_results) == 0:
                st.error(f"No MD&A sections were scraped for {ticker}.")
                st.stop()

            records = load_mda_files(ticker)
            st.success(f"Scraped and loaded {len(records)} MD&A filings for {ticker}")

        except ValueError:
            st.error(f"Folder exists for {ticker}, but no .txt files were found.")
            st.stop()

    # --- SUMMARY METRICS ---
    years = sorted([record["year"] for record in records])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Ticker", ticker)

    with col2:
        st.metric("Filings Loaded", len(records))

    with col3:
        st.metric("Year Range", f"{min(years)} – {max(years)}")

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs([
        "Overview",
        "Sentiment",
        "Knowledge Graph"
    ])

    # --- TAB 1: OVERVIEW ---
    with tab1:
        st.subheader("Available Filings")

        years = sorted([r["year"] for r in records])

        selected_year = st.radio(
            "Years",
            years,
            horizontal=True
        )

        selected_record = next(
            record for record in records
            if record["year"] == selected_year
        )

        st.subheader(f"MD&A Text ({selected_year})")

        st.text_area(
            "MD&A Content",
            selected_record["text"],
            height=400
        )    

    # --- TAB 2: SENTIMENT ---
    with tab2:
        st.subheader("Sentiment by Year")

        sentiment_results = compute_sentiment_by_year(records)

        st.dataframe(sentiment_results, use_container_width=True)

        # Simple line chart
        years = [r["year"] for r in sentiment_results]
        scores = [r["sentiment"] for r in sentiment_results]

        fig, ax = plt.subplots()
        ax.plot(years, scores, marker='o')
        ax.set_title("Sentiment Trend")
        ax.set_xlabel("Year")
        ax.set_ylabel("Sentiment Score")

        st.pyplot(fig)

    # --- TAB 3: KNOWLEDGE GRAPH ---
    with tab3:
        st.subheader("Knowledge Graph")

        selected_year = st.selectbox(
            "Select filing year",
            years
        )

        selected_record = next(
            record for record in records
            if record["year"] == selected_year
        )

        if generate_graph:
            if not openai_api_key:
                st.error("Please enter your OpenAI API key in the sidebar.")
                st.stop()
            
            
            with st.spinner("Generating knowledge graph..."):
                graph_data = generate_graph_data(selected_record, openai_api_key)
                G = build_networkx_graph(graph_data)

            st.success("Knowledge graph generated")

            fig, ax = plt.subplots(figsize=(12, 9))

            pos = nx.spring_layout(G, seed=42, k=1.2)

            nx.draw(
                G,
                pos,
                ax=ax,
                with_labels=True,
                node_size=2500,
                node_color="lightblue",
                font_size=8,
                arrows=True,
                arrowsize=15
            )

            edge_labels = nx.get_edge_attributes(G, "relationship")

            nx.draw_networkx_edge_labels(
                G,
                pos,
                edge_labels=edge_labels,
                font_size=7,
                label_pos=0.5,
                ax=ax
            )

            ax.set_title(f"{ticker} {selected_year} MD&A Knowledge Graph")
            ax.axis("off")

            st.pyplot(fig)