import streamlit as st
import requests

st.set_page_config(page_title="Heritage Lens", page_icon="🪔")

st.title("🪔 Heritage Lens - AI-Powered Cultural Explorer")
st.markdown("""
Welcome! Enter a description below to explore cultural artifacts using AI-powered semantic search.
""")

col1, col2 = st.columns([4,1])
with col1:
    query = st.text_input("🔎 Describe an artifact, theme, or cultural region:")
with col2:
    k = st.slider("Results", 1, 10, 3, help="Number of matches to show")

if st.button("Search") and query:
    with st.spinner("🔍 Searching... please wait"):
        try:
            api_url = st.secrets.get("API_URL", "http://localhost:8000/api/explorer/search")
            response = requests.post(api_url, json={"query": query, "k": k}, timeout=15)
            data = response.json()
            if response.status_code == 200 and data.get("results"):
                for idx, item in enumerate(data["results"], 1):
                    st.markdown(f"### {idx}. {item.get('title', 'Untitled')}")
                    cols = st.columns([2, 4])
                    with cols[0]:
                        if item.get("image_url"):
                            st.image(item["image_url"], use_container_width=True)
                    with cols[1]:
                        st.markdown(f"""
- **Region:** `{item.get('region','-')}`
- **Period:** `{item.get('period','-')}`
- **Themes:** `{', '.join(item.get('themes', [])) or '-'}`
""")
                        st.write(item.get("description", "_No description available._"))
                    st.markdown("---")
            else:
                no_result_message = """
                <div style="background-color:#262626; padding: 1.5rem; border-radius: 10px;">
                    <h3 style="color:#FFD700;">😕 No results found!</h3>
                    <p style="color:#FFF;">
                        We couldn't find any matching artifacts.<br>
                        <strong>Tips:</strong>
                        <ul>
                            <li>Try a broader or different description (e.g., <em>“ancient bronze statue”</em>)</li>
                            <li>Use fewer keywords or try searching by region or period</li>
                            <li>Check your spelling</li>
                        </ul>
                        <span style="color:#FFD700;">Example searches:</span>
                        <ul>
                            <li>Terracotta Army in China</li>
                            <li>Buddhist sculpture</li>
                            <li>Roman mosaic art</li>
                        </ul>
                    </p>
                </div>
                """
                st.markdown(no_result_message, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("""
---
**Powered by** MongoDB Atlas & Google Cloud  
Made with ❤️ by Mayur Pawar
""")
