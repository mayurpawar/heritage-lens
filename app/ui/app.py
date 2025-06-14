import streamlit as st
import pandas as pd
import requests
import json
import os

# ---- Config and Layout ----

st.set_page_config(
    page_title="Heritage Lens",
    page_icon="assets/favicon.png",   # Your favicon
    layout="wide"
)
st.markdown(
    """
<style>
/* Label (bold text like "Region", "Period") */
ul li strong {
    color: #000000 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Info next to the label (text after "Region:", etc.) */
ul li {
    color: #333333 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background: none !important;
}

/* Remove any background or border Streamlit might add */
ul {
    background: none !important;
    padding: 0.4rem 0.8rem;
    border: none !important;
    margin-left: 1.1rem;
}

/* Shine effect for image */
.image-container {position:relative; overflow:hidden;}
.image-container:hover::after {
    content:''; position:absolute; top:0; left:-150%;
    width:50%; height:100%;
    background:rgba(255,255,255,0.2);
    transform:skewX(-20deg);
    animation:shine 0.8s forwards;
}
@keyframes shine {from{left:-150%;} to{left:150%;}}

/* Reference link button */
.ref-btn {
    display: inline-block;
    margin: 0.5rem 0 0 0;
    padding: 0.28rem 0.9rem;
    background: transparent;
    border: 1px solid #ffb263;
    color: #824b14 !important;
    border-radius: 0.3rem;
    text-decoration: none !important;
    font-weight: 600;
    font-family: inherit;
    transition: border 0.2s, color 0.2s;
}
.ref-btn:hover {
    border-color: #FF6F61;
    color: #FF6F61 !important;
    background: #fff7ef;
    text-decoration: none !important;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("""
    <style>
        /* Hide the entire Streamlit default header */
        header[data-testid="stHeader"] {
            display: none;
        }
        /* Optional: reduce top padding caused by hidden header */
        .block-container {
            padding-top: 1.5rem !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .custom-banner-content {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 1.5rem;
        height: 60px;
        font-size: 1.12rem;
        font-weight: 500;
        color: #824b14;
        letter-spacing: 0.01em;
        background: linear-gradient(90deg, #fbeee6 0%, #ffe3ca 100%);
        box-shadow: 0 2px 8px rgba(150,112,45,0.04);
        border-bottom: 1px solid #e8b470;
        z-index: 1000;
    }
    .custom-banner-logo {
        height: 32px;
        margin-right: 0.6rem;
        margin-left: 0.1rem;
        filter: drop-shadow(0 1px 6px #f3d6a2aa);
        border-radius: 8px;
        background: #fff8f3;
        padding: 2px 5px;
    }
    .custom-banner-title {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .custom-banner-main {
        font-weight: 700;
        font-size: 1.16rem;
        margin-right: 0.4rem;
    }
    .custom-banner-tagline {
        font-size: 1.01rem;
        font-weight: 400;
        color: #a2732e;
        letter-spacing: 0.02em;
        margin-left: 0.4rem;
    }
    .emoji-spin {
        display: inline-block;
        animation: spin 1.2s linear infinite;
        font-size: 1em;
        vertical-align: left;
    }
    @keyframes spin {
    100% { transform: rotate(1turn);}
    }
    .emoji-glow {
        display: inline-block;
        animation: glow 1.2s infinite alternate;
        font-size: 1.2em;
        vertical-align: middle;
        filter: drop-shadow(0 0 4px #ff3939) drop-shadow(0 0 12px #ffa914);
    }
    @keyframes glow {
    from {
        filter: drop-shadow(0 0 4px #ff3939) drop-shadow(0 0 12px #ffa914);
    }
    to {
        filter: drop-shadow(0 0 18px #ffa914) drop-shadow(0 0 30px #ffa914);
    }
}

    /* Add top margin to body content so it isn't hidden */
    .block-container {
        margin-top: 68px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="custom-banner-content">
        <div class="custom-banner-title">
            <img src="/assets/logo-small.png" class="custom-banner-logo" alt="Logo">
            <span class="custom-banner-main">Heritage Lens</span>
            <span class="custom-banner-tagline">AI-Powered Cultural Explorer</span>
        </div>
        <div style="font-size:0.97rem; color:#824b14;">
            🌟 Celebrating Cultural Treasures from Around the World 🌎 &nbsp; | &nbsp; 🔍 Search Millions of Artifacts
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ---- Main App Content ----

logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets/logo.png"))

# Logo and Title Row
col_logo, col_title = st.columns([2, 7])
with col_logo:
    st.image(logo_path, width=300)


# Tagline below both (centered, styled, with top margin)
st.markdown(
    """
    <div style='text-align:center; margin-top: 14px; margin-bottom: 10px; font-size:2.5rem; font-weight:900; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color:#2d2d2d; letter-spacing:0.01em;'>
        AI-Powered Cultural Explorer
    </div>
    """, unsafe_allow_html=True
)

# Spacer before welcome line
st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

# Welcome message (centered)
st.markdown(
    """
    <div style='display: flex; justify-content: center;'>
        <div style='text-align: center; max-width: 800px; color:#2d2d2d; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'>
            Welcome! Enter a description below to explore cultural artifacts using AI-powered semantic search.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- Style: Max width for main content area ---
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1100px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- App Logic ----

RESULTS_PER_PAGE = 10

if "results" not in st.session_state:
    st.session_state.results = []
if "page" not in st.session_state:
    st.session_state.page = 0
if "search_attempted" not in st.session_state:
    st.session_state.search_attempted = False

# Search bar and button
search_col, btn_col = st.columns([18, 2], gap="small")
query = search_col.text_input("🔎 Describe an artifact, theme, or cultural region:", label_visibility="collapsed")
search_clicked = btn_col.button("Search")

# Get results
results = st.session_state.get("results", [])
search_attempted = st.session_state.get("search_attempted", False)

# Info + Export buttons
info_col, export_col = st.columns([11, 6])  # Wide info, narrow export

count = len(results)  # assuming 'results' is a list

result_text = f"<span class='emoji-glow'> 🔍 </span> {count} result{'s' if count != 1 else ''} found!"


with info_col:
    if search_attempted:
        st.markdown(
            f"<div style='text-align:left; margin-left: 4px; font-size:1.2rem; font-weight:500; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif'>{result_text}</div>",
            unsafe_allow_html=True,
        )

with export_col:
    if results:
        df = pd.DataFrame(results)
        btn_csv, btn_json, btn_spacer = st.columns([6, 6, 1])
        with btn_spacer:
            pass  # This pushes both buttons to the right
        with btn_csv:
            st.download_button(
                label="📤 Export as CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="artifacts.csv",
                mime="text/csv",
                key="export_csv"
            )
        with btn_json:
            st.download_button(
                label="📦 Export as JSON",
                data=json.dumps(results, ensure_ascii=False, indent=2),
                file_name="artifacts.json",
                mime="application/json",
                key="export_json"
            )

if search_clicked and query:
    with st.spinner("🔍 Searching... please wait"):
        try:
            api_url = st.secrets.get(
                "API_URL", "http://localhost:8000/api/explorer/search"
            )
            response = requests.post(
                api_url, json={"query": query, "k": 50}, timeout=15
            )
            data = response.json()
            st.session_state.search_attempted = True
            if response.status_code == 200 and data.get("results"):
                st.session_state.results = data["results"]
                st.session_state.page = 0
                st.session_state.search_attempted = True
                st.rerun()
            else:
                st.session_state.results = []
                st.session_state.search_attempted = True
                st.warning("No results found!")
        except Exception as e:
            st.session_state.search_attempted = True
            st.error(f"Error: {e}")

results = st.session_state.get("results", [])
page = st.session_state.get("page", 0)

start = page * RESULTS_PER_PAGE
end = start + RESULTS_PER_PAGE

if results:
    for idx, item in enumerate(results[start:end], start + 1):
        st.markdown(
            f"<h3 style='font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif;'>{idx}. {item.get('title', 'Untitled')}</h3>",
                unsafe_allow_html=True
        )

        cols = st.columns([2, 4])
        with cols[0]:
            if item.get("image_url"):
                st.markdown(
                    f"<div class='image-container'><img src='{item['image_url']}' class='artifact-image'></div>",
                    unsafe_allow_html=True,
                )
        with cols[1]:

            st.markdown(
    f"""
- **Region:** {item.get('region', '-')}
- **Period:** {item.get('period', '-')}
- **Themes:** {', '.join(item.get('themes', [])) or '-'}
- **Description:** {item.get('description', '-')}
""",
    unsafe_allow_html=True
)

            if item.get("reference_link"):
                st.markdown(
                    f"""
                    <div style='display: flex; margin-left: 4rem; justify-content: flex-start;'>
                        <a href='{item['reference_link']}' target='_blank' class='ref-btn'>More Info</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
    )

        st.markdown("---")

    total_pages = (len(results) - 1) // RESULTS_PER_PAGE + 1
    col_prev, col_spacer, col_next = st.columns([3, 15, 2])
    with col_prev:
        if st.button("Previous", disabled=page == 0):
            st.session_state.page = max(page - 1, 0)
            st.rerun()
    with col_next:
        if st.button("Next", disabled=end >= len(results)):
            st.session_state.page = min(page + 1, total_pages - 1)
            st.rerun()

# ---- Footer ----
st.markdown(
    """
    <hr>
    <div style='text-align: right; margin-top: 0.6rem;'>
        Made with ❤️ by Mayur Pawar<br>
        <strong>Powered by</strong> MongoDB Atlas &amp; Google Cloud<br>
        <span style="font-size:0.98rem; color:#888;">
            Data and images sourced from 
            <a href="https://www.metmuseum.org/about-the-met/policies-and-documents/open-access" target="_blank" style="color:#824b14; text-decoration:underline;">The MET Museum Open Access</a>
            &amp; 
            <a href="https://www.si.edu/openaccess" target="_blank" style="color:#824b14; text-decoration:underline;">Smithsonian Open Access</a>.
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

