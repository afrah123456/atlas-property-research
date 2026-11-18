from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from src.chat import ChatError, answer_question
from src.corpus import ROOT, load_documents
from src.retrieval import Retriever

load_dotenv(ROOT / ".env")
st.set_page_config(page_title="Atlas | Property research", page_icon="◈", layout="wide")
st.markdown("""<style>
#MainMenu, footer {visibility:hidden;}
.block-container {max-width:1120px;padding-top:2.4rem;padding-bottom:3rem;}
[data-testid="stSidebar"] {border-right:1px solid #dce5ef;}
.atlas-label {color:#176b5b;font-size:.9rem;font-weight:700;letter-spacing:.13em;}
.atlas-title {font-size:clamp(2.2rem,5vw,3.5rem);font-weight:650;line-height:1.1;letter-spacing:-.045em;margin:.6rem 0 1rem;color:#142b45;}
.atlas-intro {font-size:1.08rem;color:#52657a;line-height:1.7;max-width:720px;}
.atlas-note {font-size:.9rem;color:#52657a;border-top:1px solid #dce5ef;padding-top:1rem;margin-top:1rem;}
[data-testid="stChatMessage"] {border:1px solid #dce5ef;border-radius:16px;background:white;}
[data-testid="stChatInput"] {border-radius:16px;}
div.stButton>button {border-radius:10px;min-height:2.8rem;}
</style>""", unsafe_allow_html=True)


@st.cache_data
def documents(dataset_mtime: float):
    return load_documents()


@st.cache_resource(show_spinner=False)
def retrieval(dataset_mtime: float, mode: str):
    return Retriever(documents(dataset_mtime), mode=mode)


def render_sources(sources, ids=None):
    selected = set(ids) if ids is not None else set(range(1, len(sources) + 1))
    for number, source in enumerate(sources, 1):
        if number not in selected:
            continue
        with st.expander(f"[{number}] {source['source']} · {source['title']}"):
            st.write(source["text"])
            st.link_button("Open original source", source["url"])
            st.caption(f"Reviewed/collected: {source.get('collected_at', 'Not recorded')} · Method: {source.get('collection_method', 'Not recorded')}")


mtime = (ROOT / "data" / "documents.json").stat().st_mtime
docs = documents(mtime)
api_key = os.getenv("OPENROUTER_API_KEY", "")
mode = os.getenv("RETRIEVAL_MODE", "hybrid")
st.session_state.setdefault("messages", [])
st.session_state.setdefault("questions", 0)

