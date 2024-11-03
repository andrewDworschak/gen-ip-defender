import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import openai
from fraud_case_input import load_fraud_case_images
from o1_detector import generate_infringement_report, InfringementVerdict

# Function to load token data
@st.cache_data
def load_token_data():
    return load_fraud_case_images("fraud_case_images.csv", "token_data.csv")

# Function to get image from URL
def get_image_from_url(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img


def get_color(verdict):
    if verdict == InfringementVerdict.infringement:
        return "#FFCDD2"  # Light Red
    elif verdict == InfringementVerdict.coincidence:
        return "#C8E6C9"  # Light Green
    else:
        # For Fair Use verdicts
        return "#BBDEFB"  # Light Blue


# Function to display the infringement report nicely
def display_infringement_report(report):

    if report and report.analysis:
        for idx, analysis in enumerate(report.analysis):
            color = get_color(analysis.verdict)
            analysis_html = f"""
                    <div style="
                        border-left: 8px solid {color};
                        padding-left: 15px;
                        padding-bottom: 2px;
                        margin-bottom: 20px;
                        background-color: #F5F5F5;
                        border-radius: 5px;
                    ">
                        <h3 style="color: #333;">Analysis {idx + 1}</h3>
                        <p style="color: #000;"><strong>Image Component:</strong> {analysis.image_component}</p>
                        <p style="color: #000;"><strong>Brand:</strong> {analysis.brand}</p>
                        <p style="color: #000;"><strong>Branded Content:</strong> {analysis.branded_content}</p>
                        <p style="color: #000;"><strong>Relation:</strong> {analysis.relation}</p>
                        <p style="color: #000;"><strong>Intent:</strong> {analysis.intent}</p>
                        <p style="color: #000;"><strong>Reason for:</strong> {analysis.reason_for}</p>
                        <p style="color: #000;"><strong>Reason against:</strong> {analysis.reason_against}</p>
                        <p style="color: #000;"><strong>Verdict:</strong> {analysis.verdict.value}</p>
                    </div>
                    """
            st.markdown(analysis_html, unsafe_allow_html=True)
    else:
        st.write("No analyses available in the report.")


def app():
    st.title("Infringement Report Generator")

    # Get OpenAI API key
    openai_api_key = st.sidebar.text_input('Enter your OpenAI API key', type='password')
    if not openai_api_key:
        st.warning('Please enter your OpenAI API key to proceed.')
        st.stop()
    else:
        openai.api_key = openai_api_key

    # Load token data
    token_data = load_token_data()
    total_tokens = len(token_data)

    # Initialize session state variables
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0

    if 'infringement_reports' not in st.session_state:
        st.session_state.infringement_reports = {}

    # Token navigation
    index = st.number_input('Select token index', min_value=0, max_value=total_tokens - 1, value=st.session_state.current_index, step=1)
    st.session_state.current_index = index

    # Get current token
    token = token_data[int(st.session_state.current_index)]

    # Display image
    image_url = token["preview_url"]
    try:
        image = get_image_from_url(image_url)
        st.image(image, caption=f"Token Index: {int(st.session_state.current_index)}")
    except Exception as e:
        st.error(f"Failed to load image: {e}")

    # Display token details
    st.write("Token Details:")
    st.write(token)

    # Check if infringement report exists
    if st.session_state.current_index in st.session_state.infringement_reports:
        infringement_report = st.session_state.infringement_reports[st.session_state.current_index]
        st.write("Infringement Report:")
        display_infringement_report(infringement_report)
    else:
        st.write("No Infringement Report generated yet.")

    # Button to generate infringement report
    if st.button('Generate Infringement Report'):
        with st.spinner('Generating infringement report...'):
            try:
                infringement_report = generate_infringement_report(image_url=image_url, api_key=openai_api_key)
                # Store the report in session_state
                st.session_state.infringement_reports[st.session_state.current_index] = infringement_report
                st.success('Infringement report generated.')
            except RuntimeError as e:
                st.error(f"Refusal: {e}")
            except Exception as e:
                st.error(f"Error: {e}")

        # Display the infringement report
        if st.session_state.current_index in st.session_state.infringement_reports:
            infringement_report = st.session_state.infringement_reports[st.session_state.current_index]
            st.write("Infringement Report:")
            display_infringement_report(infringement_report)


if __name__ == "__main__":
    app()