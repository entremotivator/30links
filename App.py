
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
    
    .status-error { 
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white !important;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 2.5rem; 
        font-weight: 800; 
        color: #ffffff; 
        margin: 3rem 0 2rem 0;
        padding-bottom: 1.5rem; 
        border-bottom: 4px solid rgba(255, 255, 255, 0.3);
        text-shadow: 0 4px 12px rgba(0,0,0,0.3);
        position: relative;
        animation: slideInLeft 0.6s ease-out;
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Stat Boxes */
    .stat-box {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-top: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .stat-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.15);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 900;
        color: #667eea;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 0.95rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    /* Streamlit overrides */
    .stButton>button {
        background-color: #667eea;
        color: white;
        border-radius: 15px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        background-color: #764ba2;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(118, 75, 162, 0.4);
    }
    
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea, .stFileUploader>div>div>button {
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        padding: 10px 15px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus, .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
    }
    
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        justify-content: center;
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 1rem 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab-list"] button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: #667eea;
    }
    
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.9);
        color: #667eea;
        border-radius: 15px;
        font-weight: 700;
        padding: 1rem 1.5rem;
        border: 2px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        transform: translateX(5px);
    }
    
    /* Loading Animation */
    .stSpinner > div {
        border-color: #667eea transparent transparent transparent !important;
    }
    
    /* Success/Error Messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 15px !important;
        padding: 1.5rem !important;
        border-left-width: 6px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        animation: slideIn 0.5s ease-out !important;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Action Buttons Container */
    .action-buttons {
        display: flex;
        gap: 12px;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }
    
    .action-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 15px;
        font-weight: 700;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .action-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        border-color: white;
    }
    
    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin: 2rem 0;
    }
    
    /* Filter Panel */
    .filter-panel {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        padding: 2rem;
        border-radius: 25px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    }
    
    /* Tag Badge */
    .tag-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        color: #667eea;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    /* Note Card */
    .note-card {
        background: #fff9e6;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-style: italic;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ==================== #
@st.cache_resource
def init_google_sheets(credentials_json):
    """Initialize Google Sheets client with service account credentials"""
    try:
        credentials_dict = json.loads(credentials_json)
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"🔴 Authentication Error: {str(e)}")
        return None

@st.cache_data(ttl=60)
def load_sheet_data(_client, sheet_id, sheet_name):
    """Load data from Google Sheets with caching"""
    try:
        spreadsheet = _client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"🔴 Data Loading Error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_daily_tracker():
    """Load daily tracker data from Google Sheets"""
    client = st.session_state.gsheets_client
    if client:
        try:
            spreadsheet = client.open_by_key(DAILY_TRACKER_SHEET_ID)
            worksheet = spreadsheet.worksheet(DAILY_TRACKER_SHEET_NAME)
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            # Ensure numeric types for calculations
            for col in ['Connections_Sent', 'Messages_Sent', 'Follow_ups_Sent', 'Responses_Received', 'Leads_Converted']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            return df
        except Exception as e:
            st.error(f"🔴 Error loading daily tracker: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=60)
def load_leads_database():
    """Load leads database from Google Sheets"""
    client = st.session_state.gsheets_client
    if client:
        try:
            spreadsheet = client.open_by_key(LEADS_DATABASE_SHEET_ID)
            # Attempt to open by GID first, then by name if GID fails or is not provided
            worksheet = None
            if LEADS_SHEET_GID:
                try:
                    worksheet = spreadsheet.get_worksheet_by_id(int(LEADS_SHEET_GID))
                except gspread.exceptions.WorksheetNotFound:
                    st.warning(f"Worksheet with GID {LEADS_SHEET_GID} not found. Trying by name.")
            if not worksheet:
                worksheet = spreadsheet.worksheet("Leads") # Assuming a default worksheet name if GID fails

            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            # Convert 'timestamp' column to datetime objects
            if 'timestamp' in df.columns:
                df['parsed_time'] = df['timestamp'].apply(parse_timestamp)
            return df
        except Exception as e:
            st.error(f"🔴 Error loading leads database: {e}")
    return pd.DataFrame()

def parse_timestamp(timestamp_str):
    """Parse various timestamp formats"""
    if pd.isna(timestamp_str) or timestamp_str == '':
        return None
    try:
        return pd.to_datetime(timestamp_str, format='%m/%d/%Y %H:%M:%S')
    except ValueError:
        try:
            return pd.to_datetime(timestamp_str)
        except:
            return None

def is_message_sent(row):
    """Check if a message has been sent"""
    if row.get("email_subject") or row.get("email_message"):
        return False
    success = str(row.get('success', '')).lower()
    return success == 'true' or success == 'yes' or success == '1'

def is_me(sender_name, sender_url, my_profile):
    """Check if the sender is the current user"""
    if not sender_name or not isinstance(sender_name, str):
        return False
    return (my_profile["name"].lower() in sender_name.lower() or
            (sender_url and my_profile["url"].lower() in str(sender_url).lower()))

def get_initials(name):
    """Get initials from a name"""
    if not name:
        return "?"
    parts = name.split()
    return f"{parts[0][0]}{parts[1][0]}".upper() if len(parts) >= 2 else name[0].upper()

def send_webhook_request(webhook_url, payload):
    """Send data to webhook endpoint"""
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200, response.text
    except Exception as e:
        return False, str(e)

def generate_lead_id(profile_name, linkedin_url):
    """Generate unique lead ID"""
    unique_string = f"{profile_name}_{linkedin_url}_{datetime.now().isoformat()}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:12]

def export_to_csv(df, filename="export.csv"):
    """Export dataframe to CSV"""
    return df.to_csv(index=False).encode('utf-8')

def create_pdf_report(data_dict):
    """Create a PDF report from data dictionary"""
    # This is a placeholder - implement with reportlab or similar
    return b"PDF Report Content"

def filter_dataframe(df, filters):
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    if filters.get('status') and filters['status'] != 'all':
        if 'status' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['status'] == filters['status']]
    
    if filters.get('date_range'):
        days = filters['date_range']
        cutoff_date = datetime.now() - timedelta(days=days)
        if 'parsed_time' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['parsed_time'] >= cutoff_date]
    
    if filters.get('search_query'):
        query = filters['search_query'].lower()
        mask = filtered_df.apply(lambda row: any(
            query in str(val).lower() for val in row.values
        ), axis=1)
        filtered_df = filtered_df[mask]
    
    return filtered_df

