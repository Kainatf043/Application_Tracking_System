import streamlit as st
import os
import PyPDF2 as pdf
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
from fpdf import FPDF

# 🏠 Streamlit Interface
st.set_page_config(page_title="Smart ATS", page_icon="✨", layout="centered")
st.title("✨Smart ATS - Resume Evaluator🚀")

# Load environment variables
load_dotenv()

# Sidebar: Google API key input
with st.sidebar.expander("🔒 Google API", expanded=False):
    st.markdown('[Click here](https://console.cloud.google.com/apis/credentials) to get your Google API key')
    google_api_key = st.text_input("🔑 Enter your API Key", type="password")

# Configure API Key only if it's provided
if google_api_key and google_api_key.strip():
    genai.configure(api_key=google_api_key)
else:
    st.warning("⚠️ Please enter a valid Google API Key in the sidebar.")
    st.stop()  # Prevent further execution if API key is missing

# Function to get response from Gemini API
def get_gemini_response(input_text):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(input_text)
    return response.text

# Function to extract text from uploaded PDF
def input_pdf_text(uploaded_file):
    try:
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
        return text.strip()
    except Exception as e:
        return None


# Function to generate a PDF report
def generate_pdf_report(results):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Resume Evaluation Report", ln=True, align='C')
    pdf.ln(10)
    
    for key, value in results.items():
        pdf.cell(200, 10, f"{key}: {value}", ln=True)
        pdf.ln(5)
    
    # Generate PDF output as a string
    pdf_output = pdf.output(dest='S').encode('latin1')  # Use 'S' for string output and then encode to bytes
    pdf_report = BytesIO(pdf_output)  # Store it in BytesIO for download
    pdf_report.seek(0)  # Reset the pointer to the beginning of the buffer
    return pdf_report



# Prompt template
input_prompt = """
Hey Act Like a skilled or very experienced ATS(Application Tracking System)
with a deep understanding of the tech field, software engineering, data science, data analyst,
and big data engineer. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide the best assistance for improving
the resumes. Assign the percentage matching based on JD and the missing keywords with high accuracy.
resume:{text}
description:{jd}

I want the response in one single string having the structure:
{{"JD Match":"%","MissingKeywords":[],"Profile Summary":"","Suggestions": ""}}
"""


st.markdown("**📢 Get instant feedback on your resume & improve your job match chances!**")

# 🎯 Job description input
jd = st.text_area("📝 Paste the Job Description:", 
                  placeholder="Enter the job description here...", 
                  label_visibility="collapsed")

# 📄 Upload Multiple Resumes
uploaded_files = st.file_uploader("📄 Upload your Resume(s) (PDF format only):", 
                                  type="pdf", 
                                  help="Please upload resume(s) in PDF format.", 
                                  accept_multiple_files=True)

# 🔘 Submit Button
submit = st.button("📊 Evaluate Resume(s) 🧑‍💻")

# 🟢 Process evaluation when button is clicked
if submit:
    if uploaded_files and jd.strip():
        with st.spinner("🔄 Processing... Please wait while we evaluate your resumes..."):
            best_match = {"JD Match": "0%", "MissingKeywords": [], "Profile Summary": "", "Suggestions": ""}
            best_resume = ""
            
            for uploaded_file in uploaded_files:
                text = input_pdf_text(uploaded_file)
                if not text:
                    st.error(f"❌ Failed to extract text from {uploaded_file.name}. Please upload a valid PDF file.")
                    continue
                
                formatted_prompt = input_prompt.format(text=text, jd=jd)
                try:
                    response = get_gemini_response(formatted_prompt)
                    response_dict = eval(response)
                    
                    st.success(f"✅ Evaluation for {uploaded_file.name}")
                    st.markdown(f"📊 **Job Description Match**: **{response_dict['JD Match']}%** 🎯")
                    st.markdown(f"💬 **Profile Summary**: {response_dict['Profile Summary']} 💡")
                    
                    if response_dict["MissingKeywords"]:
                        st.markdown(f"❌ **Missing Keywords**: {', '.join(response_dict['MissingKeywords'])} 🚫")
                    else:
                        st.markdown("✅ **No missing keywords detected!** 🎉")
                    
                    st.info(f"💡 **Suggestions**: {response_dict['Suggestions']}")
                    
                    if int(response_dict['JD Match'].replace('%', '')) > int(best_match['JD Match'].replace('%', '')):
                        best_match = response_dict
                        best_resume = uploaded_file.name
                
                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {e}")
            
            # Display best-matching resume
            st.markdown("### 🏆 **Best Matching Resume:**")
            st.markdown(f"🎖️ **{best_resume}** with **{best_match['JD Match']}% match**")
            
            # Generate and download PDF report
            pdf_report = generate_pdf_report(best_match)
            st.download_button("📥 Download Report as PDF", pdf_report, "resume_evaluation_report.pdf", "application/pdf")
    else:
        st.warning("⚠️ Please provide both a job description and at least one resume before submitting! ✋")
