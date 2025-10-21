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
    page_title="LinkedIn Analytics & Habit Tracker - All-in-One",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== STATIC CONFIGURATION ==================== #
# LinkedIn Analytics Configuration
CHAT_SPREADSHEET_ID = "1klm60YFXSoV510S4igv5LfREXeykDhNA5Ygq7HNFN0I"
CHAT_SHEET_NAME = "linkedin_chat_history_advanced 2"
OUTREACH_SPREADSHEET_ID = "1eLEFvyV1_f74UC1g5uQ-xA7A62sK8Pog27KIjw_Sk3Y"
OUTREACH_SHEET_NAME = "linkedin-tracking-csv.csv"
MY_PROFILE = {"name": "Donmenico Hudson", "url": "https://www.linkedin.com/in/donmenicohudson/"}
WEBHOOK_URL = "https://agentonline-u29564.vm.elestio.app/webhook/Leadlinked"

# Habit Tracking Configuration
DAILY_TRACKER_SHEET_ID = "1UkuTf8VwGPIilTxhTEdP9K-zdtZFnThazFdGyxVYfmg"
LEADS_DATABASE_SHEET_ID = "1eLEFvyV1_f74UC1g5uQ-xA7A62sK8Pog27KIjw_Sk3Y"
DAILY_TRACKER_SHEET_NAME = "daily_tracker_20251021"
LEADS_SHEET_GID = "1881909623"