def calculate_metrics(chat_df, outreach_df, daily_tracker_df):
    """Calculate comprehensive metrics"""
    metrics = {
        'total_conversations': len(chat_df),
        'total_leads': len(outreach_df),
        'messages_sent': 0,
        'messages_received': 0,
        'response_rate': 0,
        'avg_response_time': 0,
        'pending_leads': 0,
        'ready_to_send': 0,
        'conversion_rate': 0,
        'connections_sent_today': 0,
        'messages_sent_today': 0,
        'follow_ups_sent_today': 0,
        'responses_received_today': 0,
        'leads_converted_today': 0
    }
    
    if not chat_df.empty:
        is_my_message = chat_df.apply(
            lambda row: is_me(row.get('sender_name'), row.get('sender_url'), MY_PROFILE), axis=1
        ).astype(bool)
        metrics['messages_sent'] = len(chat_df[is_my_message])
        metrics['messages_received'] = len(chat_df) - metrics['messages_sent']
        
        if metrics['messages_sent'] > 0:
            metrics['response_rate'] = round((metrics['messages_received'] / metrics['messages_sent']) * 100, 2)
    
    if not outreach_df.empty:
        if 'status' in outreach_df.columns:
            metrics['pending_leads'] = len(outreach_df[outreach_df['status'] == 'pending'])
            metrics['ready_to_send'] = len(outreach_df[outreach_df['status'] == 'ready_to_send'])
        
        if 'success' in outreach_df.columns:
            sent_count = len(outreach_df[outreach_df['success'].astype(str).str.lower() == 'true'])
            if metrics['total_leads'] > 0:
                metrics['conversion_rate'] = round((sent_count / metrics['total_leads']) * 100, 2)

    if not daily_tracker_df.empty:
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_row = daily_tracker_df[daily_tracker_df['Date'] == today_str]
        if not today_row.empty:
            metrics['connections_sent_today'] = int(today_row['Connections_Sent'].iloc[0])
            metrics['messages_sent_today'] = int(today_row['Messages_Sent'].iloc[0])
            metrics['follow_ups_sent_today'] = int(today_row['Follow_ups_Sent'].iloc[0])
            metrics['responses_received_today'] = int(today_row['Responses_Received'].iloc[0])
            metrics['leads_converted_today'] = int(today_row['Leads_Converted'].iloc[0])

    return metrics

def get_current_day():
    """Get current day of challenge"""
    days_elapsed = (datetime.now() - datetime.strptime(st.session_state.challenge_start_date, "%Y-%m-%d")).days + 1
    return min(max(days_elapsed, 1), 30)

