import os
from urllib.parse import urlsplit

import streamlit as st
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import APIConnectionError, APIStatusError, OpenAI

st.set_page_config(page_title="Custom ChatGPT", page_icon="💬", layout="wide")
st.title("Azure OpenAI ChatGPT サンプルアプリケーション")

deployment = os.getenv("OPENAI_DEPLOYMENT", "").strip() or "gpt-4.1-mini"
endpoint = os.getenv("OPENAI_API_ENDPOINT", "").strip().rstrip("/")

st.sidebar.header("ChatGPT Demo")
st.sidebar.text(f"Deployment: {deployment}")
st.sidebar.markdown("ChatGPTのパラメータ設定")
temperature = st.sidebar.slider("Temperature (温度)", 0.0, 1.0, 0.7, 0.01)
max_tokens = st.sidebar.slider("最大応答トークン数", 1, 16384, 500)
top_p = st.sidebar.slider("Top P", 0.0, 1.0, 0.9, 0.01)
system_prompt = st.sidebar.text_area(
    "System Role (システムの役割)",
    "あなたは優秀な助手です。丁寧に質問や相談に回答してください",
).strip()

conversation = st.session_state.setdefault("conversation", [])
if st.sidebar.button("Clear Chat"):
    conversation.clear()

history = [
    message
    for message in conversation
    if message["role"] in ("user", "assistant") and message["content"]
]
for message in history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

parsed_endpoint = urlsplit(endpoint)
if (
    parsed_endpoint.scheme != "https"
    or not parsed_endpoint.hostname
    or parsed_endpoint.path not in ("", "/openai/v1")
    or parsed_endpoint.query
    or parsed_endpoint.fragment
):
    st.error("OPENAI_API_ENDPOINT に Azure OpenAI リソースの HTTPS URL を設定してください。")
    st.stop()

base_url = endpoint if parsed_endpoint.path else f"{endpoint}/openai/v1"
prompt = st.chat_input("質問を入力してください")
if not prompt or not prompt.strip():
    st.stop()

user_message = {"role": "user", "content": prompt.strip()}
messages = []
if system_prompt:
    messages.append({"role": "system", "content": system_prompt})
messages.extend(history)
messages.append(user_message)

with st.chat_message("user"):
    st.markdown(user_message["content"])

try:
    with DefaultAzureCredential() as credential:
        token_provider = get_bearer_token_provider(credential, "https://ai.azure.com/.default")
        with OpenAI(
            base_url=base_url, api_key=token_provider, timeout=60.0, max_retries=1
        ) as client:
            response = client.chat.completions.create(
                model=deployment,
                messages=messages,
                max_completion_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
except APIStatusError as error:
    st.error(f"Azure OpenAI の呼び出しに失敗しました (HTTP {error.status_code})。")
    st.stop()
except (APIConnectionError, AzureError):
    st.error("Azure OpenAI に接続できませんでした。エンドポイントと認証設定を確認してください。")
    st.stop()

answer = response.choices[0].message.content if response.choices else None
if not answer:
    st.warning("モデルから表示できるテキストが返りませんでした。")
    st.stop()

conversation.extend([user_message, {"role": "assistant", "content": answer}])
with st.chat_message("assistant"):
    st.markdown(answer)
