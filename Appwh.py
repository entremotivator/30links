import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import time
import re
import hashlib
from io import BytesIO
import base64
import io

# ==================== PAGE CONFIG ==================== #
st.set_page_config(
    page_title="LinkedIn Analytics & Habit Tracker Pro - Complete Edition",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== STATIC CONFIGURATION ==================== #
CHAT_SPREADSHEET_ID = "1klm60YFXSoV510S4igv5LfREXeykDhNA5Ygq7HNFN0I"
CHAT_SHEET_NAME = "linkedin_chat_history_advanced 2"
OUTREACH_SPREADSHEET_ID = "1eLEFvyV1_f74UC1g5uQ-xA7A62sK8Pog27KIjw_Sk3Y"
OUTREACH_SHEET_NAME = "linkedin-tracking-csv.csv"
MY_PROFILE = {"name": "Donmenico Hudson", "url": "https://www.linkedin.com/in/donmenicohudson/"}
WEBHOOK_URL = "https://agentonline-u29564.vm.elestio.app/webhook/Leadlinked"
DAILY_TRACKER_SHEET_ID = "1UkuTf8VwGPIilTxhTEdP9K-zdtZFnThazFdGyxVYfmg"
LEADS_DATABASE_SHEET_ID = "1eLEFvyV1_f74UC1g5uQ-xA7A62sK8Pog27KIjw_Sk3Y"
DAILY_TRACKER_SHEET_NAME = "daily_tracker_20251021"
LEADS_SHEET_GID = "1881909623"

# ==================== SESSION STATE ==================== #
for key, default in [
    ("authenticated", False), ("gsheets_client", None), ("activity_log", []),
    ("sent_leads", set()), ("selected_leads", []), ("current_client", None),
    ("chat_df", pd.DataFrame()), ("outreach_df", pd.DataFrame()),
    ("last_refresh", datetime.utcnow()), ("webhook_history", []), ("email_queue", []),
    ("show_notifications", True), ("dark_mode", False), ("selected_contact", None),
    ("filter_status", "all"), ("filter_date_range", 7), ("sort_by", "timestamp"),
    ("search_query", ""), ("favorites", set()), ("notes", {}), ("tags", {}),
    ("export_format", "csv"), ("auto_refresh", False), ("refresh_interval", 60),
    ("daily_tracker", pd.DataFrame()), ("leads_database", pd.DataFrame()),
    ("challenge_start_date", datetime.now().strftime("%Y-%m-%d")), ("sheets_data", None),
    ("leads_sheets_data", None), ("webhook_test_payload", "{}"),
    ("current_page", "🏠 Dashboard") # Added for multi-page navigation
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ==================== ENHANCED STYLES ==================== #
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    * { 
        font-family: 'Inter', sans-serif; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stApp { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Main Title with Animation */
    .main-title {
        text-align: center; 
        font-size: 4rem; 
        font-weight: 900;
        background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem; 
        text-shadow: 0 4px 20px rgba(0,0,0,0.3);
        animation: fadeInDown 0.8s ease-out;
        letter-spacing: -2px;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .sub-title {
        text-align: center; 
        font-size: 1.4rem; 
        color: #ffffff;
        margin-bottom: 3rem; 
        font-weight: 500; 
        opacity: 0.95;
        animation: fadeIn 1s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Enhanced Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 25px; 
        padding: 2.5rem; 
        text-align: center;
        box-shadow: 0 15px 45px rgba(0,0,0,0.2); 
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border: 2px solid rgba(255, 255, 255, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: rotate(45deg);
        transition: all 0.5s;
    }
    
    .metric-card:hover {
        transform: translateY(-10px) scale(1.02);
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    
    .metric-card:hover::before {
        left: 100%;
    }
    
    .metric-value { 
        font-size: 3.5rem; 
        font-weight: 900; 
        margin-bottom: 0.8rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: countUp 1s ease-out;
    }
    
    @keyframes countUp {
        from { transform: scale(0.5); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }
    
    .metric-label { 
        font-size: 1.1rem; 
        color: #666; 
        text-transform: uppercase; 
        letter-spacing: 2px; 
        font-weight: 700;
    }
    
    .metric-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
    }
    
    /* Enhanced Lead Cards */
    .lead-card, .email-card, .crm-card, .habit-card {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(20px);
        border-radius: 25px; 
        padding: 2.5rem; 
        margin-bottom: 2rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15); 
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border-left: 6px solid #667eea;
        position: relative;
        overflow: hidden;
    }
    
    .lead-card::after, .email-card::after, .crm-card::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 0 0 0 100%;
    }
    
    .lead-card:hover, .email-card:hover, .crm-card:hover, .habit-card:hover {
        transform: translateY(-12px);
        box-shadow: 0 20px 50px rgba(0,0,0,0.25);
        border-left-width: 8px;
    }
    
    .lead-card *, .email-card *, .crm-card *, .habit-card *, .message-card-all * {
        color: #2d3748 !important;
    }
    
    .lead-title { 
        font-size: 1.8rem; 
        font-weight: 800; 
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .lead-sub { 
        font-size: 1.1rem; 
        margin-bottom: 0.8rem; 
        font-weight: 500;
        opacity: 0.8;
    }
    
    .lead-msg {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 20px; 
        padding: 1.8rem; 
        margin: 1.5rem 0;
        border-left: 5px solid #667eea; 
        line-height: 1.8; 
        font-style: italic;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.05);
        position: relative;
    }
    
    .lead-msg::before {
        content: '"';
        position: absolute;
        top: -10px;
        left: 10px;
        font-size: 4rem;
        color: #667eea;
        opacity: 0.2;
    }
    
    /* Profile Badge */
    .profile-badge {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: 900;
        color: white;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        flex-shrink: 0;
    }
    
    /* Enhanced Message Cards */
    .message-card-all {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(20px);
        padding: 2.5rem; 
        border-radius: 25px; 
        margin-bottom: 2rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        transition: all 0.4s ease;
        border: 2px solid transparent;
    }
    
    .message-card-all:hover {
        border-color: #667eea;
        transform: translateX(10px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
    }
    
    /* Enhanced Status Badges */
    .status-badge {
        display: inline-flex; 
        align-items: center; 
        gap: 0.5rem; 
        padding: 0.7rem 1.5rem;
        border-radius: 30px; 
        font-size: 0.9rem; 
        font-weight: 700;
        text-transform: uppercase; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        letter-spacing: 1px;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(-20px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .status-success { 
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white !important;
    }
    
    .status-ready { 
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        color: white !important;
    }
    
    .status-sent { 
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white !important;
    }
    
    .status-pending { 
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white !important;
    }
    
    .status-converted {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white !important;
    }
    
    .status-replied {
        background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
        color: white !important;
    }
    
    /* Streamlit Overrides */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        transform: translateY(-2px);
    }
    
    .stTextInput>div>div>input, .stSelectbox>div>div, .stDateInput>div>div, .stTextArea>div>div>textarea {
        border-radius: 12px;
        border: 2px solid #ccc;
        padding: 0.5rem 1rem;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        background: rgba(255, 255, 255, 0.9);
        color: #333;
        transition: all 0.3s ease;
        padding: 0.5rem 1.5rem;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #667eea;
        color: white;
        border-bottom: none;
        box-shadow: 0 -4px 10px rgba(0,0,0,0.1);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .css-1d391kg .stButton>button {
        background: #f0f2f6;
        color: #333;
        box-shadow: none;
        border: 1px solid #ddd;
    }
    
    .css-1d391kg .stButton>button:hover {
        background: #e0e2e6;
        transform: none;
    }
    
    /* Toast/Notification */
    .st-emotion-cache-1c7v05j { /* Targeting the toast container */
        background-color: #667eea !important;
        color: white !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    
    .st-emotion-cache-1c7v05j * {
        color: white !important;
    }
    
    /* Chart Containers */
    .stPlotlyChart {
        border-radius: 25px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    /* Custom Icon Styles */
    .icon-large {
        font-size: 2rem;
        margin-right: 0.5rem;
        color: #667eea;
    }
    
    /* Custom Card Header */
    .card-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #eee;
    }
    
    .card-header h3 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #333;
        margin: 0;
    }
    
    /* Habit Tracker Styles */
    .habit-card {
        border-left: 6px solid #10b981;
    }
    
    .habit-card:hover {
        border-left-width: 8px;
    }
    
    .habit-title {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .habit-day-checked {
        background-color: #10b981;
        color: white;
        border-radius: 50%;
        width: 35px;
        height: 35px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        margin: 5px;
        box-shadow: 0 4px 8px rgba(16, 185, 129, 0.4);
    }
    
    .habit-day-unchecked {
        background-color: #f0f0f0;
        color: #333;
        border-radius: 50%;
        width: 35px;
        height: 35px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 500;
        margin: 5px;
        border: 1px solid #ddd;
    }
    
    .stProgress > div > div > div > div {
        background-color: #10b981;
    }
    
</style>
""", unsafe_allow_html=True)

# ==================== UTILITY FUNCTIONS ==================== #

def get_gsheets_client():
    """Initializes and returns the gspread client."""
    if st.session_state.gsheets_client is None:
        try:
            # Use st.secrets for credentials
            creds_json = st.secrets["gcp_service_account"]
            
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            
            # Create credentials object
            creds = Credentials.from_service_account_info(creds_json, scopes=scope)
            
            # Authorize the client
            client = gspread.authorize(creds)
            st.session_state.gsheets_client = client
            st.session_state.authenticated = True
            st.toast("✅ Google Sheets client authenticated successfully!", icon="🔑")
            return client
        except Exception as e:
            st.error(f"Authentication Error: {e}")
            st.session_state.authenticated = False
            return None
    return st.session_state.gsheets_client

def load_data_from_gsheets(spreadsheet_id, sheet_name, use_cache=True):
    """Loads data from a Google Sheet into a pandas DataFrame."""
    client = get_gsheets_client()
    if client is None:
        return pd.DataFrame()
    
    # Simple caching mechanism
    if use_cache and (spreadsheet_id, sheet_name) in st.session_state.sheets_data:
        return st.session_state.sheets_data[(spreadsheet_id, sheet_name)]

    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Store in cache
        if st.session_state.sheets_data is None:
            st.session_state.sheets_data = {}
        st.session_state.sheets_data[(spreadsheet_id, sheet_name)] = df
        
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet with ID '{spreadsheet_id}' not found.")
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Worksheet '{sheet_name}' not found in spreadsheet ID '{spreadsheet_id}'.")
    except Exception as e:
        st.error(f"An error occurred while loading data: {e}")
    
    return pd.DataFrame()

def load_leads_data(spreadsheet_id, sheet_gid, use_cache=True):
    """Loads leads data from a Google Sheet using the GID for CSV export."""
    client = get_gsheets_client()
    if client is None:
        return pd.DataFrame()

    # Simple caching mechanism
    if use_cache and (spreadsheet_id, sheet_gid) in st.session_state.leads_sheets_data:
        return st.session_state.leads_sheets_data[(spreadsheet_id, sheet_gid)]

    try:
        # Construct the export URL for the specific sheet (GID) as CSV
        export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={sheet_gid}"
        
        # Use gspread to get the spreadsheet title for logging/error messages
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Use requests to download the CSV content
        response = requests.get(export_url)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        # Read the CSV content directly into a pandas DataFrame
        df = pd.read_csv(BytesIO(response.content))
        
        # Store in cache
        if st.session_state.leads_sheets_data is None:
            st.session_state.leads_sheets_data = {}
        st.session_state.leads_sheets_data[(spreadsheet_id, sheet_gid)] = df

        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Leads Spreadsheet with ID '{spreadsheet_id}' not found.")
    except requests.exceptions.RequestException as e:
        st.error(f"Network or download error for leads data: {e}")
    except Exception as e:
        st.error(f"An error occurred while loading leads data: {e}")
    
    return pd.DataFrame()

def save_data_to_gsheets(df, spreadsheet_id, sheet_name):
    """Saves a pandas DataFrame to a Google Sheet."""
    client = get_gsheets_client()
    if client is None:
        return False
    
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Clear existing data and write new data including headers
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.toast(f"✅ Data saved successfully to {sheet_name}!", icon="💾")
        return True
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet with ID '{spreadsheet_id}' not found for saving.")
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Worksheet '{sheet_name}' not found for saving.")
    except Exception as e:
        st.error(f"An error occurred while saving data: {e}")
    
    return False

def add_log_entry(message):
    """Adds a message to the activity log and displays a toast notification."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.activity_log.append(log_entry)
    if st.session_state.show_notifications:
        st.toast(message, icon="🔔")

def get_profile_initials(name):
    """Generates initials from a name for the profile badge."""
    return "".join(word[0].upper() for word in name.split() if word).ljust(2, ' ')[0:2]

def get_status_badge(status):
    """Returns the HTML for a styled status badge."""
    status_map = {
        "Connected": ("status-success", "🤝"),
        "Sent": ("status-sent", "✉️"),
        "Pending": ("status-pending", "⏳"),
        "Replied": ("status-replied", "💬"),
        "Converted": ("status-converted", "💰"),
        "Ready": ("status-ready", "✅")
    }
    
    css_class, icon = status_map.get(status, ("status-pending", "❓"))
    
    return f"""
    <div class="{css_class} status-badge">
        {icon} {status}
    </div>
    """

def get_message_history(df, contact_url):
    """Filters the chat DataFrame for a specific contact and formats the history."""
    history_df = df[df['Contact_URL'] == contact_url].sort_values(by='Timestamp', ascending=True)
    
    history_html = ""
    for index, row in history_df.iterrows():
        sender = row['Sender_Name']
        message = row['Message_Content']
        timestamp = row['Timestamp']
        
        # Determine if the message is from 'Me' (the user's profile)
        is_me = sender == MY_PROFILE["name"]
        
        # Simple markdown to HTML conversion for messages
        message_html = message.replace('\n', '<br>')
        
        # Style the message based on sender
        if is_me:
            # Outgoing message (Blue/Purple)
            style = """
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white !important;
                border-radius: 20px 20px 5px 20px;
                align-self: flex-end;
                text-align: right;
            """
            sender_name = "You"
        else:
            # Incoming message (Light Gray)
            style = """
                background: #f0f2f6;
                color: #333 !important;
                border-radius: 20px 20px 20px 5px;
                align-self: flex-start;
                text-align: left;
            """
            sender_name = sender
            
        history_html += f"""
        <div style="display: flex; justify-content: {'flex-end' if is_me else 'flex-start'}; margin-bottom: 1rem;">
            <div style="max-width: 70%; padding: 1rem 1.5rem; {style} box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <small style="opacity: 0.8; font-size: 0.75rem; color: {'#ddd' if is_me else '#666'} !important;">{sender_name} - {timestamp}</small>
                <p style="margin: 0; font-size: 0.95rem; line-height: 1.4; color: {'white' if is_me else '#333'} !important;">{message_html}</p>
            </div>
        </div>
        """
    
    if not history_html:
        return "<p style='text-align: center; color: #999;'>No message history found for this contact.</p>"
        
    return history_html

@st.cache_data(ttl=60)
def load_daily_tracker_data(client):
    """Loads and processes the daily activity tracker data."""
    if client:
        try:
            spreadsheet = client.open_by_key(DAILY_TRACKER_SHEET_ID)
            try:
                worksheet = spreadsheet.worksheet(DAILY_TRACKER_SHEET_NAME)
            except gspread.exceptions.WorksheetNotFound:
                st.warning(f"Daily tracker worksheet '{DAILY_TRACKER_SHEET_NAME}' not found. Attempting to load the first worksheet.")
                worksheet = spreadsheet.sheet1 # Fallback to the first sheet

            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            # Ensure numeric types for calculations
            for col in ['Connections_Sent', 'Messages_Sent', 'Follow_ups_Sent', 'Responses_Received', 'Leads_Converted']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            # Ensure 'Date' column is in datetime format for filtering
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime("%Y-%m-%d")
            return df
        except Exception as e:
            st.error(f"🔴 Error loading daily tracker: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=60)
def get_daily_summary(df):
    """Calculates summary statistics from the daily tracker data."""
    if df.empty:
        return {}
    
    # Calculate totals
    total_connections = df['Connections_Sent'].sum()
    total_messages = df['Messages_Sent'].sum()
    total_followups = df['Follow_ups_Sent'].sum()
    total_responses = df['Responses_Received'].sum()
    total_leads = df['Leads_Converted'].sum()
    
    # Calculate averages
    days_tracked = df.shape[0]
    avg_connections = total_connections / days_tracked if days_tracked > 0 else 0
    avg_messages = total_messages / days_tracked if days_tracked > 0 else 0
    
    # Calculate conversion rate
    total_outreach = total_connections + total_messages + total_followups
    conversion_rate = (total_leads / total_outreach) * 100 if total_outreach > 0 else 0
    response_rate = (total_responses / total_outreach) * 100 if total_outreach > 0 else 0
    
    # Get last 7 days data
    last_7_days = df.tail(7)
    last_7_connections = last_7_days['Connections_Sent'].sum()
    last_7_leads = last_7_days['Leads_Converted'].sum()
    
    return {
        "total_connections": total_connections,
        "total_messages": total_messages,
        "total_followups": total_followups,
        "total_responses": total_responses,
        "total_leads": total_leads,
        "days_tracked": days_tracked,
        "avg_connections": avg_connections,
        "avg_messages": avg_messages,
        "conversion_rate": conversion_rate,
        "response_rate": response_rate,
        "last_7_connections": last_7_connections,
        "last_7_leads": last_7_leads,
        "df": df
    }

def get_daily_goal_progress(df, goals):
    """Calculates the progress towards daily goals."""
    if df.empty:
        return {}
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_data = df[df['Date'] == today_date]
    
    progress = {}
    
    for goal_name, goal_value in goals.items():
        current_value = today_data[goal_name].iloc[0] if not today_data.empty and goal_name in today_data.columns else 0
        
        # Calculate percentage
        percent = (current_value / goal_value) * 100 if goal_value > 0 else 0
        percent = min(percent, 100) # Cap at 100%
        
        progress[goal_name] = {
            "current": current_value,
            "goal": goal_value,
            "percent": percent
        }
        
    return progress

# ==================== WEBHOOK & CRM FUNCTIONS ==================== #

def send_webhook_payload(payload):
    """Sends a payload to the external webhook URL."""
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers, timeout=10)
        response.raise_for_status()
        
        # Log the successful webhook
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "status": "Success",
            "payload_hash": hashlib.sha256(json.dumps(payload).encode('utf-8')).hexdigest()[:8],
            "response_status": response.status_code,
            "response_text": response.text[:100] # Truncate response for log
        }
        st.session_state.webhook_history.append(log_entry)
        add_log_entry(f"Webhook sent successfully! Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        error_message = f"Webhook failed: {e}"
        st.error(error_message)
        
        # Log the failed webhook
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "status": "Failed",
            "payload_hash": hashlib.sha256(json.dumps(payload).encode('utf-8')).hexdigest()[:8],
            "response_status": getattr(e.response, 'status_code', 'N/A'),
            "response_text": str(e)
        }
        st.session_state.webhook_history.append(log_entry)
        add_log_entry(error_message)
        return False

def create_lead_payload(row):
    """Creates a standard lead payload from a DataFrame row."""
    # Ensure all keys exist in the payload, even if values are empty
    payload = {
        "Contact_Name": row.get('Contact_Name', ''),
        "Contact_URL": row.get('Contact_URL', ''),
        "Status": row.get('Status', 'Pending'),
        "Last_Message_Date": row.get('Last_Message_Date', datetime.now().strftime("%Y-%m-%d")),
        "Company": row.get('Company', ''),
        "Title": row.get('Title', ''),
        "Location": row.get('Location', ''),
        "Email": row.get('Email', ''),
        "Phone": row.get('Phone', ''),
        "Notes": st.session_state.notes.get(row.get('Contact_URL', ''), ''),
        "Tags": ", ".join(st.session_state.tags.get(row.get('Contact_URL', ''), [])),
        "Source": "LinkedIn CRM App"
    }
    return payload

def update_lead_status(contact_url, new_status):
    """Updates the status of a lead in the leads database and sends a webhook."""
    
    # 1. Update the local leads_database DataFrame
    df = st.session_state.leads_database.copy()
    if 'Contact_URL' in df.columns:
        # Find the row index for the contact
        idx = df[df['Contact_URL'] == contact_url].index
        
        if not idx.empty:
            # Update the status
            df.loc[idx, 'Status'] = new_status
            
            # Update the local session state
            st.session_state.leads_database = df
            
            # 2. Prepare and send the webhook payload
            lead_row = df.loc[idx].iloc[0]
            payload = create_lead_payload(lead_row)
            payload['Status'] = new_status # Ensure the new status is in the payload
            send_webhook_payload(payload)
            
            # 3. Save the updated DataFrame back to Google Sheets (optional, can be done less frequently)
            # save_data_to_gsheets(df, LEADS_DATABASE_SHEET_ID, LEADS_SHEET_NAME) 
            
            add_log_entry(f"Status for {lead_row.get('Contact_Name', 'Lead')} updated to {new_status}")
            return True
        else:
            st.warning(f"Could not find lead with URL: {contact_url}")
            return False
    else:
        st.error("Leads database is missing 'Contact_URL' column.")
        return False

# ==================== DATA PROCESSING & VISUALIZATION ==================== #

def process_outreach_data(df):
    """Cleans and processes the outreach tracking data."""
    if df.empty:
        return df
    
    # Rename columns for consistency (if necessary, based on the actual CSV structure)
    df.columns = df.columns.str.replace('[^A-Za-z0-9_]+', '', regex=True)
    
    # Convert 'Date' column to datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Date'], inplace=True)
        df['Date'] = df['Date'].dt.date # Keep only the date part
    
    # Standardize column names for tracking metrics (assuming these exist)
    # This is a placeholder and should be adjusted based on the actual CSV columns
    required_cols = ['Contact_Name', 'Contact_URL', 'Status', 'Last_Message_Date']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''
            
    # Clean up status column (e.g., if it contains extra text)
    if 'Status' in df.columns:
        df['Status'] = df['Status'].astype(str).str.strip()
    
    return df

def process_chat_data(df):
    """Cleans and processes the chat history data."""
    if df.empty:
        return df
    
    # Rename columns for consistency
    df.columns = df.columns.str.replace('[^A-Za-z0-9_]+', '', regex=True)
    
    # Convert 'Timestamp' to datetime
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df.dropna(subset=['Timestamp'], inplace=True)
        
    # Standardize 'Sender_Name'
    if 'Sender_Name' in df.columns:
        df['Sender_Name'] = df['Sender_Name'].astype(str).str.strip()
        
    return df

def create_status_pie_chart(df):
    """Creates a Plotly pie chart for lead status distribution."""
    if df.empty:
        return go.Figure()
        
    status_counts = df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    # Define a color map for statuses
    color_map = {
        'Connected': '#10b981', # Green
        'Sent': '#3b82f6',      # Blue
        'Pending': '#f59e0b',   # Yellow/Orange
        'Replied': '#ec4899',   # Pink
        'Converted': '#8b5cf6', # Purple
        'Ready': '#22c55e'      # Light Green
    }
    
    # Assign colors based on the map, falling back to a default color
    colors = [color_map.get(status, '#94a3b8') for status in status_counts['Status']]
    
    fig = px.pie(
        status_counts, 
        values='Count', 
        names='Status', 
        title='Lead Status Distribution',
        color='Status',
        color_discrete_map=color_map,
        hole=0.4
    )
    
    fig.update_traces(textinfo='percent+label', pull=[0.05] * len(status_counts))
    fig.update_layout(
        margin=dict(t=50, b=0, l=0, r=0),
        legend_title_text='Status',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#333"),
        title_font_color="#333",
        title_font_size=20,
    )
    
    return fig

def create_daily_activity_chart(df):
    """Creates a Plotly bar chart for daily activity metrics."""
    if df.empty:
        return go.Figure()
        
    # Melt the DataFrame to long format for Plotly
    metrics = ['Connections_Sent', 'Messages_Sent', 'Follow_ups_Sent', 'Responses_Received', 'Leads_Converted']
    df_melt = df.melt(id_vars=['Date'], value_vars=metrics, var_name='Metric', value_name='Count')
    
    # Define a color map for metrics
    metric_colors = {
        'Connections_Sent': '#667eea',
        'Messages_Sent': '#764ba2',
        'Follow_ups_Sent': '#ec4899',
        'Responses_Received': '#f59e0b',
        'Leads_Converted': '#10b981'
    }

    fig = px.bar(
        df_melt, 
        x='Date', 
        y='Count', 
        color='Metric', 
        title='Daily Outreach Activity Over Time',
        color_discrete_map=metric_colors,
        barmode='group',
        height=450
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Count",
        legend_title_text='Activity Type',
        plot_bgcolor='rgba(240,240,240,1)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#333"),
        title_font_color="#333",
        xaxis={'categoryorder':'category ascending'},
        hovermode="x unified"
    )
    
    return fig

def create_conversion_funnel(summary):
    """Creates a Plotly funnel chart for the conversion pipeline."""
    if not summary:
        return go.Figure()

    # Define the steps and values
    steps = ["Outreach Sent", "Responses Received", "Leads Converted"]
    outreach_sent = summary.get('total_connections', 0) + summary.get('total_messages', 0) + summary.get('total_followups', 0)
    values = [
        outreach_sent,
        summary.get('total_responses', 0),
        summary.get('total_leads', 0)
    ]
    
    # Filter out zero values to prevent errors in the chart
    data = [(s, v) for s, v in zip(steps, values) if v > 0]
    if not data:
        return go.Figure()
        
    steps, values = zip(*data)
    
    colors = ['#667eea', '#f59e0b', '#10b981']
    
    fig = go.Figure(data=[
        go.Funnel(
            y=list(steps),
            x=list(values),
            textinfo="value+percent initial",
            marker={"color": colors[:len(steps)]},
            connector={"line": {"color": "gray", "dash": "dot", "width": 2}}
        )
    ])
    
    fig.update_layout(
        title='Outreach to Conversion Funnel',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#333"),
        title_font_color="#333",
        height=450,
        margin=dict(t=50, b=0, l=50, r=50)
    )
    
    return fig

# ==================== MAIN APP LAYOUT ==================== #

def main_app():
    """The main function to run the Streamlit application."""
    
    # --- 1. Authentication and Data Loading ---
    client = get_gsheets_client()
    
    # Initialize data caches if they don't exist
    if st.session_state.sheets_data is None:
        st.session_state.sheets_data = {}
    if st.session_state.leads_sheets_data is None:
        st.session_state.leads_sheets_data = {}

    # Load data
    with st.spinner("Loading data from Google Sheets..."):
        # Load chat history
        chat_df_raw = load_data_from_gsheets(CHAT_SPREADSHEET_ID, CHAT_SHEET_NAME, use_cache=st.session_state.auto_refresh)
        st.session_state.chat_df = process_chat_data(chat_df_raw)
        
        # Load leads database (CRM)
        leads_df_raw = load_leads_data(LEADS_DATABASE_SHEET_ID, LEADS_SHEET_GID, use_cache=st.session_state.auto_refresh)
        st.session_state.leads_database = process_outreach_data(leads_df_raw)
        
        # Load daily tracker
        st.session_state.daily_tracker = load_daily_tracker_data(client)
    
    # --- 2. Sidebar and Configuration ---
    with st.sidebar:
        st.markdown(f'<h3 style="color:#667eea; font-weight:800;">{MY_PROFILE["name"]}</h3>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:0.9rem; margin-top:-10px;"><a href="{MY_PROFILE["url"]}" target="_blank" style="color:#764ba2;">View LinkedIn Profile</a></p>', unsafe_allow_html=True)
        
        st.header("App Settings")
        
        # Multi-page navigation (simple version)
        st.session_state.current_page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "💬 CRM & Messaging", "📊 Daily Tracker", "⚙️ Integrations & Logs"],
            index=["🏠 Dashboard", "💬 CRM & Messaging", "📊 Daily Tracker", "⚙️ Integrations & Logs"].index(st.session_state.current_page)
        )
        
        st.subheader("Data Management")
        st.session_state.auto_refresh = st.checkbox("Auto-refresh data", value=st.session_state.auto_refresh)
        if st.session_state.auto_refresh:
            st.session_state.refresh_interval = st.slider("Refresh interval (seconds)", 30, 300, st.session_state.refresh_interval, 30)
        
        if st.button("Manual Refresh Data", use_container_width=True):
            st.session_state.sheets_data = None # Clear cache
            st.session_state.leads_sheets_data = None # Clear cache
            st.session_state.last_refresh = datetime.utcnow()
            st.rerun()
            
        st.subheader("UI Settings")
        st.session_state.show_notifications = st.checkbox("Show Toast Notifications", value=st.session_state.show_notifications)
        # st.session_state.dark_mode = st.checkbox("Dark Mode (Experimental)", value=st.session_state.dark_mode)
        
        st.markdown("---")
        st.caption(f"Last Data Refresh: {st.session_state.last_refresh.strftime('%H:%M:%S UTC')}")
        st.caption("Powered by Streamlit & Google Sheets")

    # --- 3. Main Content Rendering ---
    
    st.markdown(f'<h1 class="main-title">{st.session_state.current_page}</h1>', unsafe_allow_html=True)
    
    if st.session_state.current_page == "🏠 Dashboard":
        render_dashboard()
    elif st.session_state.current_page == "💬 CRM & Messaging":
        render_crm()
    elif st.session_state.current_page == "📊 Daily Tracker":
        render_daily_tracker()
    elif st.session_state.current_page == "⚙️ Integrations & Logs":
        render_integrations_logs()
        
    # --- 4. Auto-refresh logic ---
    if st.session_state.auto_refresh:
        time.sleep(st.session_state.refresh_interval)
        st.rerun()

# ==================== PAGE RENDERERS ==================== #

def render_dashboard():
    """Renders the main dashboard page."""
    
    # --- Data Summary ---
    daily_summary = get_daily_summary(st.session_state.daily_tracker)
    
    if not daily_summary:
        st.warning("No daily tracker data found to display the dashboard. Please check your Google Sheet configuration.")
        return
        
    st.markdown('<p class="sub-title">Key Performance Indicators & Conversion Metrics</p>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🤝</div>
            <div class="metric-value">{daily_summary.get('total_connections', 0):,}</div>
            <div class="metric-label">Connections Sent</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✉️</div>
            <div class="metric-value">{daily_summary.get('total_messages', 0) + daily_summary.get('total_followups', 0):,}</div>
            <div class="metric-label">Total Messages</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">💬</div>
            <div class="metric-value">{daily_summary.get('total_responses', 0):,}</div>
            <div class="metric-label">Responses Received</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">💰</div>
            <div class="metric-value">{daily_summary.get('total_leads', 0):,}</div>
            <div class="metric-label">Leads Converted</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📈</div>
            <div class="metric-value">{daily_summary.get('conversion_rate', 0):.2f}%</div>
            <div class="metric-label">Conversion Rate</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # --- Charts ---
    chart_col1, chart_col2 = st.columns([2, 1])
    
    with chart_col1:
        st.subheader("Activity Trends")
        st.plotly_chart(create_daily_activity_chart(daily_summary['df']), use_container_width=True)
        
    with chart_col2:
        st.subheader("Conversion Pipeline")
        st.plotly_chart(create_conversion_funnel(daily_summary), use_container_width=True)
        
    st.markdown("---")
    
    # --- Leads and Statuses ---
    st.subheader("Lead Status Overview")
    
    lead_col1, lead_col2 = st.columns([1, 2])
    
    with lead_col1:
        st.plotly_chart(create_status_pie_chart(st.session_state.leads_database), use_container_width=True)
        
    with lead_col2:
        st.subheader("Top 5 Recent Conversations")
        
        # Merge chat and leads data to get contact details
        if not st.session_state.chat_df.empty and not st.session_state.leads_database.empty:
            # Get the latest message for each contact
            latest_messages = st.session_state.chat_df.sort_values('Timestamp', ascending=False).drop_duplicates(subset=['Contact_URL'])
            
            # Filter out messages sent by 'Me' to focus on replies/conversations
            latest_replies = latest_messages[latest_messages['Sender_Name'] != MY_PROFILE["name"]]
            
            # Join with leads data to get status and other info
            recent_conversations = latest_replies.merge(
                st.session_state.leads_database[['Contact_URL', 'Status', 'Contact_Name', 'Title', 'Company']],
                on='Contact_URL',
                how='left'
            ).head(5)
            
            if not recent_conversations.empty:
                for index, row in recent_conversations.iterrows():
                    # Check if the contact is in the leads database
                    if pd.notna(row['Contact_Name']):
                        with st.container(border=False):
                            col_icon, col_content = st.columns([0.5, 3])
                            
                            with col_icon:
                                initials = get_profile_initials(row['Contact_Name'])
                                st.markdown(f'<div class="profile-badge">{initials}</div>', unsafe_allow_html=True)
                                
                            with col_content:
                                st.markdown(f'<p style="font-size:1.1rem; font-weight:700; margin-bottom:0;">{row["Contact_Name"]}</p>', unsafe_allow_html=True)
                                st.markdown(f'<p style="font-size:0.85rem; margin-top:0; color:#666;">{row["Title"]} at {row["Company"]}</p>', unsafe_allow_html=True)
                                st.markdown(get_status_badge(row['Status']), unsafe_allow_html=True)
                                
                            st.divider()
            else:
                st.info("No recent replies found in chat history.")
        else:
            st.info("Chat or Leads data is empty. Cannot display recent conversations.")
            
def render_crm():
    """Renders the CRM and Messaging page."""
    
    st.markdown('<p class="sub-title">Manage Leads, View Conversations, and Update Statuses</p>', unsafe_allow_html=True)
    
    # --- Filtering and Search ---
    
    col_search, col_status, col_sort = st.columns([3, 2, 1])
    
    with col_search:
        st.session_state.search_query = st.text_input("Search Leads (Name, Title, Company)", st.session_state.search_query, placeholder="e.g., John Doe, CEO, TechCorp")
        
    with col_status:
        status_options = ['all'] + st.session_state.leads_database['Status'].unique().tolist()
        st.session_state.filter_status = st.selectbox("Filter by Status", status_options, index=status_options.index(st.session_state.filter_status))
        
    with col_sort:
        sort_options = ['Last_Message_Date', 'Status', 'Contact_Name']
        st.session_state.sort_by = st.selectbox("Sort By", sort_options, index=sort_options.index(st.session_state.sort_by))

    # --- Apply Filters and Sort ---
    
    filtered_df = st.session_state.leads_database.copy()
    
    # Status filter
    if st.session_state.filter_status != 'all':
        filtered_df = filtered_df[filtered_df['Status'] == st.session_state.filter_status]
        
    # Search filter
    if st.session_state.search_query:
        search_term = st.session_state.search_query.lower()
        filtered_df = filtered_df[
            filtered_df['Contact_Name'].astype(str).str.lower().str.contains(search_term) |
            filtered_df['Title'].astype(str).str.lower().str.contains(search_term) |
            filtered_df['Company'].astype(str).str.lower().str.contains(search_term)
        ]
        
    # Sort
    filtered_df = filtered_df.sort_values(by=st.session_state.sort_by, ascending=False)
    
    # --- Layout ---
    
    lead_list_col, conversation_col = st.columns([1, 2])
    
    # --- Lead List ---
    with lead_list_col:
        st.subheader(f"Leads ({len(filtered_df)})")
        
        if filtered_df.empty:
            st.info("No leads match the current filters.")
        else:
            # Display lead cards
            for index, row in filtered_df.iterrows():
                contact_url = row['Contact_URL']
                
                # Check if this is the currently selected contact
                is_selected = st.session_state.selected_contact == contact_url
                
                # Create a clickable container using a button-like structure
                style = """
                    cursor: pointer; 
                    padding: 1rem; 
                    border-radius: 10px; 
                    margin-bottom: 0.5rem; 
                    transition: all 0.2s;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                """
                if is_selected:
                    style += "background-color: #e6e9f0; border: 2px solid #667eea;"
                else:
                    style += "background-color: #f8f8f8; border: 1px solid #eee;"
                
                # Use a unique key for the button/container to make it clickable
                if st.button(
                    key=f"select_lead_{contact_url}",
                    label=f"""
                        <div style="{style}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="font-weight: 700; color: #333; font-size: 1rem;">{row['Contact_Name']}</div>
                                <div style="font-size: 0.75rem; color: #999;">{row['Last_Message_Date']}</div>
                            </div>
                            <div style="font-size: 0.85rem; color: #666;">{row['Title']} at {row['Company']}</div>
                            <div style="margin-top: 0.5rem;">{get_status_badge(row['Status'])}</div>
                        </div>
                    """,
                    use_container_width=True,
                    unsafe_allow_html=True
                ):
                    st.session_state.selected_contact = contact_url
                    st.rerun() # Rerun to update the conversation column
                    
    # --- Conversation View ---
    with conversation_col:
        
        if st.session_state.selected_contact:
            # Get the selected lead's data
            selected_lead = filtered_df[filtered_df['Contact_URL'] == st.session_state.selected_contact].iloc[0]
            
            st.markdown(f'<h2 class="lead-title">{selected_lead["Contact_Name"]}</h2>', unsafe_allow_html=True)
            st.markdown(f'<p class="lead-sub">{selected_lead["Title"]} at {selected_lead["Company"]}</p>', unsafe_allow_html=True)
            
            # Tabs for Conversation, Details, and Actions
            tab_conv, tab_details, tab_actions = st.tabs(["Conversation", "Details", "Actions"])
            
            with tab_conv:
                # Display message history
                history_html = get_message_history(st.session_state.chat_df, st.session_state.selected_contact)
                st.markdown(f"""
                <div style="height: 500px; overflow-y: auto; background-color: white; padding: 1.5rem; border-radius: 15px; box-shadow: inset 0 0 10px rgba(0,0,0,0.05);">
                    {history_html}
                </div>
                """, unsafe_allow_html=True)
                
            with tab_details:
                st.subheader("Contact Information")
                st.json(selected_lead.to_dict())
                
                st.subheader("Notes")
                current_notes = st.session_state.notes.get(st.session_state.selected_contact, "")
                new_notes = st.text_area("Edit Notes", current_notes, height=150)
                if new_notes != current_notes:
                    st.session_state.notes[st.session_state.selected_contact] = new_notes
                    add_log_entry(f"Notes updated for {selected_lead['Contact_Name']}")
                    st.rerun()
                    
            with tab_actions:
                st.subheader("Update Lead Status")
                
                current_status = selected_lead['Status']
                new_status = st.selectbox(
                    "Select New Status", 
                    ['Connected', 'Sent', 'Pending', 'Replied', 'Converted', 'Ready'],
                    index=['Connected', 'Sent', 'Pending', 'Replied', 'Converted', 'Ready'].index(current_status)
                )
                
                if st.button("Update Status and Send Webhook", use_container_width=True):
                    if new_status != current_status:
                        update_lead_status(st.session_state.selected_contact, new_status)
                        st.rerun()
                    else:
                        st.warning("Status is already set to this value.")
                        
                st.subheader("Manual Webhook Test")
                if st.button("Send Test Webhook for this Lead", use_container_width=True):
                    payload = create_lead_payload(selected_lead)
                    send_webhook_payload(payload)
                    
        else:
            st.info("Select a lead from the list to view the conversation and details.")

def render_daily_tracker():
    """Renders the daily activity tracker page."""
    
    st.markdown('<p class="sub-title">Track Your Daily Outreach Goals and Progress</p>', unsafe_allow_html=True)
    
    # --- Daily Goals Configuration ---
    st.subheader("Daily Goals")
    
    # Define default goals (can be moved to st.session_state for persistence)
    daily_goals = {
        'Connections_Sent': 20,
        'Messages_Sent': 50,
        'Follow_ups_Sent': 15,
        'Responses_Received': 5,
        'Leads_Converted': 1
    }
    
    # Display goals in an expander for editing
    with st.expander("Edit Daily Goals", expanded=False):
        col_g1, col_g2, col_g3, col_g4, col_g5 = st.columns(5)
        
        daily_goals['Connections_Sent'] = col_g1.number_input("Connections Sent Goal", min_value=0, value=daily_goals['Connections_Sent'], step=1)
        daily_goals['Messages_Sent'] = col_g2.number_input("Messages Sent Goal", min_value=0, value=daily_goals['Messages_Sent'], step=1)
        daily_goals['Follow_ups_Sent'] = col_g3.number_input("Follow-ups Sent Goal", min_value=0, value=daily_goals['Follow_ups_Sent'], step=1)
        daily_goals['Responses_Received'] = col_g4.number_input("Responses Received Goal", min_value=0, value=daily_goals['Responses_Received'], step=1)
        daily_goals['Leads_Converted'] = col_g5.number_input("Leads Converted Goal", min_value=0, value=daily_goals['Leads_Converted'], step=1)
        
    # --- Today's Progress ---
    st.subheader("Today's Progress")
    
    if st.session_state.daily_tracker.empty:
        st.warning("Daily tracker data is empty. Cannot calculate today's progress.")
        return
        
    progress = get_daily_goal_progress(st.session_state.daily_tracker, daily_goals)
    
    cols_p = st.columns(5)
    
    for i, (metric, data) in enumerate(progress.items()):
        with cols_p[i]:
            st.markdown(f"""
            <div class="metric-card" style="padding: 1.5rem;">
                <div style="font-weight: 700; color: #333; font-size: 1.1rem; margin-bottom: 0.5rem;">{metric.replace('_', ' ')}</div>
                <div style="font-size: 2rem; font-weight: 900; color: #667eea;">{data['current']} / {data['goal']}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(data['percent'] / 100)
            
    st.markdown("---")
    
    # --- Daily Activity Table ---
    st.subheader("Daily Activity Log")
    
    # Display the daily tracker data
    st.dataframe(
        st.session_state.daily_tracker.sort_values(by='Date', ascending=False), 
        use_container_width=True,
        height=400
    )
    
    # --- Data Export ---
    csv = st.session_state.daily_tracker.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Daily Tracker Data as CSV",
        data=csv,
        file_name='daily_tracker_export.csv',
        mime='text/csv',
        use_container_width=True
    )

def render_integrations_logs():
    """Renders the integrations and activity logs page."""
    
    st.markdown('<p class="sub-title">Monitor Webhook Activity and Application Logs</p>', unsafe_allow_html=True)
    
    tab_webhook, tab_logs = st.tabs(["Webhook History", "Activity Log"])
    
    with tab_webhook:
        st.subheader("Webhook Integration Test")
        
        col_url, col_test = st.columns([3, 1])
        col_url.text_input("Webhook URL", WEBHOOK_URL, disabled=True)
        
        with st.expander("Edit Test Payload", expanded=False):
            st.session_state.webhook_test_payload = st.text_area(
                "JSON Payload", 
                st.session_state.webhook_test_payload, 
                height=200
            )
            
        if col_test.button("Send Custom Test Webhook", use_container_width=True):
            try:
                payload = json.loads(st.session_state.webhook_test_payload)
                send_webhook_payload(payload)
            except json.JSONDecodeError:
                st.error("Invalid JSON payload.")
            
        st.markdown("---")
        st.subheader("Recent Webhook Transactions")
        
        if st.session_state.webhook_history:
            # Convert history to DataFrame for easy display
            webhook_df = pd.DataFrame(st.session_state.webhook_history).sort_values(by='timestamp', ascending=False)
            st.dataframe(webhook_df, use_container_width=True)
        else:
            st.info("No webhook transactions recorded yet.")
            
    with tab_logs:
        st.subheader("Application Activity Log")
        
        if st.session_state.activity_log:
            # Display log in reverse chronological order
            log_text = "\n".join(st.session_state.activity_log[::-1])
            st.text_area("Log Entries", log_text, height=500)
        else:
            st.info("No activity logged yet.")

# ==================== RUN APP ==================== #

if __name__ == "__main__":
    main_app()