# ==================== SESSION STATE ==================== #
for key, default in [
    ('authenticated', False), ('gsheets_client', None), ('activity_log', []),
    ('sent_leads', set()), ('selected_leads', []), ('current_client', None),
    ('chat_df', pd.DataFrame()), ('outreach_df', pd.DataFrame()),
    ('last_refresh', datetime.utcnow()), ('webhook_history', []), ('email_queue', []),
    ('show_notifications', True), ('dark_mode', False), ('selected_contact', None),
    ('filter_status', 'all'), ('filter_date_range', 7), ('sort_by', 'timestamp'),
    ('search_query', ''), ('favorites', set()), ('notes', {}), ('tags', {}),
    ('export_format', 'csv'), ('auto_refresh', False), ('refresh_interval', 60),
    ('daily_tracker', pd.DataFrame()), ('leads_database', pd.DataFrame()),
    ('challenge_start_date', datetime.now().strftime("%Y-%m-%d")), ('sheets_data', None),
    ('leads_sheets_data', None)
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
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
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
    
    .metric-card:hover {
        transform: translateY(-10px) scale(1.02);
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
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
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
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
    
    .stat-box {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-top: 4px solid #667eea;
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
    
    .note-card {
        background: #fff9e6;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-style: italic;
        color: #666;
    }
    
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
    
    .habit-progress {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 8px;
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .habit-progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #10b981 0%, #059669 100%);
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    
    .big-metric {
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        color: #0077B5;
    }
    
    .linkedin-blue {
        background: linear-gradient(135deg, #0077B5 0%, #00A0DC 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .info-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .stage-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #0077B5;
        margin: 10px 0;
    }
    
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ==================== #

@st.cache_resource
def init_google_sheets(credentials_json):
    """Initialize Google Sheets client with service account credentials"""
    try:
        credentials_dict = json.loads(credentials_json)
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
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

def get_sheet_by_gid(sheet_id, gid):
    """Get Google Sheet data using GID"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            return df
    except Exception as e:
        st.error(f"Error loading sheet with GID {gid}: {str(e)}")
    return None

def get_sheet_by_name(sheet_id, sheet_name):
    """Get Google Sheet data by sheet name"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
    except:
        pass
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
    except:
        pass
    return None

def load_daily_tracker():
    """Load daily tracker data from Google Sheets"""
    try:
        df = get_sheet_by_name(DAILY_TRACKER_SHEET_ID, DAILY_TRACKER_SHEET_NAME)
        if df is not None and not df.empty:
            df.columns = df.columns.str.strip()
            numeric_cols = ['Connections_Sent', 'Connections_Accepted', 'Initial_Messages_Sent', 
                          'Interested_Responses', 'Links_Sent', 'Follow_Up_1', 'Follow_Up_2', 
                          'Follow_Up_3', 'Follow_Up_4', 'Conversions']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            return df
        return create_empty_daily_tracker()
    except:
        return create_empty_daily_tracker()

def load_leads_database():
    """Load leads database from Google Sheets"""
    try:
        df = get_sheet_by_gid(LEADS_DATABASE_SHEET_ID, LEADS_SHEET_GID)
        
        if df is not None and not df.empty:
            df.columns = df.columns.str.strip()
            
            expected_columns = [
                'timestamp', 'profile_name', 'profile_location', 'profile_tagline',
                'linkedin_url', 'linkedin_subject', 'linkedin_message',
                'email_subject', 'email_message', 'outreach_strategy',
                'personalization_points', 'follow_up_suggestions', 'connection_status',
                'browserflow_session', 'success', 'credits_used', 'error_message',
                'status', 'search_term', 'search_city', 'search_country',
                'name', 'image_url', 'tagline', 'location', 'summary'
            ]
            
            available_columns = [col for col in expected_columns if col in df.columns]
            
            if available_columns:
                df = df[available_columns]
            
            if 'success' in df.columns:
                df['success'] = df['success'].astype(str).str.lower().isin(['true', 'yes', '1', 't'])
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            if 'credits_used' in df.columns:
                df['credits_used'] = pd.to_numeric(df['credits_used'], errors='coerce').fillna(0)
            
            return df
        
        return create_empty_leads_database()
    except Exception as e:
        st.sidebar.error(f"Error loading leads: {str(e)}")
        return create_empty_leads_database()

def create_empty_daily_tracker():
    """Create empty daily tracker dataframe"""
    start_date = datetime.now()
    dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
    return pd.DataFrame({
        'Day': [i+1 for i in range(30)],
        'Date': dates,
        'Connections_Sent': [0] * 30,
        'Connections_Accepted': [0] * 30,
        'Initial_Messages_Sent': [0] * 30,
        'Interested_Responses': [0] * 30,
        'Links_Sent': [0] * 30,
        'Follow_Up_1': [0] * 30,
        'Follow_Up_2': [0] * 30,
        'Follow_Up_3': [0] * 30,
        'Follow_Up_4': [0] * 30,
        'Conversions': [0] * 30,
        'Notes': [''] * 30
    })

def create_empty_leads_database():
    """Create empty leads database dataframe"""
    return pd.DataFrame({
        'timestamp': [],
        'profile_name': [],
        'profile_location': [],
        'profile_tagline': [],
        'linkedin_url': [],
        'linkedin_subject': [],
        'linkedin_message': [],
        'email_subject': [],
        'email_message': [],
        'outreach_strategy': [],
        'personalization_points': [],
        'follow_up_suggestions': [],
        'connection_status': [],
        'browserflow_session': [],
        'success': [],
        'credits_used': [],
        'error_message': [],
        'status': [],
        'search_term': [],
        'search_city': [],
        'search_country': [],
        'name': [],
        'image_url': [],
        'tagline': [],
        'location': [],
        'summary': []
    })

def parse_timestamp(timestamp_str):
    """Parse various timestamp formats"""
    try:
        if pd.isna(timestamp_str) or timestamp_str == '':
            return None
        return pd.to_datetime(timestamp_str, format='%m/%d/%Y %H:%M:%S')
    except:
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

def filter_dataframe(df, filters):
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    if filters.get('status') and filters['status'] != 'all':
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

def calculate_metrics(chat_df, outreach_df, daily_df):
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
        'total_connections_sent': 0,
        'total_connections_accepted': 0,
        'total_interested': 0,
        'total_conversions': 0
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
    
    # Add daily tracker metrics
    if not daily_df.empty:
        metrics['total_connections_sent'] = daily_df['Connections_Sent'].sum() if 'Connections_Sent' in daily_df.columns else 0
        metrics['total_connections_accepted'] = daily_df['Connections_Accepted'].sum() if 'Connections_Accepted' in daily_df.columns else 0
        metrics['total_interested'] = daily_df['Interested_Responses'].sum() if 'Interested_Responses' in daily_df.columns else 0
        metrics['total_conversions'] = daily_df['Conversions'].sum() if 'Conversions' in daily_df.columns else 0
    
    return metrics

def get_current_day():
    """Get current day of challenge"""
    days_elapsed = (datetime.now() - datetime.strptime(st.session_state.challenge_start_date, "%Y-%m-%d")).days + 1
    return min(max(days_elapsed, 1), 30)

# ==================== AUTHENTICATION ==================== #
def authenticate_user():
    """User authentication interface"""
    st.markdown("<div class='main-title'>🔐 LinkedIn Analytics & Habit Tracker</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Secure Authentication Portal - All-in-One Platform</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='background: rgba(255, 255, 255, 0.95); padding: 3rem; border-radius: 25px; 
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;'>
            <h2 style='color: #667eea; margin-bottom: 2rem; font-weight: 800;'>🚀 Welcome Back!</h2>
            <p style='color: #666; font-size: 1.1rem; margin-bottom: 2rem;'>
                Upload your service account credentials to access your complete analytics dashboard
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("📁 Upload Service Account JSON", type=['json'], 
                                        help="Drag and drop your Google Service Account JSON file here")
        
        if uploaded_file:
            try:
                with st.spinner("🔄 Authenticating your credentials..."):
                    credentials_json = uploaded_file.read().decode('utf-8')
                    client = init_google_sheets(credentials_json)
                    if client:
                        st.session_state.authenticated = True
                        st.session_state.gsheets_client = client
                        st.success("✅ Authentication successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Authentication failed: {str(e)}")

# ==================== MAIN APPLICATION ==================== #
def main():
    """Main application logic - All features on one page"""
    
    # Check authentication
    if not st.session_state.authenticated:
        authenticate_user()
        return
    
    # Load data
    client = st.session_state.gsheets_client
    
    with st.spinner("📊 Loading all data..."):
        chat_df = load_sheet_data(client, CHAT_SPREADSHEET_ID, CHAT_SHEET_NAME)
        outreach_df = load_sheet_data(client, OUTREACH_SPREADSHEET_ID, OUTREACH_SHEET_NAME)
        daily_df = load_daily_tracker()
        leads_df = load_leads_database()
        
        st.session_state.chat_df = chat_df
        st.session_state.outreach_df = outreach_df
        st.session_state.daily_tracker = daily_df
        st.session_state.leads_database = leads_df
        st.session_state.last_refresh = datetime.utcnow()
    
    # Calculate metrics
    metrics = calculate_metrics(chat_df, outreach_df, daily_df)
    current_day = get_current_day()
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #667eea; font-size: 2rem; font-weight: 900;'>🚀 LinkedIn Hub</h1>
            <p style='color: #666; font-size: 0.9rem;'>All-in-One Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Challenge info
        st.markdown("### 📊 Challenge Overview")
        st.markdown(f"**📅 Day {current_day} of 30**")
        st.progress(current_day / 30)
        st.markdown(f"**Started:** {st.session_state.challenge_start_date}")
        
        st.markdown("---")
        
        # Quick Stats
        st.markdown("### 🎯 Quick Stats")
        st.metric("Connections Sent", f"{int(metrics['total_connections_sent'])}/1,200")
        st.metric("Accepted", int(metrics['total_connections_accepted']))
        st.metric("Interested", int(metrics['total_interested']))
        st.metric("Conversions", int(metrics['total_conversions']))
        st.metric("Total Leads", metrics['total_leads'])
        st.metric("Response Rate", f"{metrics['response_rate']}%")
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        
        st.markdown("---")
        
        # Footer
        st.markdown("""
        <div style='text-align: center; padding: 1rem; color: #999; font-size: 0.8rem;'>
            <p>Last updated:<br>{}</p>
            <p style='margin-top: 1rem;'>Made with ❤️ by Donmenico</p>
        </div>
        """.format(st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)
    
    # Main Content - All Features on One Page
    st.markdown("<div class='main-title'>🚀 LinkedIn Analytics & Habit Tracker</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Complete All-in-One Dashboard - All Features in One View</div>", unsafe_allow_html=True)
    
    # ==================== SECTION 1: KEY METRICS ==================== #
    st.markdown("<div class='section-header'>📊 Key Performance Metrics</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔗</div>
            <div class="metric-value">{int(metrics['total_connections_sent'])}</div>
            <div class="metric-label">Connections Sent</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card success-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{int(metrics['total_connections_accepted'])}</div>
            <div class="metric-label">Accepted</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card info-card">
            <div class="metric-icon">💡</div>
            <div class="metric-value">{int(metrics['total_interested'])}</div>
            <div class="metric-label">Interested</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card warning-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-value">{int(metrics['total_conversions'])}</div>
            <div class="metric-label">Conversions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{metrics['total_leads']}</div>
            <div class="metric-label">Total Leads</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ==================== SECTION 2: DAILY TRACKER ==================== #
    st.markdown("<div class='section-header'>📅 Daily Habit Tracker</div>", unsafe_allow_html=True)
    
    st.markdown(f"<p style='text-align: center; color: white; font-size: 1.2rem;'>Day {current_day} of 30-Day Challenge</p>", unsafe_allow_html=True)
    
    if not daily_df.empty:
        # Display today's metrics
        if current_day <= len(daily_df):
            today_row = daily_df.iloc[current_day - 1]
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown(f"""
                <div class="stat-box" style="border-top-color: #667eea;">
                    <div class="metric-icon">🔗</div>
                    <div class="stat-number">{int(today_row.get('Connections_Sent', 0))}</div>
                    <div class="stat-label">Today's Connections</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stat-box" style="border-top-color: #10b981;">
                    <div class="metric-icon">✅</div>
                    <div class="stat-number">{int(today_row.get('Connections_Accepted', 0))}</div>
                    <div class="stat-label">Accepted Today</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="stat-box" style="border-top-color: #3b82f6;">
                    <div class="metric-icon">💬</div>
                    <div class="stat-number">{int(today_row.get('Initial_Messages_Sent', 0))}</div>
                    <div class="stat-label">Messages Sent</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="stat-box" style="border-top-color: #f59e0b;">
                    <div class="metric-icon">💡</div>
                    <div class="stat-number">{int(today_row.get('Interested_Responses', 0))}</div>
                    <div class="stat-label">Interested</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col5:
                st.markdown(f"""
                <div class="stat-box" style="border-top-color: #ef4444;">
                    <div class="metric-icon">🎯</div>
                    <div class="stat-number">{int(today_row.get('Conversions', 0))}</div>
                    <div class="stat-label">Conversions</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Display 30-day chart
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📈 30-Day Performance Chart")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_df['Date'],
            y=daily_df['Connections_Sent'],
            mode='lines+markers',
            name='Connections Sent',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_df['Date'],
            y=daily_df['Initial_Messages_Sent'],
            mode='lines+markers',
            name='Messages Sent',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_df['Date'],
            y=daily_df['Conversions'],
            mode='lines+markers',
            name='Conversions',
            line=dict(color='#10b981', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(255,255,255,0.95)',
            font=dict(family='Inter', size=12),
            title_font_size=20,
            title_font_color='#667eea',
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ==================== SECTION 3: LEADS DATABASE ==================== #
    st.markdown("<div class='section-header'>👥 Leads Database (CRM)</div>", unsafe_allow_html=True)
    
    if leads_df is not None and not leads_df.empty:
        st.success(f"✅ Loaded {len(leads_df)} leads from Google Sheets")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Leads", f"{len(leads_df):,}")
        
        with col2:
            if 'success' in leads_df.columns:
                successful = leads_df[leads_df['success'] == True].shape[0]
                success_rate = (successful / len(leads_df) * 100) if len(leads_df) > 0 else 0
                st.metric("Successful Outreach", successful)
                st.caption(f"✅ {success_rate:.1f}% success rate")
        
        with col3:
            if 'connection_status' in leads_df.columns:
                connected = leads_df[leads_df['connection_status'].notna()].shape[0]
                st.metric("With Status", connected)
        
        with col4:
            if 'timestamp' in leads_df.columns:
                today_leads = leads_df[leads_df['timestamp'].dt.date == datetime.now().date()]
                st.metric("Today's Leads", len(today_leads))
        
        # Display leads table
        st.markdown("### 📋 Lead Records (Top 20)")
        display_cols = []
        priority_display = [
            'timestamp', 'profile_name', 'name', 'profile_location', 'location',
            'linkedin_url', 'connection_status', 'success', 'search_term'
        ]
        
        for col in priority_display:
            if col in leads_df.columns:
                display_cols.append(col)
        
        if display_cols:
            st.dataframe(leads_df[display_cols].head(20), use_container_width=True, height=400)
        else:
            st.dataframe(leads_df.head(20), use_container_width=True, height=400)
    else:
        st.warning("⚠️ No leads data loaded from Google Sheets")
    
    # ==================== SECTION 4: ANALYTICS & CHARTS ==================== #
    st.markdown("<div class='section-header'>📊 Advanced Analytics</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Cumulative Progress")
        if not daily_df.empty and 'Day' in daily_df.columns:
            cumulative_df = daily_df.copy()
            cumulative_df['Cumulative_Sent'] = cumulative_df['Connections_Sent'].cumsum()
            cumulative_df['Cumulative_Accepted'] = cumulative_df['Connections_Accepted'].cumsum()
            cumulative_df['Cumulative_Conversions'] = cumulative_df['Conversions'].cumsum()
            
            fig = px.line(cumulative_df, x='Day', 
                         y=['Cumulative_Sent', 'Cumulative_Accepted', 'Cumulative_Conversions'],
                         title='Cumulative Metrics Over 30 Days',
                         labels={'value': 'Count', 'variable': 'Metric'})
            fig.add_hline(y=1200, line_dash="dash", line_color="red", 
                         annotation_text="Goal: 1,200")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Conversion Funnel")
        funnel_data = {
            'Stage': ['Sent', 'Accepted', 'Messaged', 'Interested', 'Converted'],
            'Count': [
                metrics['total_connections_sent'], 
                metrics['total_connections_accepted'], 
                metrics['messages_sent'],
                metrics['total_interested'], 
                metrics['total_conversions']
            ]
        }
        fig = go.Figure(go.Funnel(
            y=funnel_data['Stage'],
            x=funnel_data['Count'],
            textinfo="value+percent initial"
        ))
        st.plotly_chart(fig, use_container_width=True)
    
    # ==================== SECTION 5: CONVERSATION HISTORY ==================== #
    st.markdown("<div class='section-header'>💬 Recent Conversations</div>", unsafe_allow_html=True)
    
    if not chat_df.empty:
        # Parse timestamps
        if 'timestamp' in chat_df.columns:
            chat_df['parsed_time'] = chat_df['timestamp'].apply(parse_timestamp)
            recent_chats = chat_df.sort_values('parsed_time', ascending=False).head(10)
        else:
            recent_chats = chat_df.head(10)
        
        for _, row in recent_chats.iterrows():
            sender_name = row.get('sender_name', 'Unknown')
            message_text = row.get('message', 'No message content')
            timestamp = row.get('timestamp', 'N/A')
            is_from_me = is_me(sender_name, row.get('sender_url'), MY_PROFILE)
            
            alignment = "right" if is_from_me else "left"
            bg_color = "#667eea" if is_from_me else "#f8f9fa"
            text_color = "white" if is_from_me else "#2d3748"
            
            st.markdown(f"""
            <div style='display: flex; justify-content: {alignment}; margin: 1rem 0;'>
                <div style='max-width: 70%; background: {bg_color}; color: {text_color}; 
                            padding: 1.5rem; border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                    <div style='font-weight: 700; margin-bottom: 0.5rem;'>{sender_name}</div>
                    <div style='line-height: 1.6;'>{message_text[:200]}...</div>
                    <div style='font-size: 0.85rem; opacity: 0.7; margin-top: 0.5rem;'>{timestamp}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💬 No conversation data available")
    
    # ==================== SECTION 6: QUICK ACTIONS ==================== #
    st.markdown("<div class='section-header'>⚡ Quick Actions & Tools</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📥 Export Daily Tracker", use_container_width=True):
            csv_data = export_to_csv(daily_df)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"daily_tracker_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📥 Export Leads Database", use_container_width=True):
            csv_data = export_to_csv(leads_df)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"leads_database_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("🔄 Refresh All Data", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Data refreshed!")
            st.rerun()
    
    with col4:
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("📊 Report generation feature coming soon!")
    
    # ==================== SECTION 7: PROGRESS SUMMARY ==================== #
    st.markdown("<div class='section-header'>🎯 Progress Summary</div>", unsafe_allow_html=True)
    
    avg_daily = metrics['total_connections_sent'] / current_day if current_day > 0 else 0
    remaining = 1200 - metrics['total_connections_sent']
    days_left = 30 - current_day
    needed_daily = remaining / days_left if days_left > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if avg_daily >= 40:
            st.markdown(f'<div class="success-box">✅ <b>On Track!</b> Daily avg: {avg_daily:.1f}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warning-box">⚠️ <b>Below Target</b> Daily avg: {avg_daily:.1f} (Goal: 40)</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="stage-card"><b>Remaining:</b> {int(remaining)} connections<br><b>Days Left:</b> {days_left}</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div class="stage-card"><b>To reach 1,200:</b><br>{needed_daily:.0f} connections/day</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: white; padding: 20px;'>
        <p><b>🔥 LinkedIn Analytics & Habit Tracker - All-in-One Platform 🔥</b></p>
        <p>⚡ Complete Dashboard | Real-time Analytics | 30-Day Challenge Tracker</p>
        <p style='font-size: 1.1em; margin-top: 15px;'><b>All features combined in one powerful view!</b></p>
    </div>
    """, unsafe_allow_html=True)

# ==================== RUN APPLICATION ==================== #
if __name__ == "__main__":
    main()
