import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import json
from collections import defaultdict
import hashlib
import time
import re

# Page configuration
st.set_page_config(
    page_title="LinkedIn Outreach & Habit Tracker Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
<style>
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
    .habit-green {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
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
    .gold-card {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
    }
    .stage-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #0077B5;
        margin: 10px 0;
    }
    .habit-card {
        background-color: #f0f9ff;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #38ef7d;
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
    .streak-badge {
        display: inline-block;
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        margin: 5px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
    }
    .habit-complete {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .habit-incomplete {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets Configuration
DAILY_TRACKER_SHEET_ID = "1UkuTf8VwGPIilTxhTEdP9K-zdtZFnThazFdGyxVYfmg"
LEADS_DATABASE_SHEET_ID = "1eLEFvyV1_f74UC1g5uQ-xA7A62sK8Pog27KIjw_Sk3Y"
DAILY_TRACKER_SHEET_NAME = "daily_tracker_20251021"
LEADS_SHEET_GID = "1881909623"  # linkedin-tracking-csv.csv sheet

# Function to get sheet data by GID
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

# Function to get sheet data by name
def get_sheet_by_name(sheet_id, sheet_name):
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

# Load daily tracker data
@st.cache_data(ttl=60)
def load_daily_tracker():
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

# Load leads database
@st.cache_data(ttl=60)
def load_leads_database():
    """Load leads database from linkedin-tracking-csv.csv sheet (GID: 1881909623)"""
    try:
        df = get_sheet_by_gid(LEADS_DATABASE_SHEET_ID, LEADS_SHEET_GID)

        if df is not None and not df.empty:
            df.columns = df.columns.str.strip()

            expected_columns = [
                'timestamp', 'name', 'profile_name', 'profile_location', 'profile_tagline',
                'linkedin_url', 'linkedin_subject', 'linkedin_message',
                'email_subject', 'email_message', 'outreach_strategy',
                'personalization_points', 'follow_up_suggestions', 'connection_status',
                'browserflow_session', 'success', 'credits_used', 'error_message',
                'status', 'search_term', 'search_city', 'search_country',
                'image_url', 'tagline', 'location', 'summary'
            ]

            available_columns = [col for col in expected_columns if col in df.columns]

            if available_columns:
                df = df[available_columns]

            if 'name' not in df.columns and 'profile_name' in df.columns:
                df['name'] = df['profile_name']
            elif 'profile_name' not in df.columns and 'name' in df.columns:
                df['profile_name'] = df['name']

            if 'success' in df.columns:
                df['success'] = df['success'].astype(str).str.lower().isin(['true', 'yes', '1', 't'])

            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

            if 'credits_used' in df.columns:
                df['credits_used'] = pd.to_numeric(df['credits_used'], errors='coerce').fillna(0)

            return df

        return create_empty_leads_database()
    except Exception as e:
        st.sidebar.error(f"Error loading leads from linkedin-tracking-csv.csv: {str(e)}")
        return create_empty_leads_database()

# Create empty dataframes
def create_empty_daily_tracker():
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
        'timestamp': [],
        'name': [],  # Added 'name' as primary field
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
        'image_url': [],
        'tagline': [],
        'location': [],
        'summary': []
    })

def create_empty_habits():
    """Create empty habits dataframe"""
    return pd.DataFrame({
        'Habit_Name': [],
        'Category': [],
        'Target_Frequency': [],
        'Current_Streak': [],
        'Longest_Streak': [],
        'Total_Completions': [],
        'Success_Rate': [],
        'Created_Date': [],
        'Active': []
    })

def create_empty_habit_log():
    """Create empty habit log dataframe"""
    dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
    return pd.DataFrame({
        'Date': dates,
        'Morning_Routine': [False] * 30,
        'LinkedIn_Outreach': [False] * 30,
        'Exercise': [False] * 30,
        'Reading': [False] * 30,
        'Meditation': [False] * 30,
        'Deep_Work': [False] * 30,
        'Networking': [False] * 30,
        'Learning': [False] * 30,
        'Content_Creation': [False] * 30,
        'Gratitude_Journal': [False] * 30,
        'Notes': [''] * 30
    })

# Initialize session state
if 'daily_tracker' not in st.session_state:
    st.session_state.daily_tracker = load_daily_tracker()

if 'leads_database' not in st.session_state:
    st.session_state.leads_database = create_empty_leads_database()

if 'habits' not in st.session_state:
    st.session_state.habits = create_empty_habits()

if 'habit_log' not in st.session_state:
    st.session_state.habit_log = create_empty_habit_log()

if 'challenge_start_date' not in st.session_state:
    st.session_state.challenge_start_date = datetime.now().strftime("%Y-%m-%d")

if 'sheets_data' not in st.session_state:
    st.session_state.sheets_data = None

if 'leads_sheets_data' not in st.session_state:
    st.session_state.leads_sheets_data = None

# CRM-specific session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'gsheets_client' not in st.session_state:
    st.session_state.gsheets_client = None

if 'activity_log' not in st.session_state:
    st.session_state.activity_log = []

if 'sent_leads' not in st.session_state:
    st.session_state.sent_leads = set()

if 'selected_leads' not in st.session_state:
    st.session_state.selected_leads = []

if 'current_client' not in st.session_state:
    st.session_state.current_client = None

if 'webhook_history' not in st.session_state:
    st.session_state.webhook_history = []

if 'email_queue' not in st.session_state:
    st.session_state.email_queue = []

if 'show_notifications' not in st.session_state:
    st.session_state.show_notifications = True

if 'selected_contact' not in st.session_state:
    st.session_state.selected_contact = None

if 'filter_status' not in st.session_state:
    st.session_state.filter_status = 'all'

if 'filter_date_range' not in st.session_state:
    st.session_state.filter_date_range = 7

if 'sort_by' not in st.session_state:
    st.session_state.sort_by = 'timestamp'

if 'search_query' not in st.session_state:
    st.session_state.search_query = ''

if 'favorites' not in st.session_state:
    st.session_state.favorites = set()

if 'notes' not in st.session_state:
    st.session_state.notes = {}

if 'tags' not in st.session_state:
    st.session_state.tags = {}

if 'export_format' not in st.session_state:
    st.session_state.export_format = 'csv'

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 60

# CRM Configuration
WEBHOOK_URL = "https://agentonline-u29564.vm.elestio.app/webhook/Leadlinked"
MY_PROFILE = {"name": "Donmenico Hudson", "url": "https://www.linkedin.com/in/donmenicohudson/"}

# CRM helper functions
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

def generate_lead_id(name, linkedin_url):
    """Generate unique lead ID using name instead of profile_name"""
    unique_string = f"{name}_{linkedin_url}_{datetime.now().isoformat()}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:12]

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

def calculate_metrics(chat_df, outreach_df):
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


# Helper functions
def get_current_day():
    days_elapsed = (datetime.now() - datetime.strptime(st.session_state.challenge_start_date, "%Y-%m-%d")).days + 1
    return min(max(days_elapsed, 1), 30)

def calculate_streak(habit_log, habit_name):
    """Calculate current streak for a habit"""
    if habit_name not in habit_log.columns:
        return 0

    streak = 0
    for i in range(len(habit_log) - 1, -1, -1):
        if habit_log.iloc[i][habit_name]:
            streak += 1
        else:
            break
    return streak

def calculate_success_rate(habit_log, habit_name):
    """Calculate success rate for a habit"""
    if habit_name not in habit_log.columns:
        return 0.0

    total_days = len(habit_log)
    completed_days = habit_log[habit_name].sum()
    return (completed_days / total_days * 100) if total_days > 0 else 0.0

# Title
st.markdown('''
<div class="linkedin-blue">
    <h1>🚀 LinkedIn Outreach & Habit Tracker Pro</h1>
    <p>Complete Productivity System: 30-Day LinkedIn Challenge + Daily Habit Tracking + Performance Analytics</p>
</div>
''', unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ Control Center")

# Sync status
st.sidebar.subheader("☁️ Google Sheets Sync")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("⬇️ Load Sheets", use_container_width=True):
        st.cache_data.clear()
        with st.spinner("Loading data..."):
            daily_data = load_daily_tracker()
            leads_data = load_leads_database()

            if daily_data is not None and not daily_data.empty:
                st.session_state.sheets_data = daily_data
                st.sidebar.success(f"✅ Daily: {len(daily_data)} rows")
            else:
                st.sidebar.warning("⚠️ No daily tracker data")

            if leads_data is not None and not leads_data.empty:
                st.session_state.leads_sheets_data = leads_data
                st.sidebar.success(f"✅ Leads: {len(leads_data)} rows")
            else:
                st.sidebar.warning("⚠️ No leads data")
        st.rerun()

with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Debug info
with st.sidebar.expander("🔍 Connection Info", expanded=False):
    st.caption(f"**Daily Tracker ID:** {DAILY_TRACKER_SHEET_ID}")
    st.caption(f"**Sheet Name:** {DAILY_TRACKER_SHEET_NAME}")
    st.caption(f"**Leads DB ID:** {LEADS_DATABASE_SHEET_ID}")
    st.caption(f"**Leads Sheet GID:** {LEADS_SHEET_GID}")

st.sidebar.markdown("---")

# Quick Links
st.sidebar.markdown("### 🔗 Quick Links")
st.sidebar.markdown(f"[📈 Daily Tracker Sheet](https://docs.google.com/spreadsheets/d/{DAILY_TRACKER_SHEET_ID}/edit)")
st.sidebar.markdown(f"[👥 Leads Database Sheet](https://docs.google.com/spreadsheets/d/{LEADS_DATABASE_SHEET_ID}/edit?gid={LEADS_SHEET_GID})")

st.sidebar.markdown("---")

# Load data
daily_df = st.session_state.sheets_data if st.session_state.sheets_data is not None else st.session_state.daily_tracker
leads_df = st.session_state.leads_sheets_data if st.session_state.leads_sheets_data is not None else load_leads_database()
habit_log = st.session_state.habit_log

# Challenge info
current_day = get_current_day()
st.sidebar.markdown("### 📊 Challenge Overview")
st.sidebar.markdown(f"**📅 Day {current_day} of 30**")
st.sidebar.progress(current_day / 30)
st.sidebar.markdown(f"**Started:** {st.session_state.challenge_start_date}")

# Quick stats - LinkedIn
total_sent = daily_df['Connections_Sent'].sum() if 'Connections_Sent' in daily_df.columns else 0
total_accepted = daily_df['Connections_Accepted'].sum() if 'Connections_Accepted' in daily_df.columns else 0
total_interested = daily_df['Interested_Responses'].sum() if 'Interested_Responses' in daily_df.columns else 0
total_conversions = daily_df['Conversions'].sum() if 'Conversions' in daily_df.columns else 0

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 LinkedIn Progress")
st.sidebar.metric("Connections Sent", f"{int(total_sent)}/1,200", f"{int(total_sent/12)}%")
st.sidebar.metric("Accepted", int(total_accepted))
st.sidebar.metric("Interested", int(total_interested))
st.sidebar.metric("Conversions", int(total_conversions))

# Quick stats - Habits
st.sidebar.markdown("---")
st.sidebar.markdown("### ✅ Habit Streaks")

# Calculate today's habit completion
today_date = datetime.now().strftime("%Y-%m-%d")
today_habits = habit_log[habit_log['Date'] == today_date]

if not today_habits.empty:
    habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]
    completed_today = sum([today_habits.iloc[0][col] for col in habit_columns if col in today_habits.columns])
    total_habits = len(habit_columns)

    st.sidebar.metric("Today's Habits", f"{completed_today}/{total_habits}")
    st.sidebar.progress(completed_today / total_habits if total_habits > 0 else 0)

    # Show top streaks
    for habit in habit_columns[:3]:
        if habit in habit_log.columns:
            streak = calculate_streak(habit_log, habit)
            if streak > 0:
                st.sidebar.markdown(f"🔥 **{habit.replace('_', ' ')}:** {streak} days")

st.sidebar.markdown("---")

# Export/Import
st.sidebar.markdown("### 💾 Data Management")

csv_daily = io.StringIO()
daily_df.to_csv(csv_daily, index=False)
st.sidebar.download_button(
    label="📥 Download Daily Tracker",
    data=csv_daily.getvalue(),
    file_name=f"daily_tracker_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=True
)

csv_habits = io.StringIO()
habit_log.to_csv(csv_habits, index=False)
st.sidebar.download_button(
    label="📥 Download Habit Log",
    data=csv_habits.getvalue(),
    file_name=f"habit_log_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=True
)

# Main Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
    "🏠 Dashboard",
    "📅 Daily Tracker",
    "✅ Habit Tracker",
    "👥 Leads CRM",
    "🔍 Advanced Search",
    "💬 Conversations",
    "📧 Email Queue",
    "📊 Analytics Hub",
    "🎯 Daily Checklist",
    "🔥 Streaks & Rewards",
    "🔗 Webhook Monitor",
    "⚙️ Settings"
])

