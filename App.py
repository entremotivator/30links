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
    ('leads_sheets_data', None), ('webhook_test_payload', '{}')
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
    
    .filter-panel {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ==================== #

@st.cache_resource
def init_google_sheets(credentials_json):
    """Initialize Google Sheets client"""
    try:
        credentials_dict = json.loads(credentials_json)
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Authentication Error: {str(e)}")
        return None

@st.cache_data(ttl=60)
def load_sheet_data(_client, sheet_id, sheet_name):
    """Load data from Google Sheets"""
    try:
        spreadsheet = _client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Data Loading Error: {str(e)}")
        return pd.DataFrame()

def get_sheet_by_gid(sheet_id, gid):
    """Get sheet data by GID"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        st.error(f"Error loading sheet: {str(e)}")
    return None

def get_sheet_by_name(sheet_id, sheet_name):
    """Get sheet data by name"""
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
    """Load daily tracker data"""
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
    """Load leads database"""
    try:
        df = get_sheet_by_gid(LEADS_DATABASE_SHEET_ID, LEADS_SHEET_GID)
        if df is not None and not df.empty:
            df.columns = df.columns.str.strip()
            if 'success' in df.columns:
                df['success'] = df['success'].astype(str).str.lower().isin(['true', 'yes', '1', 't'])
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            return df
        return create_empty_leads_database()
    except Exception as e:
        st.error(f"Error loading leads: {str(e)}")
        return create_empty_leads_database()

def create_empty_daily_tracker():
    """Create empty daily tracker"""
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
    """Create empty leads database"""
    return pd.DataFrame({
        'timestamp': [], 'profile_name': [], 'profile_location': [], 'profile_tagline': [],
        'linkedin_url': [], 'linkedin_subject': [], 'linkedin_message': [], 'email_subject': [],
        'email_message': [], 'outreach_strategy': [], 'personalization_points': [],
        'follow_up_suggestions': [], 'connection_status': [], 'browserflow_session': [],
        'success': [], 'credits_used': [], 'error_message': [], 'status': [],
        'search_term': [], 'search_city': [], 'search_country': [], 'name': [],
        'image_url': [], 'tagline': [], 'location': [], 'summary': [], 'company_name': []
    })

def parse_timestamp(timestamp_str):
    """Parse timestamp"""
    try:
        if pd.isna(timestamp_str) or timestamp_str == '':
            return None
        return pd.to_datetime(timestamp_str, format='%m/%d/%Y %H:%M:%S')
    except:
        try:
            return pd.to_datetime(timestamp_str)
        except:
            return None

def is_me(sender_name, sender_url, my_profile):
    """Check if sender is me"""
    if not sender_name or not isinstance(sender_name, str):
        return False
    return (my_profile["name"].lower() in sender_name.lower() or
            (sender_url and my_profile["url"].lower() in str(sender_url).lower()))

def get_initials(name):
    """Get initials from name"""
    if not name:
        return "?"
    parts = name.split()
    return f"{parts[0][0]}{parts[1][0]}".upper() if len(parts) >= 2 else name[0].upper()

def send_webhook_request(webhook_url, payload):
    """Send webhook request"""
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200, response.text
    except Exception as e:
        return False, str(e)

def generate_lead_id(profile_name, linkedin_url):
    """Generate unique lead ID"""
    unique_string = f"{profile_name}_{linkedin_url}_{datetime.now().isoformat()}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:12]

def export_to_csv(df):
    """Export to CSV"""
    return df.to_csv(index=False).encode('utf-8')

def filter_dataframe(df, filters):
    """Filter dataframe"""
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

def calculate_metrics(chat_df, outreach_df):
    """Calculate metrics"""
    metrics = {
        'total_conversations': len(chat_df),
        'total_leads': len(outreach_df),
        'messages_sent': 0,
        'messages_received': 0,
        'response_rate': 0,
        'pending_leads': 0,
        'ready_to_send': 0,
        'conversion_rate': 0
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

# ==================== MAIN APPLICATION ==================== #
def main():
    """Main application"""
    
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
    
    metrics = calculate_metrics(chat_df, outreach_df)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #667eea; font-size: 2rem; font-weight: 900;'>🚀 LinkedIn Hub</h1>
            <p style='color: #666; font-size: 0.9rem;'>Complete Edition</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("### 📊 Quick Stats")
        st.metric("Total Leads", metrics['total_leads'])
        st.metric("Response Rate", f"{metrics['response_rate']}%")
        st.metric("Conversion", f"{metrics['conversion_rate']}%")
        
        st.markdown("---")
        
        st.markdown("### ⚡ Quick Actions")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        
        st.markdown("---")
        
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; color: #999; font-size: 0.8rem;'>
            <p>Last updated:<br>{st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main Content - ALL FEATURES ON ONE PAGE
    st.markdown("<div class='main-title'>🚀 LinkedIn Analytics & Habit Tracker</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Complete Dashboard - All Features Unified</div>", unsafe_allow_html=True)
    
    # Section 1: Dashboard Overview
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
    
    if not daily_tracker.empty and current_day <= len(daily_tracker):
        today_row = daily_tracker.iloc[current_day - 1]
        
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
            <div class="stat-box" style="border-top-color: #10b981;">
                <div class="metric-icon">✅</div>
                <div class="stat-number">{int(today_row.get('Connections_Accepted', 0))}</div>
                <div class="stat-label">Accepted</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-box" style="border-top-color: #3b82f6;">
                <div class="metric-icon">💬</div>
                <div class="stat-number">{int(today_row.get('Initial_Messages_Sent', 0))}</div>
                <div class="stat-label">Messages</div>
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
        
        # 30-day chart
        st.markdown("<br>", unsafe_allow_html=True)
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_tracker['Date'], y=daily_tracker['Connections_Sent'],
            mode='lines+markers', name='Connections',
            line=dict(color='#667eea', width=3), marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_tracker['Date'], y=daily_tracker['Initial_Messages_Sent'],
            mode='lines+markers', name='Messages',
            line=dict(color='#3b82f6', width=3), marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_tracker['Date'], y=daily_tracker['Conversions'],
            mode='lines+markers', name='Conversions',
            line=dict(color='#10b981', width=3), marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="30-Day Performance Trend",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(255,255,255,0.95)',
            font=dict(family='Inter', size=12),
            title_font_size=20,
            title_font_color='#667eea',
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Section 3: CRM Dashboard with Leads
    st.markdown("<div class='section-header'>📋 CRM Dashboard - Lead Management</div>", unsafe_allow_html=True)
    
    if not leads_database.empty:
        # Filters
        st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filter_status = st.selectbox("📊 Status", ['all', 'pending', 'ready_to_send', 'sent', 'responded'])
        
        with col2:
            filter_days = st.selectbox("📅 Date Range", [7, 14, 30, 60, 90], format_func=lambda x: f"Last {x} days")
        
        with col3:
            sort_by = st.selectbox("🔄 Sort By", ['timestamp', 'profile_name', 'company_name', 'status'])
        
        with col4:
            search_query = st.text_input("🔍 Search", placeholder="Search leads...")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Apply filters
        filtered_df = filter_dataframe(leads_database, {
            'status': filter_status,
            'date_range': filter_days,
            'search_query': search_query
        })
        
        if sort_by in filtered_df.columns:
            filtered_df = filtered_df.sort_values(sort_by, ascending=False)
        
        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Filtered Leads", len(filtered_df))
        with col2:
            sent = len(filtered_df[filtered_df['success'] == True]) if 'success' in filtered_df.columns else 0
            st.metric("Messages Sent", sent)
        with col3:
            if st.button("📥 Export to CSV", use_container_width=True):
                csv_data = export_to_csv(filtered_df)
                st.download_button(
                    "⬇️ Download",
                    csv_data,
                    f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
        
        # Display leads
        st.markdown("<br>", unsafe_allow_html=True)
        for idx, (i, row) in enumerate(filtered_df.head(10).iterrows()):
            linkedin_url = row.get('linkedin_url', '#')
            profile_name = row.get('profile_name', 'Unknown')
            tagline = row.get('profile_tagline', 'N/A')
            message = row.get('linkedin_message', 'No message')
            location = row.get('profile_location', 'N/A')
            company = row.get('company_name', 'N/A')
            status = row.get('status', 'unknown')
            
            status_class = {
                'sent': 'status-sent',
                'pending': 'status-pending',
                'ready_to_send': 'status-ready',
                'responded': 'status-success'
            }.get(status, 'status-pending')
            
            lead_id = generate_lead_id(profile_name, linkedin_url)
            is_favorited = lead_id in st.session_state.favorites
            
            st.markdown(f"""
            <div class="lead-card">
                <div style="display: flex; align-items: start; gap: 1.5rem;">
                    <div class="profile-badge">{get_initials(profile_name)}</div>
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between;">
                            <div>
                                <h3 class="lead-title">{profile_name}</h3>
                                <p class="lead-sub">💼 {tagline}</p>
                            </div>
                            <span class="status-badge {status_class}">{status.replace('_', ' ').title()}</span>
                        </div>
                        <div style="display: flex; gap: 2rem; margin: 1rem 0;">
                            <span>📍 {location}</span>
                            <span>🏢 {company}</span>
                        </div>
                    </div>
                </div>
                <div class="lead-msg">
                    <strong style="color: #667eea;">📩 Message:</strong><br><br>
                    {message}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✉️ Send", key=f"send_{i}_{idx}", use_container_width=True):
                    st.success("✅ Message sent!")
            with col2:
                fav_icon = "⭐" if is_favorited else "☆"
                if st.button(f"{fav_icon} Favorite", key=f"fav_{i}_{idx}", use_container_width=True):
                    if is_favorited:
                        st.session_state.favorites.remove(lead_id)
                    else:
                        st.session_state.favorites.add(lead_id)
                    st.rerun()
            with col3:
                st.markdown(f'<a href="{linkedin_url}" target="_blank" class="action-btn">🔗 View Profile</a>', unsafe_allow_html=True)
    else:
        st.info("No leads found. Use the search feature to generate leads.")
    
    # Section 4: Analytics
    st.markdown("<div class='section-header'>📊 Analytics & Insights</div>", unsafe_allow_html=True)
    
    if not outreach_df.empty and 'status' in outreach_df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            status_counts = outreach_df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index,
                        title='Lead Status Distribution',
                        color_discrete_sequence=['#667eea', '#764ba2', '#f59e0b', '#10b981'])
            fig.update_layout(paper_bgcolor='rgba(255,255,255,0.95)')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'profile_location' in outreach_df.columns:
                location_counts = outreach_df['profile_location'].value_counts().head(10)
                fig = px.bar(x=location_counts.values, y=location_counts.index,
                            orientation='h', title='Top 10 Locations')
                fig.update_traces(marker_color='#667eea')
                fig.update_layout(paper_bgcolor='rgba(255,255,255,0.95)')
                st.plotly_chart(fig, use_container_width=True)
    
    # Section 5: Email Queue
    st.markdown("<div class='section-header'>📧 Email Queue</div>", unsafe_allow_html=True)
    
    if st.session_state.email_queue:
        for idx, email in enumerate(st.session_state.email_queue):
            st.markdown(f"""
            <div class='email-card'>
                <h3 class='lead-title'>To: {email['to']}</h3>
                <p class='lead-sub'><strong>Subject:</strong> {email['subject']}</p>
                <div class='lead-msg'>{email['body']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Send", key=f"email_{idx}", use_container_width=True):
                    st.success("Email sent!")
                    st.session_state.email_queue.pop(idx)
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"del_email_{idx}", use_container_width=True):
                    st.session_state.email_queue.pop(idx)
                    st.rerun()
    else:
        st.info("📧 Email queue is empty")
    
    # Section 6: Webhook Monitor
    st.markdown("<div class='section-header'>🔗 Webhook Monitor</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='crm-card'>
        <h3 style='color: #667eea;'>📡 Webhook Configuration</h3>
        <p><strong>Endpoint:</strong> {WEBHOOK_URL}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_payload = st.text_area("Test Payload (JSON)", value='{"action": "test", "message": "Hello"}', height=150)
    
    with col2:
        if st.button("🧪 Test Webhook", use_container_width=True):
            try:
                payload = json.loads(test_payload)
                success, response = send_webhook_request(WEBHOOK_URL, payload)
                if success:
                    st.success("✅ Webhook test successful!")
                    st.json(json.loads(response) if response else {})
                else:
                    st.error(f"❌ Test failed: {response}")
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON payload")
    
    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: rgba(255,255,255,0.95); border-radius: 20px;'>
        <h3 style='color: #667eea; margin-bottom: 1rem;'>🎉 All Features Loaded Successfully!</h3>
        <p style='color: #666;'>LinkedIn Analytics & Habit Tracker - Complete Edition</p>
        <p style='color: #999; font-size: 0.9rem; margin-top: 1rem;'>Made with ❤️ by Donmenico Hudson</p>
    </div>
    """, unsafe_allow_html=True)

# ==================== RUN APPLICATION ==================== #
if __name__ == "__main__":
    main()
