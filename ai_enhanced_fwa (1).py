# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import streamlit as st
import boto3
import uuid
import base64
import pdfplumber
from PyPDF2 import PdfReader
from io import BytesIO
from PIL import Image
import re



# --- Configuration ---
# --- Configuration (Fixed to use st.secrets) ---
# IMPORTANT: Before running, create a .streamlit/secrets.toml file with your
# AWS credentials. Example:
# [aws]
# aws_access_key_id = "YOUR_AWS_ACCESS_KEY_ID"
# aws_secret_access_key = "YOUR_AWS_SECRET_ACCESS_KEY"
# aws_region = "ap-south-1"
# [bedrock]
# agent_id = "5GILSDVVQO"
# agent_alias_id = "TSTALIASID"
try:
    AWS_ACCESS_KEY_ID = st.secrets["aws"]["aws_access_key_id"]
    AWS_SECRET_ACCESS_KEY = st.secrets["aws"]["aws_secret_access_key"]
    AWS_REGION = st.secrets["aws"].get("aws_region", "ap-south-1")
    AGENT_ID = st.secrets["bedrock"]["agent_id"]
    AGENT_ALIAS_ID = st.secrets["bedrock"]["agent_alias_id"]
except KeyError as e:
    st.error(f"Missing secret: {e}")
    st.stop()

# --- Helper Functions ---
def extract_text_from_pdf_pages(uploaded_file, pages):
    text = ""
    try:
        reader = PdfReader(uploaded_file)
        page_indices = [p - 1 for p in pages if 0 < p <= len(reader.pages)]
        for i in page_indices:
            page_text = reader.pages[i].extract_text()
            if page_text:
                text += f"--- Page {i+1} ---\n{page_text}\n\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def query_bedrock_agent(text, prompt_prefix=""):
    try:
        client = boto3.client(
            'bedrock-agent-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        session_id = str(uuid.uuid4())
        full_prompt = f"{prompt_prefix}\n\nHere is the context:\n{text}"

        response = client.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=full_prompt
        )

        completion = ""
        for event in response['completion']:
            chunk = event.get('chunk')
            if chunk and 'bytes' in chunk:
                completion += chunk['bytes'].decode('utf-8')

        return completion or "I DO NOT HAVE ANSWER AT PRESENT"
    except Exception as e:
        st.error(f"Bedrock error: {e}")
        return "I DO NOT HAVE ANSWER AT PRESENT"

def show_pdf_preview(uploaded_file, page_num):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            page = pdf.pages[page_num - 1]
            img = page.to_image(resolution=150).original
            st.image(img, caption=f"Page {page_num}", use_container_width=True)
    except Exception as e:
        st.warning(f"Preview error: {e}")

def extract_score(text):
    match = re.search(r'(\d{1,3})', text)
    if match:
        score = int(match.group(1))
        return min(score, 100)
    return None

# --- App Layout ---
st.set_page_config(page_title="Medisight AI", layout="wide")
st.title("🏥 Medisight AI : Healthcare Claims Processing Agent")

st.markdown("""
An advanced Agentic AI system built on AWS Bedrock to analyze medical claims for Fraud, Waste, and Abuse (FWA).
""")

# --- State Initialization ---
for key in ['uploaded_file_name', 'pdf_text', 'agent_response', 'pdf_pages', 'chat_history']:
    st.session_state.setdefault(key, None if key != 'chat_history' else [])