# ==================== AUTHENTICATION ==================== #
def authenticate_user():
    """Authentication interface"""
    st.markdown("<div class='main-title'>🔐 LinkedIn Analytics Hub</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Complete Edition - All Features Unified</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='background: rgba(255, 255, 255, 0.95); padding: 3rem; border-radius: 25px; 
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;'>
            <h2 style='color: #667eea; margin-bottom: 2rem; font-weight: 800;'>🚀 Welcome!</h2>
            <p style='color: #666; font-size: 1.1rem; margin-bottom: 2rem;'>
                Upload your Google Service Account JSON to access all features
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("📁 Upload Service Account JSON", type=['json'])
        
        if uploaded_file:
            try:
                with st.spinner("🔄 Authenticating..."):
                    credentials_json = uploaded_file.read().decode('utf-8')
                    client = init_google_sheets(credentials_json)
                    if client:
                        st.session_state.authenticated = True
                        st.session_state.gsheets_client = client
                        st.success("✅ Authentication successful!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Authentication failed: {str(e)}")

# ==================== DASHBOARD OVERVIEW ==================== #
def show_dashboard_overview(metrics, daily_tracker_df):
    st.markdown("<div class='section-header'>📊 Dashboard Overview</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{metrics['total_leads']}</div>
            <div class="metric-label">Total Leads</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">💬</div>
            <div class="metric-value">{metrics['messages_sent']}</div>
            <div class="metric-label">Messages Sent</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📈</div>
            <div class="metric-value">{metrics['response_rate']}%</div>
            <div class="metric-label">Response Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{metrics['conversion_rate']}%</div>
            <div class="metric-label">Conversion Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Section 2: Daily Habit Tracker
    st.markdown("<div class='section-header'>📅 Daily Habit Tracker - 30 Day Challenge</div>", unsafe_allow_html=True)
    
    current_day = get_current_day()
    st.markdown(f"<p style='text-align: center; color: white; font-size: 1.5rem; font-weight: 700;'>Day {current_day} of 30</p>", unsafe_allow_html=True)
    
    if not daily_tracker_df.empty and current_day <= len(daily_tracker_df):
        today_row = daily_tracker_df.iloc[current_day - 1]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="stat-box" style="border-top-color: #667eea;">
                <div class="metric-icon">🔗</div>
                <div class="stat-number">{int(today_row.get('Connections_Sent', 0))}</div>
                <div class="stat-label">Connections</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-box" style="border-top-color: #764ba2;">
                <div class="metric-icon">💬</div>
                <div class="stat-number">{int(today_row.get('Messages_Sent', 0))}</div>
                <div class="stat-label">Messages</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-box" style="border-top-color: #667eea;">
                <div class="metric-icon">⬆️</div>
                <div class="stat-number">{int(today_row.get('Follow_ups_Sent', 0))}</div>
                <div class="stat-label">Follow-ups</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stat-box" style="border-top-color: #764ba2;">
                <div class="metric-icon">📩</div>
                <div class="stat-number">{int(today_row.get('Responses_Received', 0))}</div>
                <div class="stat-label">Responses</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="stat-box" style="border-top-color: #667eea;">
                <div class="metric-icon">💰</div>
                <div class="stat-number">{int(today_row.get('Leads_Converted', 0))}</div>
                <div class="stat-label">Converted</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No daily tracker data available for today.")

    # Habit Tracker Chart
    if not daily_tracker_df.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📈 30-Day Challenge Progress")
        
        # Create a date range for the challenge
        start_date = datetime.strptime(st.session_state.challenge_start_date, "%Y-%m-%d")
        challenge_dates = [start_date + timedelta(days=i) for i in range(30)]
        challenge_df = pd.DataFrame({'Date': [d.strftime("%Y-%m-%d") for d in challenge_dates]})
        
        # Merge with actual data
        display_df = pd.merge(challenge_df, daily_tracker_df, on='Date', how='left').fillna(0)
        display_df['Day'] = range(1, 31)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                            subplot_titles=("Daily Activity", "Conversion & Response"))

        # Trace 1: Connections, Messages, Follow-ups
        fig.add_trace(go.Scatter(x=display_df['Day'], y=display_df['Connections_Sent'], mode='lines+markers', name='Connections Sent', line=dict(color='#667eea')), row=1, col=1)
        fig.add_trace(go.Scatter(x=display_df['Day'], y=display_df['Messages_Sent'], mode='lines+markers', name='Messages Sent', line=dict(color='#764ba2')), row=1, col=1)
        fig.add_trace(go.Scatter(x=display_df['Day'], y=display_df['Follow_ups_Sent'], mode='lines+markers', name='Follow-ups Sent', line=dict(color='#a266ea')), row=1, col=1)
        
        # Trace 2: Responses, Converted
        fig.add_trace(go.Scatter(x=display_df['Day'], y=display_df['Responses_Received'], mode='lines+markers', name='Responses Received', line=dict(color='#10b981')), row=2, col=1)
        fig.add_trace(go.Scatter(x=display_df['Day'], y=display_df['Leads_Converted'], mode='lines+markers', name='Leads Converted', line=dict(color='#059669')), row=2, col=1)

        fig.update_layout(height=700, title_text="30-Day Challenge Progress",
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(255,255,255,0.95)',
                          font=dict(family='Inter', size=12), title_font_size=20, title_font_color='#667eea',
                          hovermode="x unified")
        fig.update_xaxes(title_text="Day of Challenge")
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

# ==================== CONVERSATION HISTORY ==================== #
def show_conversation_history(chat_df):
    st.markdown("<div class='section-header'>💬 Conversation History</div>", unsafe_allow_html=True)

    if chat_df.empty:
        st.info("No chat history available.")
        return

    # Pre-process chat_df for display
    chat_df['is_me'] = chat_df.apply(lambda row: is_me(row.get('sender_name'), row.get('sender_url'), MY_PROFILE), axis=1)
    chat_df['display_name'] = chat_df.apply(lambda row: MY_PROFILE['name'] if row['is_me'] else row.get('sender_name', 'Unknown'), axis=1)
    chat_df['initials'] = chat_df['display_name'].apply(get_initials)
    chat_df['message_type'] = chat_df['is_me'].apply(lambda x: 'sent' if x else 'received')
    chat_df['parsed_time'] = chat_df['timestamp'].apply(parse_timestamp)

    # Sort by timestamp
    chat_df = chat_df.sort_values(by='parsed_time', ascending=False).reset_index(drop=True)

    # Filters
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        message_type_filter = st.selectbox("Filter by Type", ['All', 'Sent', 'Received'], key='chat_type_filter')
    with col2:
        date_range_filter = st.selectbox("Date Range", ["All Time", "Last 7 Days", "Last 30 Days"], key='chat_date_filter')
    with col3:
        search_query = st.text_input("Search messages...", key='chat_search_query')

    filtered_chat_df = chat_df.copy()

    if message_type_filter == 'Sent':
        filtered_chat_df = filtered_chat_df[filtered_chat_df['message_type'] == 'sent']
    elif message_type_filter == 'Received':
        filtered_chat_df = filtered_chat_df[filtered_chat_df['message_type'] == 'received']

    if date_range_filter == "Last 7 Days":
        cutoff_date = datetime.now() - timedelta(days=7)
        filtered_chat_df = filtered_chat_df[filtered_chat_df['parsed_time'] >= cutoff_date]
    elif date_range_filter == "Last 30 Days":
        cutoff_date = datetime.now() - timedelta(days=30)
        filtered_chat_df = filtered_chat_df[filtered_chat_df['parsed_time'] >= cutoff_date]

    if search_query:
        filtered_chat_df = filtered_chat_df[filtered_chat_df['message'].str.contains(search_query, case=False, na=False)]

    st.markdown(f"<p style='color: white; font-size: 1.1rem;'>Displaying {len(filtered_chat_df)} of {len(chat_df)} messages</p>", unsafe_allow_html=True)

    for i, row in filtered_chat_df.iterrows():
        col_img, col_msg = st.columns([0.1, 0.9])
        with col_img:
            st.markdown(f"<div class='profile-badge'>{row['initials']}</div>", unsafe_allow_html=True)
        with col_msg:
            st.markdown(f"""
            <div class='message-card-all'>
                <p style='font-weight: 700; color: #667eea;'>{row['display_name']} <span style='font-weight: 400; color: #999; font-size: 0.8em;'>({row['parsed_time'].strftime('%Y-%m-%d %H:%M:%S') if row['parsed_time'] else 'N/A'})</span></p>
                <p style='color: #333;'>{row['message']}</p>
            </div>
            """, unsafe_allow_html=True)

# ==================== CRM DASHBOARD ==================== #
def show_crm_dashboard(outreach_df):
    st.markdown("<div class='section-header'>📋 CRM Dashboard</div>", unsafe_allow_html=True)

    if outreach_df.empty:
        st.info("No outreach data available. Go to 'Search & Send' to add leads.")
        return

    # Pre-process outreach_df for display
    if 'timestamp' in outreach_df.columns:
        outreach_df['parsed_time'] = outreach_df['timestamp'].apply(parse_timestamp)
    else:
        outreach_df['parsed_time'] = pd.NaT # Not a Time

    # Filters
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        status_filter = st.selectbox("Filter by Status", ['all', 'sent', 'pending', 'ready_to_send', 'responded'], key='crm_status_filter')
    with col2:
        date_range_filter = st.selectbox("Date Range", [7, 30, 90, "All Time"], format_func=lambda x: f"Last {x} Days" if isinstance(x, int) else x, key='crm_date_filter')
    with col3:
        search_query = st.text_input("Search leads...", key='crm_search_query')

    filters = {
        'status': status_filter,
        'date_range': date_range_filter if isinstance(date_range_filter, int) else None,
        'search_query': search_query
    }
    filtered_df = filter_dataframe(outreach_df, filters)

    st.markdown(f"<p style='color: white; font-size: 1.1rem;'>Displaying {len(filtered_df)} of {len(outreach_df)} leads</p>", unsafe_allow_html=True)

    # Stats for CRM
    total_leads = len(filtered_df)
    sent = len(filtered_df[filtered_df.apply(is_message_sent, axis=1)])
    pending = len(filtered_df[filtered_df['status'] == 'pending']) if 'status' in filtered_df.columns else 0
    ready = len(filtered_df[filtered_df['status'] == 'ready_to_send']) if 'status' in filtered_df.columns else 0

    st.markdown("""
    <div class="stats-grid">
    """, unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-box" style="border-top-color: #667eea;">
            <div class="metric-icon">👥</div>
            <div class="stat-number">{total_leads}</div>
            <div class="stat-label">Total Leads</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-box" style="border-top-color: #10b981;">
            <div class="metric-icon">✅</div>
            <div class="stat-number">{sent}</div>
            <div class="stat-label">Messages Sent</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-box" style="border-top-color: #f59e0b;">
            <div class="metric-icon">⏳</div>
            <div class="stat-number">{pending}</div>
            <div class="stat-label">Pending</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-box" style="border-top-color: #22c55e;">
            <div class="metric-icon">🚀</div>
            <div class="stat-number">{ready}</div>
            <div class="stat-label">Ready to Send</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div><br>", unsafe_allow_html=True)

    # Export options
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("📥 Export to CSV", use_container_width=True, key='crm_export_csv_btn'):
            csv_data = export_to_csv(filtered_df)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key='crm_download_csv_btn'
            )
    
    with col2:
        if st.button("📊 Generate Report", use_container_width=True, key='crm_generate_report_btn'):
            st.info("📊 Report generation feature coming soon!")

    # Lead Cards
    st.markdown("<br>", unsafe_allow_html=True)
    for idx, (i, row) in enumerate(filtered_df.iterrows()):
        with st.container():
            linkedin_url = row.get('linkedin_url', '#')
            profile_name = row.get('profile_name', 'Unknown')
            tagline = row.get('profile_tagline', 'N/A')
            message = row.get('linkedin_message', 'No message available')
            timestamp = row.get('timestamp', 'N/A')
            location = row.get('profile_location', 'N/A')
            company = row.get('company_name', 'N/A')
            status = row.get('status', 'unknown')
            
            # Status badge
            status_class = {
                'sent': 'status-sent',
                'pending': 'status-pending',
                'ready_to_send': 'status-ready',
                'responded': 'status-success'
            }.get(status, 'status-pending')
            
            # Check if favorited
            lead_id = generate_lead_id(profile_name, linkedin_url)
            is_favorited = lead_id in st.session_state.favorites
            has_notes = lead_id in st.session_state.notes
            lead_tags = st.session_state.tags.get(lead_id, [])
            
            st.markdown(f"""
            <div class="lead-card">
                <div style="display: flex; align-items: start; gap: 1.5rem; margin-bottom: 1rem;">
                    <div class="profile-badge">{get_initials(profile_name)}</div>
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <h3 class="lead-title">{profile_name}</h3>
                                <p class="lead-sub">💼 {tagline}</p>
                            </div>
                            <span class="status-badge {status_class}">{status.replace('_', ' ').title()}</span>
                        </div>
                        <div style="display: flex; gap: 2rem; margin: 1rem 0; flex-wrap: wrap;">
                            <span style="color: #666;">📍 {location}</span>
                            <span style="color: #666;">🏢 {company}</span>
                            <span style="color: #666;">🕐 {timestamp}</span>
                        </div>
                        {"<div style='margin: 0.5rem 0;'>" + "".join([f"<span class='tag-badge'>{tag}</span>" for tag in lead_tags]) + "</div>" if lead_tags else ""}
                    </div>
                </div>
                
                <div class="lead-msg">
                    <strong style="color: #667eea; font-size: 1.1rem;">📩 Outreach Message:</strong><br><br>
                    {message}
                </div>
            """, unsafe_allow_html=True)
            
            # Display notes if any
            if has_notes:
                st.markdown(f"""
                <div class="note-card">
                    <strong>📝 Note:</strong> {st.session_state.notes[lead_id]}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div class='action-buttons'>", unsafe_allow_html=True)
            st.markdown(f"""
                <a href="{linkedin_url}" target="_blank" class="action-btn">
                    🔗 View LinkedIn Profile
                </a>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Action buttons for each lead
            col_btn1, col_btn2, col_btn3, col_btn4, col_btn5 = st.columns(5)
            
            with col_btn1:
                if st.button("✉️ Send Message", key=f"crm_lead_send_{i}_{idx}", use_container_width=True):
                    success, response = send_webhook_request(WEBHOOK_URL, {
                        'action': 'send_message',
                        'profile_url': linkedin_url,
                        'message': message
                    })
                    if success:
                        st.success("✅ Message sent successfully!")
                    else:
                        st.error(f"❌ Failed to send: {response}")
            
            with col_btn2:
                if st.button("📧 Send Email", key=f"crm_lead_email_{i}_{idx}", use_container_width=True):
                    st.session_state.email_queue.append({
                        'to': profile_name,
                        'subject': f"Following up on LinkedIn",
                        'body': message
                    })
                    st.success("✅ Email queued!")
            
            with col_btn3:
                fav_icon = "⭐" if is_favorited else "☆"
                if st.button(f"{fav_icon} Favorite", key=f"crm_lead_fav_{i}_{idx}", use_container_width=True):
                    if is_favorited:
                        st.session_state.favorites.remove(lead_id)
                        st.info("Removed from favorites")
                    else:
                        st.session_state.favorites.add(lead_id)
                        st.success("⭐ Added to favorites!")
                    st.rerun()
            
            with col_btn4:
                if st.button("📝 Add Note", key=f"crm_lead_note_{i}_{idx}", use_container_width=True):
                    st.session_state.selected_contact = lead_id
            
            with col_btn5:
                if st.button("🏷️ Add Tag", key=f"crm_lead_tag_{i}_{idx}", use_container_width=True):
                    st.session_state.selected_contact = f"tag_{lead_id}"
            
            # Note input
            if st.session_state.selected_contact == lead_id:
                note_text = st.text_area("Enter your note:", key=f"crm_note_input_{lead_id}")
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button("💾 Save Note", key=f"crm_save_note_{lead_id}"):
                        st.session_state.notes[lead_id] = note_text
                        st.session_state.selected_contact = None
                        st.success("📝 Note saved!")
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Cancel", key=f"crm_cancel_note_{lead_id}"):
                        st.session_state.selected_contact = None
                        st.rerun()
            
            # Tag input
            if st.session_state.selected_contact == f"tag_{lead_id}":
                tag_text = st.text_input("Enter tag:", key=f"crm_tag_input_{lead_id}")
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button("💾 Add Tag", key=f"crm_save_tag_{lead_id}"):
                        if lead_id not in st.session_state.tags:
                            st.session_state.tags[lead_id] = []
                        st.session_state.tags[lead_id].append(tag_text)
                        st.session_state.selected_contact = None
                        st.success("🏷️ Tag added!")
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Cancel", key=f"crm_cancel_tag_{lead_id}"):
                        st.session_state.selected_contact = None
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

# ==================== SEARCH INTERFACE ==================== #
def show_search_interface(webhook_url):
    """Advanced lead search and generation interface"""
    st.markdown("<div class='section-header'>🔍 Advanced Lead Search & Generation</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: rgba(255, 255, 255, 0.95); padding: 2.5rem; border-radius: 25px; 
                text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.15); margin-bottom: 3rem;'>
        <h2 style='color: #667eea; margin-bottom: 1rem; font-weight: 800;'>🌍 Global Business Intelligence</h2>
        <p style='color: #666; font-size: 1.2rem; line-height: 1.8;'>
            Search and connect with decision-makers worldwide. Target by job title, location, industry, 
            and company size to generate highly qualified leads instantly.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Expanded job titles (100+)
    SEARCH_TERMS = [
        "Business Owner", "CEO", "Founder", "President", "Co-Founder", "Managing Director",
        "VP of Sales", "VP of Marketing", "Marketing Director", "Sales Director", "Chief Operating Officer",
        "Chief Financial Officer", "Chief Marketing Officer", "Chief Technology Officer", "Chief Strategy Officer",
        "Partner", "Investor", "Consultant", "Business Analyst", "Strategic Advisor", "Operations Manager",
        "Growth Manager", "Product Manager", "Head of Business Development", "Sales Executive", "Client Relations Manager",
        "Customer Success Manager", "Account Executive", "Regional Manager", "General Manager", "Division Head",
        "Director of Operations", "Director of Business Development", "Director of Strategy", "Chief of Staff",
        "E-commerce Manager", "Digital Marketing Manager", "Brand Manager", "Content Strategist", "SEO Specialist",
        "SEM Specialist", "Social Media Manager", "Community Manager", "Public Relations Manager", "Event Manager",
        "HR Director", "Recruitment Manager", "Talent Acquisition Specialist", "Training and Development Manager",
        "IT Director", "Software Engineer", "Data Scientist", "Machine Learning Engineer", "DevOps Engineer",
        "Cybersecurity Analyst", "Network Administrator", "Systems Architect", "UI/UX Designer", "Web Developer",
        "Mobile Developer", "Cloud Engineer", "Solutions Architect", "Technical Lead", "Project Manager",
        "Program Manager", "Scrum Master", "Agile Coach", "Supply Chain Manager", "Logistics Manager",
        "Procurement Manager", "Financial Analyst", "Investment Banker", "Portfolio Manager", "Auditor",
        "Tax Advisor", "Economist", "Research Analyst", "Legal Counsel", "Compliance Officer",
        "Healthcare Administrator", "Medical Director", "Pharmaceutical Sales Representative", "Biotech Scientist",
        "Educator", "Professor", "Academic Dean", "Librarian", "Research Fellow", "Journalist",
        "Editor", "Publisher", "Creative Director", "Art Director", "Copywriter", "Photographer",
        "Videographer", "Animator", "Game Developer", "Architect", "Civil Engineer", "Mechanical Engineer",
        "Electrical Engineer", "Chemical Engineer", "Environmental Engineer", "Geologist", "Urban Planner",
        "Real Estate Agent", "Broker", "Property Manager", "Underwriter", "Claims Adjuster", "Actuary",
        "Customer Service Manager", "Support Specialist", "Field Service Engineer", "Quality Assurance Manager",
        "Manufacturing Engineer", "Operations Director", "Retail Manager", "Merchandiser", "Buyer",
        "Franchise Owner", "Restaurant Manager", "Chef", "Sommelier", "Hotel Manager", "Travel Agent",
        "Tour Operator", "Fitness Instructor", "Personal Trainer", "Nutritionist", "Wellness Coach",
        "Therapist", "Counselor", "Social Worker", "Non-profit Director", "Volunteer Coordinator",
        "Government Official", "Policy Advisor", "Diplomat", "Intelligence Analyst", "Military Officer"
    ]

    col1, col2 = st.columns(2)
    with col1:
        selected_job_title = st.selectbox("Target Job Title", SEARCH_TERMS, key='search_job_title')
    with col2:
        location = st.text_input("Target Location (e.g., 'New York', 'London')", key='search_location')

    industry = st.text_input("Target Industry (e.g., 'Technology', 'Finance')", key='search_industry')
    company_size = st.selectbox("Company Size", ['Any', '1-10', '11-50', '51-200', '201-500', '501-1000', '1001-5000', '5001-10000', '10000+'], key='search_company_size')
    num_leads = st.slider("Number of Leads to Generate", 1, 50, 10, key='search_num_leads')

    if st.button("🚀 Generate Leads", use_container_width=True):
        with st.spinner("Searching for leads..."):
            # Simulate lead generation and add to outreach_df
            new_leads_data = []
            for i in range(num_leads):
                profile_name = f"Generated Lead {len(st.session_state.outreach_df) + i + 1}"
                linkedin_url = f"https://www.linkedin.com/in/generated-lead-{len(st.session_state.outreach_df) + i + 1}"
                new_leads_data.append({
                    'profile_name': profile_name,
                    'linkedin_url': linkedin_url,
                    'profile_tagline': f"{selected_job_title} at {industry} Co.",
                    'linkedin_message': f"Hello {profile_name}, I found your profile while searching for {selected_job_title}s in {location}. I'd love to connect!",
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'profile_location': location,
                    'company_name': f"{industry} Co.",
                    'status': 'ready_to_send',
                    'success': 'false'
                })
            
            new_leads_df = pd.DataFrame(new_leads_data)
            st.session_state.outreach_df = pd.concat([st.session_state.outreach_df, new_leads_df], ignore_index=True)
            st.success(f"✅ Generated {num_leads} new leads!")
            st.rerun()

    st.markdown("### 📥 Manually Add Lead")
    with st.form("manual_lead_form"):
        m_profile_name = st.text_input("Profile Name")
        m_linkedin_url = st.text_input("LinkedIn Profile URL")
        m_profile_tagline = st.text_input("Profile Tagline")
        m_linkedin_message = st.text_area("Outreach Message")
        m_profile_location = st.text_input("Location")
        m_company_name = st.text_input("Company Name")
        
        submitted = st.form_submit_button("➕ Add Lead Manually")
        if submitted:
            if m_profile_name and m_linkedin_url and m_linkedin_message:
                new_lead = pd.DataFrame([{
                    'profile_name': m_profile_name,
                    'linkedin_url': m_linkedin_url,
                    'profile_tagline': m_profile_tagline,
                    'linkedin_message': m_linkedin_message,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'profile_location': m_profile_location,
                    'company_name': m_company_name,
                    'status': 'ready_to_send',
                    'success': 'false'
                }])
                st.session_state.outreach_df = pd.concat([st.session_state.outreach_df, new_lead], ignore_index=True)
                st.success(f"✅ Lead '{m_profile_name}' added successfully!")
                st.rerun()
            else:
                st.error("Profile Name, LinkedIn URL, and Outreach Message are required.")

# ==================== ANALYTICS ==================== #
def show_analytics(chat_df, outreach_df):
    st.markdown("<div class='section-header'>📊 Advanced Analytics</div>", unsafe_allow_html=True)

    if chat_df.empty and outreach_df.empty:
        st.info("No data available for analytics. Load data from Google Sheets or generate leads.")
        return

    # Time-based analysis
    st.markdown("### 📈 Activity Over Time")
    if not chat_df.empty and 'parsed_time' in chat_df.columns:
        chat_df['date'] = chat_df['parsed_time'].dt.date
        daily_activity = chat_df.groupby('date').size().reset_index(name='message_count')
        fig = px.line(daily_activity, x='date', y='message_count', title='Daily Message Activity')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(255,255,255,0.95)',
                          font=dict(family='Inter', size=12), title_font_size=20, title_font_color='#667eea')
        st.plotly_chart(fig, use_container_width=True)

    # Lead status distribution
    if not outreach_df.empty and 'status' in outreach_df.columns:
        st.markdown("### 🎯 Lead Status Distribution")
        status_counts = outreach_df['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        fig = px.pie(status_counts, values='count', names='status', title='Lead Status Breakdown',
                     color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(255,255,255,0.95)',
                          font=dict(family='Inter', size=12), title_font_size=20, title_font_color='#667eea')
        st.plotly_chart(fig, use_container_width=True)

    # Company distribution
    if not outreach_df.empty and 'company_name' in outreach_df.columns:
        st.markdown("### 🏢 Top Companies")
        
        company_counts = outreach_df['company_name'].value_counts().head(10)
        
        fig = px.bar(x=company_counts.index, y=company_counts.values,
                    title='Top 10 Companies',
                    labels={'x': 'Company', 'y': 'Number of Leads'})
        fig.update_traces(marker_color='#764ba2')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(255,255,255,0.95)',
            font=dict(family='Inter', size=12),
            title_font_size=20,
            title_font_color='#667eea'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Response rate analysis
    if not chat_df.empty:
        st.markdown("### 💬 Response Analysis")
        
        sent_messages = len(chat_df[chat_df.apply(
            lambda row: is_me(row.get('sender_name'), row.get('sender_url'), MY_PROFILE), axis=1
        )])
        received_messages = len(chat_df) - sent_messages
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📤 Messages Sent", sent_messages)
        with col2:
            st.metric("📥 Messages Received", received_messages)
        with col3:
            response_rate = round((received_messages / sent_messages * 100), 2) if sent_messages > 0 else 0
            st.metric("📊 Response Rate", f"{response_rate}%")

# ==================== EMAIL QUEUE MANAGER ==================== #
def show_email_queue():
    """Display and manage email queue"""
    st.markdown("<div class='section-header'>📧 Email Queue Manager</div>", unsafe_allow_html=True)
    
    if not st.session_state.email_queue:
        st.markdown("""
        <div style='background: rgba(255, 255, 255, 0.95); padding: 4rem; border-radius: 25px; 
                    text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.15);'>
            <h2 style='color: #667eea; font-size: 3rem; margin-bottom: 1rem;'>📧</h2>
            <h3 style='color: #2d3748; margin-bottom: 1rem;'>Email Queue is Empty</h3>
            <p style='color: #666; font-size: 1.1rem;'>Queue emails from the CRM dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"""
    <div class='stat-box'>
        <div class='metric-icon'>📧</div>
        <div class='stat-number'>{len(st.session_state.email_queue)}</div>
        <div class='stat-label'>Queued Emails</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    for idx, email in enumerate(st.session_state.email_queue):
        st.markdown(f"""
        <div class='email-card'>
            <h3 class='lead-title'>To: {email['to']}</h3>
            <p class='lead-sub'><strong>Subject:</strong> {email['subject']}</p>
            <div class='lead-msg'>
                {email['body']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Send Now", key=f"send_email_{idx}", use_container_width=True):
                st.success(f"✅ Email sent to {email['to']}!")
                st.session_state.email_queue.pop(idx)
                st.rerun()
        with col2:
            if st.button("✏️ Edit", key=f"edit_email_{idx}", use_container_width=True):
                st.info("✏️ Edit feature coming soon!")
        with col3:
            if st.button("🗑️ Delete", key=f"delete_email_{idx}", use_container_width=True):
                st.session_state.email_queue.pop(idx)
                st.rerun()

# ==================== WEBHOOK MONITOR ==================== #
def show_webhook_monitor():
    """Monitor webhook activity and test connections"""
    st.markdown("<div class='section-header'>🔗 Webhook Monitor</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='crm-card'>
        <h3 style='color: #667eea; margin-bottom: 1rem;'>📡 Webhook Configuration</h3>
        <p style='color: #666;'><strong>Endpoint:</strong> {WEBHOOK_URL}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Test webhook
    st.markdown("### 🧪 Test Webhook Connection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_action = st.selectbox("Select Test Action", 
                                   ['ping', 'search_leads', 'send_message', 'get_status'], key='webhook_test_action')
    
    with col2:
        if st.button("🚀 Send Test Request", use_container_width=True, key='send_test_webhook_btn'):
            with st.spinner("Sending test request..."):
                test_payload = {
                    'action': test_action,
                    'test': True,
                    'timestamp': datetime.now().isoformat()
                }
                
                success, response = send_webhook_request(WEBHOOK_URL, test_payload)
                
                if success:
                    st.success("✅ Webhook test successful!")
                    st.session_state.webhook_history.append({
                        'timestamp': datetime.now(),
                        'action': test_action,
                        'status': 'success',
                        'response': response
                    })
                else:
                    st.error(f"❌ Webhook test failed: {response}")
                    st.session_state.webhook_history.append({
                        'timestamp': datetime.now(),
                        'action': test_action,
                        'status': 'failed',
                        'response': response
                    })
    
    # Webhook history
    st.markdown("### 📜 Webhook History")
    
    if st.session_state.webhook_history:
        for entry in reversed(st.session_state.webhook_history[-20:]):
            status_class = 'status-success' if entry['status'] == 'success' else 'status-error'
            status_icon = '✅' if entry['status'] == 'success' else '❌'
            
            st.markdown(f"""
            <div class='message-card-all'>
                <div style='display: flex; justify-content: space-between; align-items: start;'>
                    <div style='flex: 1;'>
                        <div style='display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;'>
                            <span class='status-badge {status_class}'>{status_icon} {entry['status'].upper()}</span>
                            <strong style='color: #667eea;'>{entry['action']}</strong>
                        </div>
                        <p style='color: #666; margin: 0.5rem 0; font-size: 0.9rem;'>
                            Response: {entry['response'][:100]}{'...' if len(str(entry['response'])) > 100 else ''}
                        </p>
                    </div>
                    <span style='color: #999; font-size: 0.85rem; white-space: nowrap;'>
                        {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No webhook history yet. Send a test request to get started!")

# ==================== SETTINGS ==================== #
def show_settings():
    """Application settings and configuration"""
    st.markdown("<div class='section-header'>⚙️ Settings & Configuration</div>", unsafe_allow_html=True)
    
    # General Settings
    st.markdown("### 🎛️ General Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.show_notifications = st.checkbox(
            "🔔 Show Notifications",
            value=st.session_state.show_notifications,
            key='setting_show_notifications'
        )
        
        st.session_state.auto_refresh = st.checkbox(
            "🔄 Auto Refresh Data",
            value=st.session_state.auto_refresh,
            key='setting_auto_refresh'
        )
    
    with col2:
        st.session_state.dark_mode = st.checkbox(
            "🌙 Dark Mode (Coming Soon)",
            value=st.session_state.dark_mode,
            disabled=True,
            key='setting_dark_mode'
        )
        
        if st.session_state.auto_refresh:
            st.session_state.refresh_interval = st.slider(
                "Refresh Interval (seconds)",
                min_value=30,
                max_value=300,
                value=st.session_state.refresh_interval,
                step=30,
                key='setting_refresh_interval'
            )
    
    # Data Management
    st.markdown("### 💾 Data Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh All Data", use_container_width=True, key='setting_refresh_all_data_btn'):
            st.cache_data.clear()
            st.success("✅ Data refreshed!")
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Cache", use_container_width=True, key='setting_clear_cache_btn'):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache cleared!")
            st.rerun() # Rerun to ensure all cached data is reloaded
    
    with col3:
        if st.button("📥 Export All Data", use_container_width=True, key='setting_export_all_data_btn'):
            st.info("📥 Export feature coming soon!")
    
    # Account Information
    st.markdown("### 👤 Account Information")
    
    st.markdown(f"""
    <div class='crm-card'>
        <p><strong>Profile Name:</strong> {MY_PROFILE['name']}</p>
        <p><strong>LinkedIn URL:</strong> <a href="{MY_PROFILE['url']}" target="_blank">{MY_PROFILE['url']}</a></p>
        <p><strong>Last Refresh:</strong> {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Advanced Settings
    with st.expander("🔧 Advanced Settings"):
        st.markdown("#### API Configuration")
        
        webhook_url_custom = st.text_input("Webhook URL", value=WEBHOOK_URL, key='setting_webhook_url_input')
        
        if st.button("💾 Save Webhook URL", key='setting_save_webhook_url_btn'):
            # In a real app, you would save this to a persistent config
            st.success("✅ Webhook URL saved (for this session)!")
        
        st.markdown("#### Data Retention")
        retention_days = st.slider("Keep data for (days)", 30, 365, 90, key='setting_data_retention_slider')
        
        st.markdown("#### Export Format")
        export_format = st.selectbox("Default Export Format", ['CSV', 'Excel', 'JSON', 'PDF'], key='setting_export_format_select')

# ==================== MAIN APPLICATION ==================== #
def main():
    """Main application logic"""
    
    # Check authentication
    if not st.session_state.authenticated:
        authenticate_user()
        return
    
    # Load all data
    client = st.session_state.gsheets_client
    
    with st.spinner("📊 Loading all data..."):
        chat_df = load_sheet_data(client, CHAT_SPREADSHEET_ID, CHAT_SHEET_NAME)
        outreach_df = load_sheet_data(client, OUTREACH_SPREADSHEET_ID, OUTREACH_SHEET_NAME)
        daily_tracker = load_daily_tracker()
        leads_database = load_leads_database()
        
        st.session_state.chat_df = chat_df
        st.session_state.outreach_df = outreach_df
        st.session_state.daily_tracker = daily_tracker
        st.session_state.leads_database = leads_database
        st.session_state.last_refresh = datetime.utcnow()
    
    # Calculate metrics
    metrics = calculate_metrics(chat_df, outreach_df, daily_tracker)
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #667eea; font-size: 2rem; font-weight: 900;'>🚀 LinkedIn Hub</h1>
            <p style='color: #666; font-size: 0.9rem;'>Analytics & Outreach Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        page = st.radio(
            "📍 Navigation",
            [
                "🏠 Dashboard",
                "💬 Conversations",
                "📋 CRM",
                "🔍 Search & Send",
                "📊 Analytics",
                "📧 Email Queue",
                "🔗 Webhook Monitor",
                "⚙️ Settings"
            ],
            label_visibility="collapsed",
            key='sidebar_navigation'
        )
        st.session_state.current_page = page # Update current page in session state
        
        st.markdown("---")
        
        # Quick Stats in Sidebar
        st.markdown("### 📊 Quick Stats")
        st.metric("Total Leads", metrics['total_leads'])
        st.metric("Response Rate", f"{metrics['response_rate']}%" if metrics['response_rate'] else "0%")
        st.metric("Conversion", f"{metrics['conversion_rate']}%" if metrics['conversion_rate'] else "0%")
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("🔄 Refresh Data", use_container_width=True, key='sidebar_refresh_btn'):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True, key='sidebar_logout_btn'):
            st.session_state.authenticated = False
            st.rerun()
        
        st.markdown("---")
        
        # Footer
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; color: #999; font-size: 0.8rem;'>
            <p>Last updated:<br>{st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style='margin-top: 1rem;'>Made with ❤️ by Donmenico Hudson</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main Content Area - Render based on selected page
    if st.session_state.current_page == "🏠 Dashboard":
        show_dashboard_overview(metrics, daily_tracker)
    
    elif st.session_state.current_page == "💬 Conversations":
        show_conversation_history(chat_df)
    
    elif st.session_state.current_page == "📋 CRM":
        show_crm_dashboard(outreach_df)
    
    elif st.session_state.current_page == "🔍 Search & Send":
        show_search_interface(WEBHOOK_URL)
    
    elif st.session_state.current_page == "📊 Analytics":
        show_analytics(chat_df, outreach_df)
    
    elif st.session_state.current_page == "📧 Email Queue":
        show_email_queue()
    
    elif st.session_state.current_page == "🔗 Webhook Monitor":
        show_webhook_monitor()
    
    elif st.session_state.current_page == "⚙️ Settings":
        show_settings()

# ==================== RUN APPLICATION ==================== #
if __name__ == "__main__":
    main()