# TAB 1: UNIFIED DASHBOARD
with tab1:
    st.markdown("## 🏠 Unified Performance Dashboard")
    st.markdown("*Your complete productivity overview in one place*")

    # Top-level metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("### 🔗 Sent")
        st.markdown(f"<div class='big-metric'>{int(total_sent)}</div>", unsafe_allow_html=True)
        st.markdown(f"<center>Goal: 1,200</center>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card success-card">', unsafe_allow_html=True)
        st.markdown("### ✅ Accepted")
        st.markdown(f"<div class='big-metric'>{int(total_accepted)}</div>", unsafe_allow_html=True)
        acceptance = (total_accepted/total_sent*100) if total_sent > 0 else 0
        st.markdown(f"<center>{acceptance:.1f}% rate</center>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card info-card">', unsafe_allow_html=True)
        st.markdown("### 💡 Interested")
        st.markdown(f"<div class='big-metric'>{int(total_interested)}</div>", unsafe_allow_html=True)
        st.markdown(f"<center>Want checklist</center>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="metric-card warning-card">', unsafe_allow_html=True)
        st.markdown("### 🎉 Conversions")
        st.markdown(f"<div class='big-metric'>{int(total_conversions)}</div>", unsafe_allow_html=True)
        conv_rate = (total_conversions/total_interested*100) if total_interested > 0 else 0
        st.markdown(f"<center>{conv_rate:.1f}% rate</center>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        # Habit completion metric
        habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]
        total_possible = len(habit_log) * len(habit_columns)
        total_completed = sum([habit_log[col].sum() for col in habit_columns if col in habit_log.columns])
        overall_rate = (total_completed / total_possible * 100) if total_possible > 0 else 0

        st.markdown('<div class="metric-card gold-card">', unsafe_allow_html=True)
        st.markdown("### 🏆 Habits")
        st.markdown(f"<div class='big-metric'>{overall_rate:.0f}%</div>", unsafe_allow_html=True)
        st.markdown(f"<center>Overall completion</center>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Today's snapshot
    st.markdown("## 📸 Today's Snapshot")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🔗 LinkedIn Activity Today")
        today_idx = current_day - 1
        if today_idx < len(daily_df):
            today_data = daily_df.iloc[today_idx]

            subcol1, subcol2, subcol3, subcol4 = st.columns(4)
            with subcol1:
                st.metric("Sent", int(today_data.get('Connections_Sent', 0)), "Goal: 40")
            with subcol2:
                st.metric("Accepted", int(today_data.get('Connections_Accepted', 0)))
            with subcol3:
                st.metric("Messaged", int(today_data.get('Initial_Messages_Sent', 0)))
            with subcol4:
                st.metric("Conversions", int(today_data.get('Conversions', 0)))

    with col2:
        st.markdown("### ✅ Habit Completion Today")
        today_date = datetime.now().strftime("%Y-%m-%d")
        today_habits = habit_log[habit_log['Date'] == today_date]

        if not today_habits.empty:
            habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]

            completed = []
            incomplete = []

            for habit in habit_columns:
                if habit in today_habits.columns:
                    if today_habits.iloc[0][habit]:
                        completed.append(habit.replace('_', ' '))
                    else:
                        incomplete.append(habit.replace('_', ' '))

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**✅ Completed:**")
                for h in completed:
                    st.markdown(f"- {h}")
            with col_b:
                st.markdown("**⏳ Pending:**")
                for h in incomplete:
                    st.markdown(f"- {h}")

    st.markdown("---")

    # Combined performance chart
    st.markdown("## 📈 30-Day Performance Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### LinkedIn Outreach Trend")
        if 'Date' in daily_df.columns:
            fig = px.line(daily_df, x='Date',
                         y=['Connections_Sent', 'Connections_Accepted', 'Conversions'],
                         title='Daily LinkedIn Performance',
                         labels={'value': 'Count', 'variable': 'Metric'})
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Daily Habit Completion Rate")
        habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]
        habit_log_copy = habit_log.copy()
        habit_log_copy['Completion_Rate'] = habit_log_copy[habit_columns].sum(axis=1) / len(habit_columns) * 100
        fig = px.line(habit_log_copy, x='Date', y='Completion_Rate',
                     title='Daily Habit Completion %',
                     labels={'Completion_Rate': 'Completion %'})
        fig.add_hline(y=80, line_dash="dash", line_color="green",
                     annotation_text="80% Target")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Weekly summary
    st.markdown("## 📊 Weekly Performance Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### LinkedIn Weekly Totals")
        if 'Day' in daily_df.columns:
            df_weekly = daily_df.copy()
            df_weekly['Week'] = ((df_weekly['Day'] - 1) // 7) + 1

            weekly_summary = df_weekly.groupby('Week').agg({
                'Connections_Sent': 'sum',
                'Connections_Accepted': 'sum',
                'Interested_Responses': 'sum',
                'Conversions': 'sum'
            }).reset_index()

            weekly_summary['Week'] = 'Week ' + weekly_summary['Week'].astype(str)
            st.dataframe(weekly_summary, use_container_width=True)

    with col2:
        st.markdown("### Habit Weekly Averages")
        habit_log_copy = habit_log.copy()
        habit_log_copy['Week'] = (pd.to_datetime(habit_log_copy['Date']) - pd.to_datetime(habit_log_copy['Date'].min())).dt.days // 7 + 1

        habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes', 'Week']]
        weekly_habits = habit_log_copy.groupby('Week')[habit_columns].mean() * 100
        weekly_habits = weekly_habits.round(1)
        weekly_habits.index = 'Week ' + weekly_habits.index.astype(str)

        st.dataframe(weekly_habits.T, use_container_width=True)

    st.markdown("---")

    # Progress indicators
    st.markdown("## 🎯 Goal Progress")

    col1, col2, col3 = st.columns(3)

    with col1:
        avg_daily = total_sent / current_day if current_day > 0 else 0
        if avg_daily >= 40:
            st.markdown(f'<div class="success-box">✅ <b>LinkedIn On Track!</b> Daily avg: {avg_daily:.1f}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warning-box">⚠️ <b>Below Target</b> Daily avg: {avg_daily:.1f} (Goal: 40)</div>', unsafe_allow_html=True)

    with col2:
        if overall_rate >= 80:
            st.markdown(f'<div class="success-box">✅ <b>Habits Excellent!</b> {overall_rate:.0f}% completion</div>', unsafe_allow_html=True)
        elif overall_rate >= 60:
            st.markdown(f'<div class="warning-box">⚠️ <b>Habits Good</b> {overall_rate:.0f}% completion</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warning-box">⚠️ <b>Habits Need Work</b> {overall_rate:.0f}% completion</div>', unsafe_allow_html=True)

    with col3:
        remaining = 1200 - total_sent
        days_left = 30 - current_day
        needed_daily = remaining / days_left if days_left > 0 else 0
        st.markdown(f'<div class="stage-card"><b>To reach 1,200:</b> {needed_daily:.0f}/day for {days_left} days</div>', unsafe_allow_html=True)

# TAB 2: DAILY TRACKER (LinkedIn)
with tab2:
    st.markdown("## 📅 LinkedIn Daily Activity Tracker")

    st.markdown("### ⚡ Quick Entry - Today")

    today_idx = current_day - 1
    if today_idx < len(daily_df):
        col1, col2, col3 = st.columns(3)

        with col1:
            conn_today = st.number_input("Connections Sent", 0, 100,
                                        int(daily_df.loc[today_idx, 'Connections_Sent']) if 'Connections_Sent' in daily_df.columns else 0,
                                        key="today_conn")
            acc_today = st.number_input("Accepted", 0, 100,
                                       int(daily_df.loc[today_idx, 'Connections_Accepted']) if 'Connections_Accepted' in daily_df.columns else 0,
                                       key="today_acc")

        with col2:
            msg_today = st.number_input("Messages Sent", 0, 100,
                                       int(daily_df.loc[today_idx, 'Initial_Messages_Sent']) if 'Initial_Messages_Sent' in daily_df.columns else 0,
                                       key="today_msg")
            int_today = st.number_input("Interested", 0, 100,
                                       int(daily_df.loc[today_idx, 'Interested_Responses']) if 'Interested_Responses' in daily_df.columns else 0,
                                       key="today_int")

        with col3:
            link_today = st.number_input("Links Sent", 0, 100,
                                        int(daily_df.loc[today_idx, 'Links_Sent']) if 'Links_Sent' in daily_df.columns else 0,
                                        key="today_link")
            conv_today = st.number_input("Conversions", 0, 100,
                                        int(daily_df.loc[today_idx, 'Conversions']) if 'Conversions' in daily_df.columns else 0,
                                        key="today_conv")

        notes_today = st.text_area("Today's Notes",
                                   daily_df.loc[today_idx, 'Notes'] if 'Notes' in daily_df.columns else "",
                                   key="today_notes")

        if st.button("💾 Save Today's LinkedIn Progress", type="primary", use_container_width=True):
            daily_df.loc[today_idx, 'Connections_Sent'] = conn_today
            daily_df.loc[today_idx, 'Connections_Accepted'] = acc_today
            daily_df.loc[today_idx, 'Initial_Messages_Sent'] = msg_today
            daily_df.loc[today_idx, 'Interested_Responses'] = int_today
            daily_df.loc[today_idx, 'Links_Sent'] = link_today
            daily_df.loc[today_idx, 'Conversions'] = conv_today
            daily_df.loc[today_idx, 'Notes'] = notes_today
            st.session_state.daily_tracker = daily_df
            st.success("✅ LinkedIn progress saved!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Full 30-Day LinkedIn View")
    st.dataframe(daily_df, use_container_width=True, height=400)

    st.markdown("---")
    st.markdown("### 📈 LinkedIn Performance Charts")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(daily_df, x='Day', y='Connections_Sent',
                    title='Daily Connections Sent',
                    labels={'Connections_Sent': 'Connections'})
        fig.add_hline(y=40, line_dash="dash", line_color="red",
                     annotation_text="Daily Goal: 40")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily_df['Day'], y=daily_df['Connections_Sent'].cumsum(),
                                name='Sent', mode='lines+markers'))
        fig.add_trace(go.Scatter(x=daily_df['Day'], y=daily_df['Connections_Accepted'].cumsum(),
                                name='Accepted', mode='lines+markers'))
        fig.add_hline(y=1200, line_dash="dash", line_color="green",
                     annotation_text="Goal: 1,200")
        fig.update_layout(title='Cumulative Progress', xaxis_title='Day', yaxis_title='Count')
        st.plotly_chart(fig, use_container_width=True)

# TAB 3: HABIT TRACKER
with tab3:
    st.markdown("## ✅ Daily Habit Tracker")
    st.markdown("*Build consistency, track streaks, achieve your goals*")

    # Today's habit check-in
    st.markdown("### 🎯 Today's Habit Check-In")
    st.markdown(f"**Date:** {datetime.now().strftime('%A, %B %d, %Y')}")

    today_date = datetime.now().strftime("%Y-%m-%d")
    today_idx = habit_log[habit_log['Date'] == today_date].index

    if len(today_idx) > 0:
        today_idx = today_idx[0]

        habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]

        # Create habit checkboxes in a grid
        cols_per_row = 3
        for i in range(0, len(habit_columns), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(habit_columns):
                    habit = habit_columns[i + j]
                    habit_display = habit.replace('_', ' ').title()

                    current_value = habit_log.loc[today_idx, habit] if habit in habit_log.columns else False
                    streak = calculate_streak(habit_log, habit)
                    success_rate = calculate_success_rate(habit_log, habit)

                    with col:
                        st.markdown(f"**{habit_display}**")
                        new_value = st.checkbox(
                            f"Complete",
                            value=bool(current_value),
                            key=f"habit_{habit}",
                            label_visibility="collapsed"
                        )

                        if new_value != current_value:
                            habit_log.loc[today_idx, habit] = new_value
                            st.session_state.habit_log = habit_log

                        if streak > 0:
                            st.markdown(f'<span class="streak-badge">🔥 {streak} day streak</span>', unsafe_allow_html=True)
                        st.caption(f"Success rate: {success_rate:.0f}%")

        st.markdown("---")

        # Today's notes
        today_notes = st.text_area(
            "Today's Reflection & Notes",
            value=habit_log.loc[today_idx, 'Notes'] if 'Notes' in habit_log.columns else "",
            key="habit_notes_today",
            height=100
        )

        if st.button("💾 Save Today's Habits", type="primary", use_container_width=True):
            habit_log.loc[today_idx, 'Notes'] = today_notes
            st.session_state.habit_log = habit_log
            st.success("✅ Habits saved successfully!")
            st.rerun()

    st.markdown("---")

    # Habit overview
    st.markdown("### 📊 Habit Overview & Statistics")

    habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]

    # Create summary statistics
    habit_stats = []
    for habit in habit_columns:
        if habit in habit_log.columns:
            streak = calculate_streak(habit_log, habit)
            success_rate = calculate_success_rate(habit_log, habit)
            total_completions = habit_log[habit].sum()

            # Calculate longest streak
            longest_streak = 0
            current_streak = 0
            for val in habit_log[habit]:
                if val:
                    current_streak += 1
                    longest_streak = max(longest_streak, current_streak)
                else:
                    current_streak = 0

            habit_stats.append({
                'Habit': habit.replace('_', ' ').title(),
                'Current Streak': streak,
                'Longest Streak': longest_streak,
                'Total Completions': int(total_completions),
                'Success Rate': f"{success_rate:.1f}%"
            })

    habit_stats_df = pd.DataFrame(habit_stats)
    st.dataframe(habit_stats_df, use_container_width=True)

    st.markdown("---")

    # Habit heatmap
    st.markdown("### 🔥 30-Day Habit Heatmap")

    # Prepare data for heatmap
    habit_heatmap_data = habit_log[habit_columns].T
    habit_heatmap_data.index = [idx.replace('_', ' ').title() for idx in habit_heatmap_data.index]

    fig = px.imshow(
        habit_heatmap_data,
        labels=dict(x="Day", y="Habit", color="Completed"),
        title="Habit Completion Heatmap (Green = Completed, Purple = Missed)",
        aspect="auto",
        color_continuous_scale=["#f093fb", "#38ef7d"]
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Individual habit trends
    st.markdown("### 📈 Individual Habit Trends")

    selected_habits = st.multiselect(
        "Select habits to compare",
        options=[h.replace('_', ' ').title() for h in habit_columns],
        default=[habit_columns[0].replace('_', ' ').title()] if habit_columns else []
    )

    if selected_habits:
        # Convert back to column names
        selected_cols = [h.replace(' ', '_').upper() if h.replace(' ', '_').upper() in habit_columns
                        else h.replace(' ', '_').title() if h.replace(' ', '_').title() in habit_columns
                        else h.replace(' ', '_') for h in selected_habits]

        # Create cumulative completion chart
        fig = go.Figure()
        for habit in selected_cols:
            if habit in habit_log.columns:
                cumulative = habit_log[habit].cumsum()
                fig.add_trace(go.Scatter(
                    x=list(range(1, len(cumulative) + 1)),
                    y=cumulative,
                    mode='lines+markers',
                    name=habit.replace('_', ' ').title()
                ))

        fig.update_layout(
            title='Cumulative Habit Completions',
            xaxis_title='Day',
            yaxis_title='Total Completions'
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Full habit log
    st.markdown("### 📋 Complete Habit Log")
    st.dataframe(habit_log, use_container_width=True, height=400)

# TAB 4: LEADS CRM
with tab4:
    st.markdown("## 👥 Leads CRM - From Google Sheets")
    st.caption("Data from linkedin-tracking-csv.csv sheet (GID: 1881909623)")

    if leads_df is not None and not leads_df.empty:
        st.success(f"✅ Loaded {len(leads_df)} leads from linkedin-tracking-csv.csv")

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

        st.markdown("---")

        # Filter options
        st.markdown("### 🔍 Filter & Search")

        col1, col2, col3 = st.columns(3)

        with col1:
            success_filter = st.selectbox("Success Status",
                ["All", "Successful Only", "Pending"],
                key="success_filter")

        with col2:
            if 'connection_status' in leads_df.columns:
                status_options = ["All"] + list(leads_df['connection_status'].dropna().unique())
                status_filter = st.selectbox("Connection Status", status_options)
            else:
                status_filter = "All"

        with col3:
            if 'search_term' in leads_df.columns:
                search_terms = ["All"] + list(leads_df['search_term'].dropna().unique())
                search_filter = st.selectbox("Search Term", search_terms)
            else:
                search_filter = "All"

        # Apply filters
        filtered_df = leads_df.copy()

        if success_filter == "Successful Only" and 'success' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['success'] == True]
        elif success_filter == "Pending" and 'success' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['success'] == False]

        if status_filter != "All" and 'connection_status' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['connection_status'] == status_filter]

        if search_filter != "All" and 'search_term' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['search_term'] == search_filter]

        st.info(f"📊 Showing {len(filtered_df)} of {len(leads_df)} leads")

        st.markdown("---")

        # Display leads
        st.markdown("### 📋 Lead Records")

        display_cols = []
        priority_display = [
            'timestamp', 'name', 'profile_name', 'profile_location', 'location',
            'profile_tagline', 'tagline', 'linkedin_url', 'connection_status',
            'success', 'search_term', 'outreach_strategy'
        ]

        for col in priority_display:
            if col in filtered_df.columns:
                display_cols.append(col)

        if display_cols:
            st.dataframe(
                filtered_df[display_cols],
                use_container_width=True,
                height=500
            )
        else:
            st.dataframe(filtered_df, use_container_width=True, height=500)

        # Export filtered data
        st.markdown("---")
        csv_filtered = io.StringIO()
        filtered_df.to_csv(csv_filtered, index=False)
        st.download_button(
            label=f"📥 Download Filtered Leads ({len(filtered_df)} records)",
            data=csv_filtered.getvalue(),
            file_name=f"filtered_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:
        st.warning("⚠️ No leads data loaded from linkedin-tracking-csv.csv sheet")
        st.info("📌 Click '⬇️ Load Sheets' button in the sidebar to fetch lead data")

# TAB 5: ADVANCED SEARCH
with tab5:
    st.markdown("## 🔍 Advanced Lead Search & Generation")
    st.markdown("*Search and connect with decision-makers worldwide*")

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
        "Chief Revenue Officer", "Chief Commercial Officer", "Chief Innovation Officer", "Chief Data Officer",
        "Chief Information Officer", "Chief People Officer", "Chief Legal Officer", "Chief Compliance Officer",
        "Director of Operations", "Director of Finance", "Director of HR", "Director of IT", "Director of Engineering",
        "VP of Engineering", "VP of Product", "VP of Operations", "VP of Finance", "VP of HR",
        "Head of Sales", "Head of Marketing", "Head of Growth", "Head of Customer Success", "Head of Partnerships",
        "Business Development Manager", "Sales Manager", "Marketing Manager", "Operations Director", "Finance Director",
        "Strategy Director", "Innovation Director", "Digital Transformation Officer", "E-commerce Director",
        "Supply Chain Director", "Procurement Manager", "Purchasing Manager", "Logistics Manager",
        "Quality Assurance Manager", "Project Manager", "Program Manager", "Portfolio Manager",
        "Investment Manager", "Fund Manager", "Asset Manager", "Wealth Manager", "Relationship Manager",
        "Branch Manager", "Store Manager", "Retail Manager", "Restaurant Owner", "Franchise Owner",
        "Real Estate Developer", "Property Manager", "Construction Manager", "Architect", "Engineer",
        "Healthcare Administrator", "Medical Director", "Practice Manager", "Clinic Owner", "Hospital CEO",
        "School Principal", "Dean", "University President", "Education Director", "Training Manager",
        "HR Director", "Talent Acquisition Manager", "Recruitment Manager", "People Operations Manager",
        "Legal Director", "General Counsel", "Compliance Manager", "Risk Manager", "Audit Manager"
    ]

    # Expanded locations (200+ cities worldwide)
    LOCATIONS = [
        # North America
        "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
        "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
        "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "San Francisco, CA",
        "Charlotte, NC", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
        "Boston, MA", "Nashville, TN", "Detroit, MI", "Portland, OR", "Las Vegas, NV",
        "Miami, FL", "Atlanta, GA", "Toronto, Canada", "Vancouver, Canada", "Montreal, Canada",
        "Calgary, Canada", "Ottawa, Canada", "Mexico City, Mexico", "Guadalajara, Mexico",

        # Europe
        "London, UK", "Paris, France", "Berlin, Germany", "Madrid, Spain", "Rome, Italy",
        "Amsterdam, Netherlands", "Brussels, Belgium", "Vienna, Austria", "Stockholm, Sweden",
        "Copenhagen, Denmark", "Oslo, Norway", "Helsinki, Finland", "Dublin, Ireland",
        "Zurich, Switzerland", "Geneva, Switzerland", "Barcelona, Spain", "Milan, Italy",
        "Munich, Germany", "Frankfurt, Germany", "Hamburg, Germany", "Warsaw, Poland",
        "Prague, Czech Republic", "Budapest, Hungary", "Athens, Greece", "Lisbon, Portugal",
        "Edinburgh, UK", "Manchester, UK", "Birmingham, UK", "Lyon, France", "Marseille, France",

        # Asia
        "Tokyo, Japan", "Singapore", "Hong Kong", "Seoul, South Korea", "Shanghai, China",
        "Beijing, China", "Shenzhen, China", "Guangzhou, China", "Mumbai, India", "Delhi, India",
        "Bangalore, India", "Hyderabad, India", "Chennai, India", "Pune, India", "Kolkata, India",
        "Bangkok, Thailand", "Jakarta, Indonesia", "Manila, Philippines", "Kuala Lumpur, Malaysia",
        "Ho Chi Minh City, Vietnam", "Hanoi, Vietnam", "Taipei, Taiwan", "Osaka, Japan",
        "Dubai, UAE", "Abu Dhabi, UAE", "Riyadh, Saudi Arabia", "Doha, Qatar", "Tel Aviv, Israel",

        # Australia & New Zealand
        "Sydney, Australia", "Melbourne, Australia", "Brisbane, Australia", "Perth, Australia",
        "Adelaide, Australia", "Auckland, New Zealand", "Wellington, New Zealand",

        # South America
        "São Paulo, Brazil", "Rio de Janeiro, Brazil", "Buenos Aires, Argentina", "Santiago, Chile",
        "Lima, Peru", "Bogotá, Colombia", "Caracas, Venezuela", "Montevideo, Uruguay",

        # Africa
        "Johannesburg, South Africa", "Cape Town, South Africa", "Cairo, Egypt", "Lagos, Nigeria",
        "Nairobi, Kenya", "Casablanca, Morocco", "Accra, Ghana", "Addis Ababa, Ethiopia"
    ]

    # Industries
    INDUSTRIES = [
        "Technology", "Software", "SaaS", "E-commerce", "Fintech", "Healthcare", "Biotechnology",
        "Pharmaceuticals", "Manufacturing", "Retail", "Real Estate", "Construction", "Energy",
        "Renewable Energy", "Finance", "Banking", "Insurance", "Consulting", "Marketing",
        "Advertising", "Media", "Entertainment", "Education", "Hospitality", "Food & Beverage",
        "Transportation", "Logistics", "Automotive", "Aerospace", "Telecommunications",
        "Legal Services", "Professional Services", "Human Resources", "Recruitment",
        "Non-profit", "Government", "Agriculture", "Mining", "Oil & Gas", "Utilities"
    ]

    # Company sizes
    COMPANY_SIZES = [
        "1-10 employees", "11-50 employees", "51-200 employees", "201-500 employees",
        "501-1000 employees", "1001-5000 employees", "5001-10000 employees", "10000+ employees"
    ]

    # Search form
    with st.form("lead_search_form"):
        st.markdown("### 🎯 Define Your Target Audience")

        col1, col2 = st.columns(2)

        with col1:
            selected_titles = st.multiselect(
                "👔 Job Titles",
                SEARCH_TERMS,
                default=["CEO", "Founder", "Business Owner"],
                help="Select one or more job titles to target"
            )

            selected_locations = st.multiselect(
                "📍 Locations",
                LOCATIONS,
                default=["New York, NY", "San Francisco, CA", "London, UK"],
                help="Select target locations"
            )

            selected_industries = st.multiselect(
                "🏢 Industries",
                INDUSTRIES,
                default=["Technology", "Software", "SaaS"],
                help="Select target industries"
            )

        with col2:
            selected_company_sizes = st.multiselect(
                "📊 Company Size",
                COMPANY_SIZES,
                default=["11-50 employees", "51-200 employees"],
                help="Select target company sizes"
            )

            num_leads = st.slider(
                "🎯 Number of Leads",
                min_value=10,
                max_value=500,
                value=50,
                step=10,
                help="How many leads do you want to generate?"
            )

            custom_message = st.text_area(
                "✉️ Custom Message Template",
                value="Hi {name}, I noticed your work at {company} and would love to connect!",
                height=100,
                help="Use {name} and {company} as placeholders"
            )

        col1, col2, col3 = st.columns(3)

        with col1:
            search_button = st.form_submit_button("🔍 Search Leads", use_container_width=True)

        with col2:
            save_search = st.form_submit_button("💾 Save Search", use_container_width=True)

        with col3:
            load_search = st.form_submit_button("📂 Load Search", use_container_width=True)

    # Handle search submission
    if search_button:
        if not selected_titles or not selected_locations:
            st.error("❌ Please select at least one job title and one location")
        else:
            with st.spinner("🔍 Searching for leads... This may take a moment"):
                # Prepare webhook payload
                payload = {
                    'action': 'search_leads',
                    'job_titles': selected_titles,
                    'locations': selected_locations,
                    'industries': selected_industries,
                    'company_sizes': selected_company_sizes,
                    'num_leads': num_leads,
                    'message_template': custom_message
                }

                # Send to webhook
                success, response = send_webhook_request(WEBHOOK_URL, payload)

                if success:
                    st.success(f"✅ Successfully initiated search for {num_leads} leads!")
                    st.balloons()

                    # Log activity
                    st.session_state.activity_log.append({
                        'timestamp': datetime.now(),
                        'action': 'search_initiated',
                        'details': f"Searching for {num_leads} leads"
                    })

                    # Display search summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🎯 Target Leads", num_leads)
                    with col2:
                        st.metric("👔 Job Titles", len(selected_titles))
                    with col3:
                        st.metric("📍 Locations", len(selected_locations))

                    # Show webhook response
                    with st.expander("🔍 View Webhook Response"):
                        st.json(json.loads(response) if response else {})
                else:
                    st.error(f"❌ Search failed: {response}")

    if save_search:
        st.info("💾 Search saved! (Feature in development)")

    if load_search:
        st.info("📂 Load saved search (Feature in development)")

    # Recent searches
    st.markdown("<br>### 📜 Recent Activity", unsafe_allow_html=True)

    if st.session_state.activity_log:
        for activity in reversed(st.session_state.activity_log[-10:]):
            st.markdown(f"""
            <div style='background: rgba(255, 255, 255, 0.98); padding: 1.5rem; border-radius: 15px; margin: 0.5rem 0;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <strong style='color: #667eea;'>{activity['action'].replace('_', ' ').title()}</strong>
                        <p style='color: #666; margin: 0.5rem 0 0 0;'>{activity['details']}</p>
                    </div>
                    <span style='color: #999; font-size: 0.9rem;'>{activity['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent activity to display")

# TAB 6: CONVERSATIONS
with tab6:
    st.markdown("## 💬 Conversation History")
    st.markdown("*Track all your LinkedIn conversations in one place*")

    # Load conversation data from leads
    if leads_df is not None and not leads_df.empty:
        # Group conversations
        st.markdown("### 📊 Conversation Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_convos = len(leads_df)
            st.metric("Total Conversations", total_convos)

        with col2:
            if 'success' in leads_df.columns:
                successful = leads_df[leads_df['success'] == True].shape[0]
                st.metric("Successful", successful)

        with col3:
            if 'connection_status' in leads_df.columns:
                responded = leads_df[leads_df['connection_status'].notna()].shape[0]
                st.metric("Responded", responded)

        with col4:
            if 'timestamp' in leads_df.columns:
                today_convos = leads_df[leads_df['timestamp'].dt.date == datetime.now().date()]
                st.metric("Today", len(today_convos))

        st.markdown("---")

        # Display conversations
        st.markdown("### 💬 Recent Conversations")

        for idx, row in leads_df.head(20).iterrows():
            profile_name = row.get('name', row.get('profile_name', 'Unknown'))
            linkedin_url = row.get('linkedin_url', '#')
            message = row.get('linkedin_message', 'No message')
            timestamp = row.get('timestamp', 'N/A')
            status = row.get('connection_status', 'pending')

            st.markdown(f"""
            <div style='background: rgba(255, 255, 255, 0.98); padding: 2rem; border-radius: 20px;
                        margin: 1rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                    <div>
                        <h3 style='color: #667eea; margin: 0;'>{profile_name}</h3>
                        <p style='color: #666; margin: 0.5rem 0;'>{row.get('profile_tagline', row.get('tagline', 'N/A'))}</p>
                    </div>
                    <span style='background: #667eea; color: white; padding: 0.5rem 1rem;
                                border-radius: 20px; font-size: 0.9rem;'>{status}</span>
                </div>
                <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 15px;
                            border-left: 4px solid #667eea; margin: 1rem 0;'>
                    <p style='color: #2d3748; margin: 0; line-height: 1.6;'>{message}</p>
                </div>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;'>
                    <span style='color: #999; font-size: 0.9rem;'>📅 {timestamp}</span>
                    <a href="{linkedin_url}" target="_blank"
                       style='background: #667eea; color: white; padding: 0.5rem 1.5rem;
                              border-radius: 15px; text-decoration: none;'>View Profile</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💬 No conversations yet. Start your outreach to see conversations here!")

# TAB 7: EMAIL QUEUE
with tab7:
    st.markdown("## 📧 Email Queue Manager")
    st.markdown("*Manage and send follow-up emails to your leads*")

    if not st.session_state.email_queue:
        st.markdown("""
        <div style='background: rgba(255, 255, 255, 0.95); padding: 4rem; border-radius: 25px;
                    text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.15);'>
            <h2 style='color: #667eea; font-size: 3rem; margin-bottom: 1rem;'>📧</h2>
            <h3 style='color: #2d3748; margin-bottom: 1rem;'>Email Queue is Empty</h3>
            <p style='color: #666; font-size: 1.1rem;'>Queue emails from the CRM dashboard</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background: rgba(255, 255, 255, 0.95); padding: 2rem; border-radius: 20px;
                    text-align: center; margin-bottom: 2rem;'>
            <h2 style='color: #667eea;'>📧 {len(st.session_state.email_queue)} Queued Emails</h2>
        </div>
        """, unsafe_allow_html=True)

        for idx, email in enumerate(st.session_state.email_queue):
            st.markdown(f"""
            <div style='background: rgba(255, 255, 255, 0.98); padding: 2rem; border-radius: 20px;
                        margin: 1rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <h3 style='color: #667eea;'>To: {email['to']}</h3>
                <p style='color: #666;'><strong>Subject:</strong> {email['subject']}</p>
                <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 15px; margin: 1rem 0;'>
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


# TAB 8: ANALYTICS HUB
with tab8:
    st.markdown("## 📊 Advanced Analytics Hub")
    st.markdown("*Deep insights into your LinkedIn outreach and habit performance*")

    # KPIs
    st.markdown("### 🎯 Key Performance Indicators")

    col1, col2, col3, col4, col5 = st.columns(5)

    messages_sent = daily_df['Initial_Messages_Sent'].sum() if 'Initial_Messages_Sent' in daily_df.columns else 0

    with col1:
        if total_sent > 0:
            acceptance_rate = (total_accepted / total_sent) * 100
            st.metric("Acceptance Rate", f"{acceptance_rate:.1f}%",
                     "Target: 30-40%")

    with col2:
        if total_accepted > 0:
            message_rate = (messages_sent / total_accepted) * 100
            st.metric("Message Rate", f"{message_rate:.1f}%",
                     "% messaged")

    with col3:
        if messages_sent > 0:
            interest_rate = (total_interested / messages_sent) * 100
            st.metric("Interest Rate", f"{interest_rate:.1f}%",
                     "Target: 15-25%")

    with col4:
        if total_interested > 0:
            final_conv_rate = (total_conversions / total_interested) * 100
            st.metric("Conversion Rate", f"{final_conv_rate:.1f}%",
                     "Target: 5-15%")

    with col5:
        habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]
        avg_daily_habits = sum([habit_log[col].mean() for col in habit_columns if col in habit_log.columns]) / len(habit_columns) * 100 if habit_columns else 0
        st.metric("Avg Daily Habits", f"{avg_daily_habits:.0f}%",
                 "Target: 80%+")

    st.markdown("---")

    # Combined performance analysis
    st.markdown("### 📈 Integrated Performance Analysis")

    # Create correlation between habits and LinkedIn performance
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### LinkedIn Conversion Funnel")
        funnel_data = {
            'Stage': ['Sent', 'Accepted', 'Messaged', 'Interested', 'Converted'],
            'Count': [total_sent, total_accepted, messages_sent, total_interested, total_conversions]
        }
        fig = go.Figure(go.Funnel(
            y=funnel_data['Stage'],
            x=funnel_data['Count'],
            textinfo="value+percent initial"
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Habit Completion by Category")
        habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]
        habit_completion = {habit.replace('_', ' ').title(): habit_log[habit].sum()
                          for habit in habit_columns if habit in habit_log.columns}

        fig = px.bar(x=list(habit_completion.keys()), y=list(habit_completion.values()),
                    title='Total Completions by Habit',
                    labels={'x': 'Habit', 'y': 'Completions'})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Weekly trends
    st.markdown("### 📅 Weekly Trend Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### LinkedIn Weekly Performance")
        if 'Day' in daily_df.columns:
            df_weekly = daily_df.copy()
            df_weekly['Week'] = ((df_weekly['Day'] - 1) // 7) + 1

            weekly_summary = df_weekly.groupby('Week').agg({
                'Connections_Sent': 'sum',
                'Connections_Accepted': 'sum',
                'Conversions': 'sum'
            }).reset_index()

            fig = go.Figure()
            fig.add_trace(go.Bar(x=weekly_summary['Week'], y=weekly_summary['Connections_Sent'],
                                name='Sent'))
            fig.add_trace(go.Bar(x=weekly_summary['Week'], y=weekly_summary['Connections_Accepted'],
                                name='Accepted'))
            fig.add_trace(go.Bar(x=weekly_summary['Week'], y=weekly_summary['Conversions'],
                                name='Conversions'))
            fig.update_layout(barmode='group', title='Weekly LinkedIn Metrics')
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Habit Weekly Completion Rates")
        habit_log_copy = habit_log.copy()
        habit_log_copy['Week'] = (pd.to_datetime(habit_log_copy['Date']) - pd.to_datetime(habit_log_copy['Date'].min())).dt.days // 7 + 1

        habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes', 'Week']]
        weekly_habits = habit_log_copy.groupby('Week')[habit_columns].mean() * 100

        fig = go.Figure()
        for habit in habit_columns[:5]:  # Show top 5 habits
            if habit in weekly_habits.columns:
                fig.add_trace(go.Scatter(x=weekly_habits.index, y=weekly_habits[habit],
                                        mode='lines+markers',
                                        name=habit.replace('_', ' ').title()))

        fig.update_layout(title='Weekly Habit Completion %',
                         xaxis_title='Week', yaxis_title='Completion %')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Correlation analysis
    st.markdown("### 🔗 Habit-Performance Correlation")
    st.markdown("*Discover which habits correlate with better LinkedIn performance*")

    # Calculate daily habit completion rate
    habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]
    habit_log_analysis = habit_log.copy()
    habit_log_analysis['Daily_Habit_Rate'] = habit_log_analysis[habit_columns].sum(axis=1) / len(habit_columns) * 100

    # Merge with LinkedIn data
    if 'Date' in daily_df.columns and 'Date' in habit_log_analysis.columns:
        merged_data = pd.merge(daily_df, habit_log_analysis[['Date', 'Daily_Habit_Rate']],
                              on='Date', how='inner')

        col1, col2 = st.columns(2)

        with col1:
            fig = px.scatter(merged_data, x='Daily_Habit_Rate', y='Connections_Sent',
                           title='Habit Completion vs Connections Sent',
                           labels={'Daily_Habit_Rate': 'Daily Habit Completion %',
                                  'Connections_Sent': 'Connections Sent'},
                           trendline="ols")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(merged_data, x='Daily_Habit_Rate', y='Conversions',
                           title='Habit Completion vs Conversions',
                           labels={'Daily_Habit_Rate': 'Daily Habit Completion %',
                                  'Conversions': 'Conversions'},
                           trendline="ols")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Projections
    st.markdown("### 🎯 Goal Projections & Forecasts")

    if current_day > 0:
        col1, col2, col3 = st.columns(3)

        with col1:
            avg_daily_sent = total_sent / current_day
            projected_total = avg_daily_sent * 30

            st.markdown("#### LinkedIn Projections")
            st.metric("Projected Total Sent", f"{int(projected_total):,}")

            gap = 1200 - projected_total
            if gap > 0:
                st.metric("Gap to Goal", f"{int(gap):,}",
                         delta=f"Need {gap/(30-current_day):.0f}/day",
                         delta_color="inverse")
            else:
                st.metric("Surplus", f"{int(abs(gap)):,}",
                         delta="On track! 🎉")

        with col2:
            st.markdown("#### Habit Projections")
            projected_habit_rate = avg_daily_habits
            st.metric("Projected Completion", f"{projected_habit_rate:.0f}%")

            if projected_habit_rate >= 80:
                st.success("✅ Excellent trajectory!")
            elif projected_habit_rate >= 60:
                st.info("📈 Good progress!")
            else:
                st.warning("⚠️ Room for improvement")

        with col3:
            st.markdown("#### Success Probability")
            linkedin_prob = min(100, (projected_total / 1200) * 100)
            habit_prob = min(100, projected_habit_rate)
            overall_prob = (linkedin_prob + habit_prob) / 2

            st.metric("LinkedIn Goal", f"{linkedin_prob:.0f}%")
            st.metric("Habit Goal", f"{habit_prob:.0f}%")
            st.metric("Overall Success", f"{overall_prob:.0f}%")

# TAB 9: DAILY CHECKLIST
with tab9:
    st.markdown("## ✅ Daily Outreach & Habit Checklist")
    st.markdown(f"### Day {current_day} of 30 - {datetime.now().strftime('%A, %B %d, %Y')}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="stage-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 LinkedIn Goals Today")
        st.markdown("""
        - [ ] Send 40 connection requests with personalized messages
        - [ ] Check for newly accepted connections
        - [ ] Send initial AI Systems Checklist offer to new connections
        - [ ] Follow up with interested leads
        - [ ] Send checklist links to those who responded
        - [ ] Send scheduled follow-up messages (4-sequence)
        - [ ] Track conversions and update database
        - [ ] Review and respond to all messages
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="habit-card">', unsafe_allow_html=True)
        st.markdown("### 🏆 Habit Goals Today")

        today_date = datetime.now().strftime("%Y-%m-%d")
        today_habits = habit_log[habit_log['Date'] == today_date]

        if not today_habits.empty:
            habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]

            for habit in habit_columns:
                if habit in today_habits.columns:
                    status = "✅" if today_habits.iloc[0][habit] else "⏳"
                    habit_display = habit.replace('_', ' ').title()
                    st.markdown(f"- [{status}] {habit_display}")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Time blocking
    st.markdown("### ⏰ Suggested Time Blocks")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🌅 Morning (30-45 min)")
        st.markdown("""
        - ☕ Morning routine habit
        - 🧘 Meditation/mindfulness
        - 🔗 Send 20 LinkedIn connections
        - ✅ Check accepted connections
        - 💬 Send initial messages
        """)

    with col2:
        st.markdown("#### ☀️ Midday (15-20 min)")
        st.markdown("""
        - 📧 Check LinkedIn responses
        - 🔗 Send checklist links
        - ✏️ Mark interested leads
        - 💪 Quick exercise/stretch
        - 📚 Learning session
        """)

    with col3:
        st.markdown("#### 🌆 Afternoon (30-45 min)")
        st.markdown("""
        - 🔗 Send remaining 20 connections
        - 📤 Send follow-up messages
        - 📊 Update tracker
        - 📝 Content creation
        - 🙏 Gratitude journal
        """)

    st.markdown("---")

    # Today's progress
    st.markdown("### 📊 Today's Progress Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### LinkedIn Today")
        today_idx = current_day - 1
        if today_idx < len(daily_df):
            today_data = daily_df.iloc[today_idx]

            sent = int(today_data.get('Connections_Sent', 0))
            accepted = int(today_data.get('Connections_Accepted', 0))
            conversions = int(today_data.get('Conversions', 0))

            st.metric("Sent", sent, f"{sent}/40")
            st.metric("Accepted", accepted)
            st.metric("Conversions", conversions)

    with col2:
        st.markdown("#### Habits Today")
        today_date = datetime.now().strftime("%Y-%m-%d")
        today_habits = habit_log[habit_log['Date'] == today_date]

        if not today_habits.empty:
            habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]
            completed = sum([today_habits.iloc[0][col] for col in habit_columns if col in today_habits.columns])
            total = len(habit_columns)

            st.metric("Completed", f"{completed}/{total}")
            st.metric("Completion Rate", f"{(completed/total*100):.0f}%")

            if completed == total:
                st.success("🎉 Perfect day!")
            elif completed >= total * 0.8:
                st.info("💪 Great job!")
            else:
                st.warning("⚡ Keep going!")

    with col3:
        st.markdown("#### Overall Score")

        # Calculate combined score
        linkedin_score = (sent / 40 * 100) if sent <= 40 else 100
        habit_score = (completed / total * 100) if total > 0 else 0
        overall_score = (linkedin_score + habit_score) / 2

        st.metric("Today's Score", f"{overall_score:.0f}%")

        if overall_score >= 90:
            st.success("🏆 Outstanding!")
        elif overall_score >= 75:
            st.info("⭐ Excellent!")
        elif overall_score >= 60:
            st.warning("👍 Good effort!")
        else:
            st.error("💪 Room to improve!")