# --- Layout Columns ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📁 Upload & Settings")
    uploaded_file = st.file_uploader("Upload Medical Claim PDF", type="pdf")

    if uploaded_file:
        uploaded_file_bytes = uploaded_file.getvalue()
        if uploaded_file.name != st.session_state.uploaded_file_name:
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.pdf_text = ""
            st.session_state.agent_response = None
            st.session_state.pdf_pages = []
            st.session_state.chat_history = []

        pdf_reader = PdfReader(BytesIO(uploaded_file_bytes))
        total_pages = len(pdf_reader.pages)
        st.info(f"PDF has {total_pages} page(s).")

        page_options = list(range(1, total_pages + 1))
        selected_pages = st.multiselect("Select pages for analysis:", page_options, default=page_options)
        st.session_state.pdf_pages = selected_pages

    if st.button("🚀 Analyze Claim"):
        if not uploaded_file:
            st.error("Upload a PDF first.")
        elif not st.session_state.pdf_pages:
            st.warning("Select at least one page.")
        else:
            with st.spinner("Extracting text..."):
                pdf_text = extract_text_from_pdf_pages(BytesIO(uploaded_file_bytes), st.session_state.pdf_pages)
            st.session_state.pdf_text = pdf_text

            if pdf_text:
                with st.spinner("Analyzing with Bedrock Agent..."):
                    prompt = "Analyze this medical claim for potential Fraud, Waste, and Abuse. Provide a detailed report."
                    response = query_bedrock_agent(pdf_text, prompt)
                st.session_state.agent_response = response
                st.session_state.chat_history.append({"role": "assistant", "content": response})

    if st.button("🔄 Reset App"):
        st.session_state.clear()
        st.experimental_rerun()

    with st.expander("🔧 Configuration"):
        st.text_input("Agent ID", value=AGENT_ID, disabled=True)
        st.text_input("Alias ID", value=AGENT_ALIAS_ID, disabled=True)
        st.text_input("Region", value=AWS_REGION, disabled=True)

with col2:
    if uploaded_file:
        st.subheader("📄 PDF Viewer")
        for page_num in st.session_state.pdf_pages:
            show_pdf_preview(uploaded_file, page_num)

        st.download_button("📥 Download PDF", uploaded_file_bytes, uploaded_file.name, mime="application/pdf")

        st.subheader("📋 Extracted Text")
        if st.session_state.pdf_text:
            st.text_area("Text", st.session_state.pdf_text, height=200, disabled=True)
        else:
            st.info("Click 'Analyze Claim' to extract text.")

    st.subheader("🔍 AI Assistant")
    if st.session_state.agent_response:
        st.success("✅ Analysis Complete")

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"], avatar="🙋‍♂️" if msg["role"] == "user" else "🤖"):
                st.write(msg["content"])

        st.markdown("---")
        st.subheader("🧠 Actions")
        ac1, ac2, ac3 = st.columns(3)

        with ac1:
            if st.button("❓ Explain Rejection"):
                prompt = "Explain why this claim might be rejected and suggest resolution steps."
                response = query_bedrock_agent(st.session_state.pdf_text, prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

        with ac2:
            if st.button("📊 Get Risk Score"):
                prompt = "Assign a risk score (0-100) for Fraud, Waste, and Abuse. Justify the score."
                response = query_bedrock_agent(st.session_state.pdf_text, prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                score = extract_score(response)
                if score is not None:
                    st.progress(score / 100)
                    st.info(f"Estimated FWA Risk Score: {score}/100")
                st.rerun()

        with ac3:
            if st.button("🛠️ Suggest Corrections"):
                prompt = "Suggest corrections to improve claim approval chances."
                response = query_bedrock_agent(st.session_state.pdf_text, prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

        st.markdown("---")
        if st.button("📄 Generate Full Analysis Report"):
            prompt = """
            Please generate a comprehensive analysis report for the following medical claim.
            Include:
            1. Summary of the claim
            2. Any detected issues (Fraud, Waste, Abuse)
            3. Risk score (0–100) with justification
            4. Reasons for potential rejection
            5. Suggested corrections
            6. Likelihood of approval
            Format the report clearly with headings.
            """
            with st.spinner("🧠 Generating full report..."):
                report = query_bedrock_agent(st.session_state.pdf_text, prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": report})
            st.subheader("📋 Full Analysis Report")
            st.markdown(report)

        if st.button("🔍 Extract Claim Metadata"):
          prompt = "Extract key metadata from this claim: patient name, provider, date of service, claim amount, diagnosis codes."
          response = query_bedrock_agent(st.session_state.pdf_text, prompt)
          st.session_state.chat_history.append({"role": "assistant", "content": response})
          st.subheader("📌 Claim Metadata")
          st.markdown(response)


