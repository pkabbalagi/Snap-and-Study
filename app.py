import time
import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Snap & Study",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

MODEL_NAME = "gemini-3.8-flash"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        margin-top: 0px;
        opacity: 0.75;
    }

    .feature-card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 15px;
    }

    .success-box {
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(0,180,100,0.3);
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# GEMINI CLIENT
# ============================================================

@st.cache_resource
def get_gemini_client():

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing from "
            ".streamlit/secrets.toml"
        )

    return genai.Client(
        api_key=api_key
    )


try:

    client = get_gemini_client()

except Exception as error:

    st.error("❌ Gemini configuration error.")
    st.code(str(error))
    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "student_name" not in st.session_state:
    st.session_state.student_name = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    st.session_state.chat = None

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "started" not in st.session_state:
    st.session_state.started = False


# ============================================================
# CREATE GEMINI CHAT
# ============================================================

def create_chat():

    return client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )


# ============================================================
# GEMINI REQUEST
# ============================================================

def ask_gemini(parts):

    if st.session_state.chat is None:

        st.session_state.chat = create_chat()

    last_error = None

    # Only retry temporary server errors.
    # Quota errors are NOT retried.
    for attempt in range(2):

        try:

            response = (
                st.session_state.chat.send_message(
                    parts
                )
            )

            if response and response.text:

                return response.text

            return (
                "I could not generate a response. "
                "Please try again."
            )

        except Exception as error:

            last_error = error

            error_text = str(error)

            # --------------------------------------------
            # QUOTA ERROR
            # --------------------------------------------

            if (
                "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            ):

                raise RuntimeError(
                    "GEMINI_QUOTA_EXCEEDED"
                )

            # --------------------------------------------
            # TEMPORARY SERVER ERROR
            # --------------------------------------------

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
            ):

                if attempt == 0:

                    time.sleep(5)

                    continue

            break

    raise RuntimeError(
        str(last_error)
    )


# ============================================================
# ADD MESSAGE
# ============================================================

def add_message(
    role,
    message_type,
    content
):

    st.session_state.messages.append(
        {
            "role": role,
            "type": message_type,
            "content": content
        }
    )


# ============================================================
# GENERATE LOCAL SUMMARY
# ============================================================
# IMPORTANT:
# This DOES NOT call Gemini.
# Therefore it consumes ZERO additional API requests.
# ============================================================

def generate_summary():

    answers = []

    for message in st.session_state.messages:

        if (
            message["role"] == "assistant"
            and message["type"] == "text"
        ):

            answers.append(
                message["content"]
            )

    if not answers:

        return (
            "No AI study responses are available "
            "for creating a summary."
        )

    # Use the latest five AI responses
    answers = answers[-5:]

    summary = (
        "📚 SNAP & STUDY\n"
        "QUICK REVISION SUMMARY\n\n"
    )

    for number, answer in enumerate(
        answers,
        start=1
    ):

        summary += (
            f"⭐ Study Point {number}\n"
            f"{answer}\n\n"
        )

    summary += (
        "🎯 Use these points for quick revision "
        "before your exam."
    )

    return summary


# ============================================================
# CLEAR SESSION
# ============================================================

def clear_session():

    st.session_state.student_name = ""
    st.session_state.messages = []
    st.session_state.chat = None
    st.session_state.summary = ""
    st.session_state.started = False


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 📚 Snap & Study"
    )

    st.write(
        "AI-Powered Study Assistant"
    )

    st.divider()

    st.markdown(
        "### Features"
    )

    st.write("📷 Study image analysis")
    st.write("🤖 AI explanations")
    st.write("💬 Follow-up questions")
    st.write("📝 Quick revision summary")
    st.write("⬇️ Download study notes")

    st.divider()

    if st.session_state.started:

        st.write(
            f"👤 Student: "
            f"**{st.session_state.student_name}**"
        )

        if st.button(
            "🗑️ Start New Session",
            use_container_width=True
        ):

            clear_session()
            st.rerun()


# ============================================================
# WELCOME / START SCREEN
# ============================================================