# TAB 10: STREAKS & REWARDS
with tab10:
    st.markdown("## 🔥 Streaks, Achievements & Rewards")
    st.markdown("*Celebrate your consistency and unlock achievements!*")

    # Current streaks
    st.markdown("### 🔥 Current Streaks")

    habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]

    streak_data = []
    for habit in habit_columns:
        if habit in habit_log.columns:
            streak = calculate_streak(habit_log, habit)
            success_rate = calculate_success_rate(habit_log, habit)

            # Calculate longest streak
            longest_streak = 0
            current_streak = 0
            for val in habit_log[habit]:
                if val:
                    current_streak += 1
                    longest_streak = max(longest_streak, current_streak)
                else:
                    current_streak = 0

            streak_data.append({
                'Habit': habit.replace('_', ' ').title(),
                'Current Streak': streak,
                'Longest Streak': longest_streak,
                'Success Rate': success_rate
            })

    # Sort by current streak
    streak_data.sort(key=lambda x: x['Current Streak'], reverse=True)

    # Display top streaks
    col1, col2, col3 = st.columns(3)

    for i, data in enumerate(streak_data[:3]):
        with [col1, col2, col3][i]:
            if data['Current Streak'] >= 7:
                card_class = "success-card"
                emoji = "🔥"
            elif data['Current Streak'] >= 3:
                card_class = "info-card"
                emoji = "⭐"
            else:
                card_class = "metric-card"
                emoji = "💪"

            st.markdown(f'<div class="metric-card {card_class}">', unsafe_allow_html=True)
            st.markdown(f"### {emoji} {data['Habit']}")
            st.markdown(f"<div class='big-metric'>{data['Current Streak']}</div>", unsafe_allow_html=True)
            st.markdown(f"<center>Day Streak</center>", unsafe_allow_html=True)
            st.markdown(f"<center>Best: {data['Longest Streak']} days | {data['Success Rate']:.0f}% success</center>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # All streaks table
    st.markdown("### 📊 All Habit Streaks")
    streak_df = pd.DataFrame(streak_data)
    st.dataframe(streak_df, use_container_width=True)

    st.markdown("---")

    # Achievements
    st.markdown("### 🏆 Achievements & Milestones")

    achievements = []

    # LinkedIn achievements
    if total_sent >= 100:
        achievements.append({"Achievement": "🎯 Century Club", "Description": "Sent 100+ connections", "Status": "✅ Unlocked"})
    if total_sent >= 500:
        achievements.append({"Achievement": "🚀 Half Way Hero", "Description": "Sent 500+ connections", "Status": "✅ Unlocked"})
    if total_sent >= 1000:
        achievements.append({"Achievement": "💎 Networking Master", "Description": "Sent 1000+ connections", "Status": "✅ Unlocked"})
    if total_accepted >= 50:
        achievements.append({"Achievement": "🤝 Connection King", "Description": "50+ accepted connections", "Status": "✅ Unlocked"})
    if total_conversions >= 10:
        achievements.append({"Achievement": "💰 Conversion Champion", "Description": "10+ conversions", "Status": "✅ Unlocked"})

    # Habit achievements
    for data in streak_data:
        if data['Current Streak'] >= 7:
            achievements.append({
                "Achievement": f"🔥 {data['Habit']} Week Warrior",
                "Description": f"7+ day streak in {data['Habit']}",
                "Status": "✅ Unlocked"
            })
        if data['Current Streak'] >= 14:
            achievements.append({
                "Achievement": f"⭐ {data['Habit']} Fortnight Force",
                "Description": f"14+ day streak in {data['Habit']}",
                "Status": "✅ Unlocked"
            })
        if data['Current Streak'] >= 30:
            achievements.append({
                "Achievement": f"👑 {data['Habit']} Monthly Master",
                "Description": f"30+ day streak in {data['Habit']}",
                "Status": "✅ Unlocked"
            })
        if data['Success Rate'] >= 90:
            achievements.append({
                "Achievement": f"💯 {data['Habit']} Perfectionist",
                "Description": f"90%+ success rate in {data['Habit']}",
                "Status": "✅ Unlocked"
            })

    # Overall achievements
    habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]
    total_possible = len(habit_log) * len(habit_columns)
    total_completed = sum([habit_log[col].sum() for col in habit_columns if col in habit_log.columns])
    overall_rate = (total_completed / total_possible * 100) if total_possible > 0 else 0

    if overall_rate >= 80:
        achievements.append({"Achievement": "🌟 Consistency Champion", "Description": "80%+ overall habit completion", "Status": "✅ Unlocked"})
    if overall_rate >= 90:
        achievements.append({"Achievement": "💎 Diamond Discipline", "Description": "90%+ overall habit completion", "Status": "✅ Unlocked"})

    if achievements:
        achievement_df = pd.DataFrame(achievements)
        st.dataframe(achievement_df, use_container_width=True)

        st.balloons()
        st.success(f"🎉 You've unlocked {len(achievements)} achievements!")
    else:
        st.info("Keep working on your habits and LinkedIn outreach to unlock achievements!")

    st.markdown("---")

    # Streak calendar
    st.markdown("### 📅 Streak Calendar")
    st.markdown("*Visual representation of your consistency*")

    # Create a calendar view
    habit_log_calendar = habit_log.copy()
    habit_log_calendar['Total_Completed'] = habit_log_calendar[habit_columns].sum(axis=1)
    habit_log_calendar['Completion_Rate'] = (habit_log_calendar['Total_Completed'] / len(habit_columns) * 100).round(0)

    fig = px.bar(habit_log_calendar, x='Date', y='Completion_Rate',
                title='Daily Habit Completion Rate (%)',
                labels={'Completion_Rate': 'Completion %'},
                color='Completion_Rate',
                color_continuous_scale=['#f093fb', '#38ef7d'])
    fig.add_hline(y=80, line_dash="dash", line_color="green",
                 annotation_text="80% Target")
    st.plotly_chart(fig, use_container_width=True)

