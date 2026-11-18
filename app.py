from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import streamlit as st
from dotenv import load_dotenv
from src.chat import ChatError, answer_question
from src.corpus import ROOT, load_documents
from src.retrieval import Retriever

load_dotenv(ROOT / ".env")
st.set_page_config(page_title="Atlas | Property chatbot", page_icon="💬", layout="centered")
st.markdown("""<style>
#MainMenu, footer {visibility:hidden;}
.block-container {max-width:800px;padding-top:2rem;}
div.stButton>button {border-radius:12px;}
</style>""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def retrieval(dataset_mtime: float, mode: str):
    return Retriever(load_documents(), mode=mode)


def new_chat():
    st.session_state.messages = []
    st.session_state.pop("pending_question", None)
    st.session_state.chat_number += 1
    # Keep session usage limits when resetting the conversation.


def ask_example(question):
    st.session_state.pending_question = question


def show_sources(message):
    sources = message.get("sources") or []
    ids = message.get("source_ids") or []
    if ids:
        with st.expander("Sources"):
            for number in ids:
                if type(number) is int and 1 <= number <= len(sources):
                    source = sources[number - 1]
                    st.markdown(f"[{number}] [{source['title']}]({source['url']})")


st.session_state.setdefault("messages", [])
st.session_state.setdefault("questions", 0)
st.session_state.setdefault("chat_number", 0)
api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
mode = os.getenv("RETRIEVAL_MODE", "lexical")

title, reset = st.columns([3, 1])
with title:
    st.title("Atlas")
with reset:
    st.button("New chat", key="reset-chat", on_click=new_chat, width="stretch")
st.caption("Ask about DarGlobal projects and Wasalt properties.")

if not api_key:
    st.info("AI answers are not configured. The owner needs to add the OpenRouter key.")

if not st.session_state.messages and "pending_question" not in st.session_state:
    st.write("Hi! What would you like to know?")
    examples = [
        "What amenities does The Astera offer?",
        "Compare Tierra Viva and Les Vagues.",
        "Show examples of Wasalt apartments in Jeddah.",
    ]
    for i, question in enumerate(examples):
        st.button(question, key=f"example-{i}", on_click=ask_example, args=(question,), width="stretch")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        show_sources(message)

typed = st.chat_input("Type your question…", key=f"question-{st.session_state.chat_number}", max_chars=1200)
pending = st.session_state.pop("pending_question", None)
question = typed or pending
if question:
    if st.session_state.questions >= 25:
        st.warning("This session has reached its question limit. Please return later.")
    elif not api_key:
        st.warning("AI answers need the owner's OpenRouter key before you can chat.")
    else:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        st.session_state.questions += 1
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking…"):
                    mtime = (ROOT / "data" / "documents.json").stat().st_mtime
                    engine = retrieval(mtime, mode)
                    past_users = [m["content"] for m in history if m["role"] == "user"]
                    search_query = question if len(question.split()) >= 6 or not past_users else f"{past_users[-1][:200]} {question}"
                    hits = engine.search(search_query, k=4)
                    result = answer_question(question, hits, history, api_key)
                message = {"role": "assistant", "content": result["answer"], "sources": result["sources"], "source_ids": result["source_ids"]}
            except ChatError as exc:
                message = {"role": "assistant", "content": str(exc)}
            except Exception:
                logging.exception("Chat request failed")
                message = {"role": "assistant", "content": "I couldn't complete that request. Please try again shortly."}
            st.session_state.messages.append(message)
        st.rerun()

st.caption("Answers use collected public pages. Confirm current prices and availability with the source.")