with st.sidebar:
    st.markdown("### ◈ Atlas")
    st.caption("PROPERTY RESEARCH")
    st.divider()
    selected_source = st.selectbox("Search within", ["All sources", "DarGlobal", "Wasalt"])
    st.markdown("**Two perspectives. One research space.**")
    st.write("Explore DarGlobal developments and Wasalt's Saudi property pages with traceable evidence.")
    st.divider()
    st.metric("Source pages", len(docs))
    st.caption("A bounded snapshot, not the full market.")
    st.caption("Source text includes English and Arabic.")
    if st.button("Start a new conversation", key="reset-chat", width="stretch"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Independent recruitment demonstration. Not an official DarGlobal or Wasalt service.")
    with st.expander("About this demo"):
        st.write("Answers use only retrieved source excerpts. Prices and availability may have changed. No investment, legal or immigration advice.")
        st.write("Wasalt pages were collected directly. DarGlobal direct requests were blocked, so its pages use short reviewed browser-text snapshots. Collection methods are recorded per page; the source package includes the scraper and authorized HTML import.")
        st.write(f"Retrieval: {'multilingual semantic + lexical' if mode == 'hybrid' else 'lexical-only'}.")

st.markdown('<div class="atlas-label">DARGLOBAL × WASALT · RESEARCH DEMO</div>', unsafe_allow_html=True)
st.markdown('<div class="atlas-title">Find the property facts.<br>See the evidence.</div>', unsafe_allow_html=True)
st.markdown('<div class="atlas-intro">Ask about locations, residences and amenities. Every supported answer connects back to the public pages behind it.</div>', unsafe_allow_html=True)
st.write("")
chat_tab, library_tab = st.tabs(["Ask Atlas", "Source library"])

with library_tab:
    st.subheader("Know what is in the collection")
    st.write("These are the pages this demo can use. Review dates describe collection, not guaranteed source freshness.")
    visible_docs = [d for d in docs if selected_source == "All sources" or d["source"] == selected_source]
    st.dataframe([{"Source": d["source"], "Page": d["title"], "Location": d.get("location", ""), "Method": d.get("collection_method", ""), "URL": d["url"]} for d in visible_docs], hide_index=True, width="stretch", column_config={"URL": st.column_config.LinkColumn("Original page")})
    for doc in visible_docs:
        with st.expander(doc["title"]):
            st.write(doc["text"])
            st.link_button("Visit source", doc["url"])
            st.caption(f"Reviewed/collected: {doc['collected_at']} · {doc.get('source_freshness', '')}")
    st.download_button("Download source metadata", data=__import__("json").dumps([{k: d.get(k) for k in ("title", "source", "url", "collected_at", "collection_method")} for d in docs], indent=2, ensure_ascii=False), file_name="atlas-sources.json", mime="application/json")

with chat_tab:
    if not api_key:
        st.info("AI answers need the owner's OpenRouter key. You can explore the source library and search evidence now; search results are not generated chatbot answers.")
    examples = ["What amenities does The Astera offer?", "Compare Tierra Viva and Les Vagues.", "Show examples of Wasalt apartments in Jeddah.", "أين يقع مشروع أيدا وما مرافقه؟"]
    pending = None
    if not st.session_state.messages:
        columns = st.columns(2)
        for i, example in enumerate(examples):
            if columns[i % 2].button(example, key=f"example-{i}", width="stretch"):
                pending = example
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                render_sources(message["sources"], message.get("source_ids"))
            if message.get("model"):
                st.caption(f"Model: {message['model']} · Sources: {len(message.get('source_ids', []))}")
    question = st.chat_input("Ask about a project, city or property feature…", max_chars=1200) or pending
    if question:
        if st.session_state.questions >= 25:
            st.warning("This demo session has reached its question limit. Please return later.")
        else:
            st.session_state.questions += 1
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Finding supporting sources…"):
                        engine = retrieval(mtime, mode)
                        # A short recent user turn helps resolve follow-up references.
                        past_users = [m["content"] for m in st.session_state.messages[:-1] if m["role"] == "user"]
                        search_query = question if len(question.split()) >= 6 or not past_users else f"{past_users[-1][:200]} {question}"
                        hits = engine.search(search_query, selected_source)
                    if not api_key:
                        st.write("**Evidence search only — AI generation is not configured.**")
                        seen = set()
                        evidence = []
                        for hit in hits:
                            if hit["url"] not in seen:
                                evidence.append(hit)
                                seen.add(hit["url"])
                        render_sources(evidence)
                        if not evidence:
                            st.write("No supporting excerpts found. Try a specific project or city.")
                        st.session_state.messages.append({"role": "assistant", "content": "Evidence search only — AI generation is not configured.", "sources": evidence})
                    else:
                        with st.spinner("Writing a source-grounded answer…"):
                            history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                            result = answer_question(question, hits, history, api_key)
                        st.markdown(result["answer"])
                        render_sources(result["sources"], result["source_ids"])
                        if result.get("model"):
                            st.caption(f"Model: {result['model']} · Source references validated")
                        st.session_state.messages.append({"role": "assistant", "content": result["answer"], **{k: result.get(k) for k in ("sources", "source_ids", "model")}})
                except ChatError as exc:
                    st.warning(str(exc))
                    st.session_state.messages.append({"role": "assistant", "content": str(exc)})
                except Exception:
                    st.error("The retrieval service could not initialize. Please retry; the owner can check the model download and application logs.")
    st.markdown('<div class="atlas-note">Verify current prices, specifications and availability with the original provider. This demo answers from a limited, dated collection.</div>', unsafe_allow_html=True)
