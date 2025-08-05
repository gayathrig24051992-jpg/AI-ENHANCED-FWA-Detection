# AI-ENHANCED-FWA-Detection
“Smart claims screening with uncompromising accuracy.”

Medisight AI Enhanced is a Streamlit application for automated healthcare claims processing. It leverages AWS Bedrock for fraud, waste, and abuse analysis, Comprehend Medical for PHI detection, and integrates S3 and DynamoDB for storage and audit logging.
Features
Page-by-page PDF viewer using pdf2image

Text extraction and targeted page analysis

Bedrock Agent integration for FWA analysis and executive summaries

PHI detection and automated redaction with Comprehend Medical

Risk scoring based on customizable keyword metrics

Prerequisites
Python 3.8 or higher

pip package manager

Poppler utilities installed (for pdf2image)

AWS account with:

S3 bucket

DynamoDB table named ClaimsAudit

Comprehend Medical enabled

Bedrock Agent and alias created

S3 storage for original documents

DynamoDB audit trail with user, role, timestamp, and risk score

Interactive chat interface for follow-up questions