if not st.session_state.started:

    st.markdown(
        '<div class="main-title">📚 Snap & Study</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Snap it. Understand it. Study smarter.'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown(
        """
        ### 🎓 Your AI Study Assistant

        Snap & Study helps students understand study
        material using AI.

        Upload a study image, ask questions, get
        simple explanations, and create quick
        revision notes.
        """
    )

    st.divider()

    student_name = st.text_input(
        "👤 Enter your name",
        placeholder="Example: Priyanka"
    )

    if st.button(
        "🚀 Start Studying",
        type="primary",
        use_container_width=True
    ):

        if not student_name.strip():

            st.warning(
                "Please enter your name."
            )

        else:

            st.session_state.student_name = (
                student_name.strip()
            )

            st.session_state.started = True

            st.session_state.chat = (
                create_chat()
            )

            welcome_message = (
                WELCOME_MESSAGE_TEMPLATE.format(
                    name=st.session_state.student_name
                )
            )

            add_message(
                "assistant",
                "text",
                welcome_message
            )

            st.rerun()

    st.stop()


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<div class="main-title">📚 Snap & Study</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-Powered Study Assistant'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# QUICK ACTIONS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown(
        """
        <div class="feature-card">
        📷 <b>Upload</b><br>
        Upload notes or study material.
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:

    st.markdown(
        """
        <div class="feature-card">
        🤖 <b>Understand</b><br>
        Get simple AI explanations.
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:

    st.markdown(
        """
        <div class="feature-card">
        📝 <b>Revise</b><br>
        Generate quick revision notes.
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DISPLAY CHAT
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        if message["type"] == "text":

            st.write(
                message["content"]
            )

        elif message["type"] == "image":

            st.image(
                message["content"],
                caption="Uploaded study material",
                use_container_width=True
            )


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Ask a question or upload a study image...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png"
    ]
)


# ============================================================
# PROCESS USER INPUT
# ============================================================

if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text.strip()

    parts = []


    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if photo is not None:

        image_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            image_bytes
        )

        parts.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=photo.type
            )
        )


    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    if text:

        add_message(
            "user",
            "text",
            text
        )

        parts.append(
            text
        )


    # --------------------------------------------------------
    # IMAGE WITHOUT QUESTION
    # --------------------------------------------------------

    elif photo is not None:

        parts.append(
            """
            Analyze this study image.

            Give the student:

            📌 TOPIC

            📖 SIMPLE EXPLANATION

            ⭐ IMPORTANT POINTS

            📝 KEY DEFINITIONS

            🎯 EXAM POINTS

            📚 QUICK SUMMARY

            Use simple student-friendly language.

            Only use information visible or clearly
            understandable from the image.

            Do not invent information.
            """
        )


    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    if parts:

        with st.spinner(
            "🤖 Snap & Study is analyzing..."
        ):

            try:

                answer = ask_gemini(
                    parts
                )

                add_message(
                    "assistant",
                    "text",
                    answer
                )

                st.rerun()

            except RuntimeError as error:

                if (
                    str(error)
                    == "GEMINI_QUOTA_EXCEEDED"
                ):

                    st.error(
                        "⚠️ Gemini API quota exceeded."
                    )

                    st.info(
                        "Your current Gemini API project "
                        "has reached its free-tier request "
                        "limit. Wait for the quota reset or "
                        "use a new API project/key."
                    )

                else:

                    st.error(
                        "❌ Gemini request failed."
                    )

                    st.code(
                        str(error)
                    )

            except Exception as error:

                st.error(
                    "❌ Image/question analysis failed."
                )

                st.code(
                    str(error)
                )


# ============================================================
# SUMMARY SECTION
# ============================================================

has_ai_response = any(
    message["role"] == "assistant"
    and message["type"] == "text"
    for message in st.session_state.messages
)


if has_ai_response:

    st.divider()

    st.subheader(
        "📝 Study Summary"
    )

    st.write(
        "Create a quick revision summary from "
        "the explanations already generated."
    )

    if st.button(
        "✨ Generate Study Summary",
        type="primary",
        use_container_width=True
    ):

        st.session_state.summary = (
            generate_summary()
        )


# ============================================================
# DISPLAY SUMMARY
# ============================================================

if st.session_state.summary:

    st.markdown(
        "### 📚 Quick Revision Notes"
    )

    st.text_area(
        "Your summary",
        value=st.session_state.summary,
        height=400
    )

    st.download_button(
        label="⬇️ Download Study Summary",
        data=st.session_state.summary,
        file_name="snap_and_study_summary.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.success(
        "✅ Your study summary is ready!"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Snap & Study | AI-Powered Study Assistant"
)