# TAB 11: WEBHOOK MONITOR
with tab11:
    st.markdown("## 🔗 Webhook Monitor & Testing")
    st.markdown("*Monitor webhook activity and test connections*")

    st.markdown(f"""
    <div style='background: rgba(255, 255, 255, 0.95); padding: 2rem; border-radius: 20px; margin-bottom: 2rem;'>
        <h3 style='color: #667eea; margin-bottom: 1rem;'>📡 Webhook Configuration</h3>
        <p style='color: #666;'><strong>Endpoint:</strong> {WEBHOOK_URL}</p>
    </div>
    """, unsafe_allow_html=True)

    # Test webhook
    st.markdown("### 🧪 Test Webhook Connection")

    col1, col2 = st.columns(2)

    with col1:
        test_action = st.selectbox("Select Test Action",
                                   ['ping', 'search_leads', 'send_message', 'get_status'])

    with col2:
        if st.button("🚀 Send Test Request", use_container_width=True):
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
            status_color = '#10b981' if entry['status'] == 'success' else '#ef4444'
            status_icon = '✅' if entry['status'] == 'success' else '❌'

            st.markdown(f"""
            <div style='background: rgba(255, 255, 255, 0.98); padding: 1.5rem; border-radius: 15px;
                        margin: 0.5rem 0; border-left: 4px solid {status_color};'>
                <div style='display: flex; justify-content: space-between; align-items: start;'>
                    <div style='flex: 1;'>
                        <div style='display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;'>
                            <span style='background: {status_color}; color: white; padding: 0.3rem 0.8rem;
                                        border-radius: 15px; font-size: 0.85rem;'>{status_icon} {entry['status'].upper()}</span>
                            <strong style='color: #667eea;'>{entry['action']}</strong>
                        </div>
                        <p style='color: #666; margin: 0.5rem 0; font-size: 0.9rem;'>
                            Response: {str(entry['response'])[:100]}{'...' if len(str(entry['response'])) > 100 else ''}
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


# TAB 12: SETTINGS
with tab12:
    st.markdown("## ⚙️ Settings & Configuration")

    # Challenge settings
    st.markdown("### 📅 Challenge Settings")

    col1, col2 = st.columns(2)

    with col1:
        new_start_date = st.date_input(
            "Challenge Start Date",
            value=datetime.strptime(st.session_state.challenge_start_date, "%Y-%m-%d")
        )

        if st.button("Update Start Date"):
            st.session_state.challenge_start_date = new_start_date.strftime("%Y-%m-%d")
            st.success("✅ Start date updated!")
            st.rerun()

    with col2:
        st.metric("Current Day", current_day)
        st.metric("Days Remaining", 30 - current_day)

    st.markdown("---")

    # Habit management
    st.markdown("### ✅ Manage Habits")

    st.markdown("**Current Habits:**")
    habit_columns = [col for col in habit_log.columns if col not in ['Date', 'Notes']]

    for habit in habit_columns:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.text(habit.replace('_', ' ').title())
        with col2:
            streak = calculate_streak(habit_log, habit)
            st.caption(f"🔥 {streak} day streak")
        with col3:
            success_rate = calculate_success_rate(habit_log, habit)
            st.caption(f"✅ {success_rate:.0f}%")

    st.markdown("---")

    # Data management
    st.markdown("### 💾 Data Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Export All Data")

        if st.button("📥 Export Complete Dataset", use_container_width=True):
            # Create a zip file with all data
            import zipfile
            from io import BytesIO

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add daily tracker
                csv_daily = daily_df.to_csv(index=False)
                zip_file.writestr('daily_tracker.csv', csv_daily)

                # Add habit log
                csv_habits = habit_log.to_csv(index=False)
                zip_file.writestr('habit_log.csv', csv_habits)

                # Add leads if available
                if leads_df is not None and not leads_df.empty:
                    csv_leads = leads_df.to_csv(index=False)
                    zip_file.writestr('leads_database.csv', csv_leads)

            st.download_button(
                label="📥 Download ZIP Archive",
                data=zip_buffer.getvalue(),
                file_name=f"complete_data_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip",
                use_container_width=True
            )

    with col2:
        st.markdown("#### Reset Data")

        st.warning("⚠️ This will reset all your data. This action cannot be undone!")

        if st.button("🔄 Reset All Data", use_container_width=True):
            if st.checkbox("I understand this will delete all my data"):
                st.session_state.daily_tracker = create_empty_daily_tracker()
                st.session_state.habit_log = create_empty_habit_log()
                st.session_state.challenge_start_date = datetime.now().strftime("%Y-%m-%d")
                st.success("✅ Data reset complete!")
                st.rerun()

    st.markdown("---")

    # Google Sheets configuration
    st.markdown("### ☁️ Google Sheets Configuration")

    st.info("📌 Make sure your Google Sheets are set to 'Anyone with link can view'")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Daily Tracker Sheet:**")
        st.code(f"Sheet ID: {DAILY_TRACKER_SHEET_ID}")
        st.code(f"Sheet Name: {DAILY_TRACKER_SHEET_NAME}")
        st.markdown(f"[Open Sheet](https://docs.google.com/spreadsheets/d/{DAILY_TRACKER_SHEET_ID}/edit)")

    with col2:
        st.markdown("**Leads Database Sheet:**")
        st.code(f"Sheet ID: {LEADS_DATABASE_SHEET_ID}")
        st.code(f"GID: {LEADS_SHEET_GID}")
        st.markdown(f"[Open Sheet](https://docs.google.com/spreadsheets/d/{LEADS_DATABASE_SHEET_ID}/edit?gid={LEADS_SHEET_GID})")

    st.markdown("---")

    # App info
    st.markdown("### ℹ️ App Information")

    st.markdown("""
    **LinkedIn Outreach & Habit Tracker Pro v2.0**

    Features:
    - 📊 Unified dashboard for LinkedIn and habits
    - 📅 30-day LinkedIn outreach tracking
    - ✅ Comprehensive habit tracking system
    - 🔥 Streak tracking and achievements
    - 📈 Advanced analytics and insights
    - ☁️ Google Sheets integration
    - 📖 Complete templates and guides
    - 🎯 Daily checklists and time blocking

    Built with Streamlit, Pandas, and Plotly
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><b>🔥 LinkedIn Outreach & Habit Tracker Pro 🔥</b></p>
    <p>⚡ Complete Productivity System | Real-time Analytics | Habit Tracking | Achievement System</p>
    <p style='font-size: 1.1em; margin-top: 15px;'><b>Consistency is the key to success. Show up every day!</b></p>
    <p style='font-size: 0.9em; margin-top: 10px;'>💡 Pro Tip: Track everything, celebrate small wins, and never break the chain!</p>
    <p style='font-size: 0.85em; margin-top: 15px; color: #999;'>📊 Data syncs from Google Sheets | 💾 Download backups regularly | 🎯 Track everything!</p>
</div>
""", unsafe_allow_html=True)
