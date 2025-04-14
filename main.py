import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
from datetime import datetime, timedelta
import time
from agent import make_agent
from gmail_tools import gmail_authenticate

# Page configuration
st.set_page_config(
    page_title="Gmail Manager",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'service' not in st.session_state:
    st.session_state.service = None
if 'email_data' not in st.session_state:
    st.session_state.email_data = None
if 'analytics' not in st.session_state:
    st.session_state.analytics = None
if 'progress' not in st.session_state:
    st.session_state.progress = 0

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4285F4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #34A853;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #E8F0FE;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #4285F4;
    }
    .metric-label {
        font-size: 1rem;
        color: #5F6368;
    }
</style>
""", unsafe_allow_html=True)

# Authentication function
def authenticate():
    with st.spinner("Authenticating with Gmail..."):
        try:
            service = gmail_authenticate()
            st.session_state.service = service
            st.session_state.authenticated = True
            st.success("Authentication successful!")
            return True
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            st.info("Make sure you have client_secret.json in the same directory")
            return False

# Sidebar navigation
st.sidebar.markdown("<h1 style='text-align: center;'>Gmail Manager</h1>", unsafe_allow_html=True)

# Authentication section in sidebar
with st.sidebar.expander("Authentication", expanded=not st.session_state.authenticated):
    if not st.session_state.authenticated:
        st.write("Please authenticate with your Gmail account")
        if st.button("Authenticate"):
            authenticate()
    else:
        st.success("Authenticated")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.service = None
            st.session_state.email_data = None
            st.session_state.analytics = None
            st.rerun()

# Navigation - Only show AI Assistant
if st.session_state.authenticated:
    page = "AI Assistant"
else:
    page = "Welcome"

# Main content area
if page == "Welcome":
    st.markdown("<h1 class='main-header'>Welcome to Gmail Manager</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class='card'>
        <h2>Manage your Gmail inbox efficiently</h2>
        <p>This application helps you analyze, organize, and clean up your Gmail inbox with powerful tools:</p>
        <ul>
            <li>📊 <strong>Email Analytics</strong> - Understand your email patterns</li>
            <li>🧹 <strong>Bulk Actions</strong> - Clean up your inbox with smart filters</li>
            <li>📝 <strong>Email Rules</strong> - Create automated rules for email management</li>
            <li>⏱️ <strong>Scheduled Cleanup</strong> - Set up regular maintenance tasks</li>
        </ul>
        <p>To get started, please authenticate with your Gmail account using the button in the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.image("https://ssl.gstatic.com/ui/v1/icons/mail/rfr/logo_gmail_lockup_default_1x_r5.png", width=200)
        if not st.session_state.authenticated:
            if st.button("Authenticate with Gmail", key="welcome_auth"):
                authenticate()

elif page == "AI Assistant":
    st.markdown("<h1 class='main-header'>AI Email Assistant</h1>", unsafe_allow_html=True)
    
    # Command palette with examples
    with st.expander("💡 Try these commands", expanded=True):
        cols = st.columns(3)
        with cols[0]:
            st.markdown("**Email Management**")
            st.caption("• Unsubscribe from newsletters")
            st.caption("• Delete old promotional emails")
            st.caption("• Archive unimportant messages")
        
        with cols[1]:
            st.markdown("**Email Analysis**")
            st.caption("• Show important emails")
            st.caption("• Analyze sender patterns")
            st.caption("• Categorize my inbox")
        
        with cols[2]:
            st.markdown("**Automation**")
            st.caption("• Create rule for social emails")
            st.caption("• Schedule weekly cleanup")
            st.caption("• Apply all email rules")

    # Initialize chat and agent
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How can I help manage your Gmail today?"}]
    
    if "agent" not in st.session_state:
        st.session_state.agent = make_agent(st.session_state.service)

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], dict):
                if "table" in message["content"]:
                    st.dataframe(message["content"]["table"])
                elif "chart" in message["content"]:
                    st.plotly_chart(message["content"]["chart"])
                else:
                    st.write(message["content"])
            else:
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to do with your emails?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    response = st.session_state.agent.run(prompt)
                    
                    # Format response based on content
                    if "|" in response and "-" in response:  # Simple table detection
                        try:
                            import pandas as pd
                            from io import StringIO
                            df = pd.read_csv(StringIO(response), sep="|").dropna(axis=1, how='all')
                            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
                            st.session_state.messages.append({"role": "assistant", "content": {"table": df}})
                            st.dataframe(df)
                        except:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.markdown(response)
                    else:
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.markdown(response)
                
                except Exception as e:
                    error_msg = f"⚠️ Error: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    st.error(error_msg)

# Run the app
if __name__ == "__main__":
    # Check if client_secret.json exists
    if not os.path.exists('client_secret.json'):
        st.error("""
        client_secret.json not found!
        
        To use this app, you need to:
        1. Create a Google Cloud project
        2. Enable the Gmail API
        3. Create OAuth credentials
        4. Download the credentials as client_secret.json
        5. Place the file in the same directory as this app
        
        For detailed instructions, visit: https://developers.google.com/gmail/api/quickstart/python
        """)
