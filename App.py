import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

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
LEADS_SHEET_GID = "1881909623"

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
    """Load leads database from linkedin-tracking-csv.csv sheet"""
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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "🏠 Dashboard", 
    "📅 Daily Tracker", 
    "✅ Habit Tracker",
    "👥 Leads CRM",
    "📊 Analytics Hub",
    "🎯 Daily Checklist",
    "🔥 Streaks & Rewards",
    "📖 Templates & Guide",
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
    st.caption("Data from linkedin-tracking-csv.csv sheet")
    
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
            'timestamp', 'profile_name', 'name', 'profile_location', 'location',
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
        st.warning("⚠️ No leads data loaded from Google Sheets")
        st.info("📌 Click '⬇️ Load Sheets' button in the sidebar to fetch lead data")

# TAB 5: ANALYTICS HUB
with tab5:
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

# TAB 6: DAILY CHECKLIST
with tab6:
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

# TAB 7: STREAKS & REWARDS
with tab7:
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

# TAB 8: TEMPLATES & GUIDE
with tab8:
    st.markdown("## 📖 Complete Strategy Guide & Templates")
    
    # Message templates
    st.markdown("### 💬 LinkedIn Message Templates")
    
    with st.expander("🤝 Connection Request Message", expanded=True):
        st.code("""Hi [First Name],

I noticed your work in [their industry/role] and thought we should connect. I help businesses implement AI automation systems and would love to share insights.

Looking forward to connecting!

[Your Name]""", language="text")
    
    with st.expander("💡 Initial Message - AI Systems Checklist Offer"):
        st.code("""Hi [First Name],

Thanks for connecting! I wanted to reach out because I've put together a free AI Systems Implementation Checklist that's been helping businesses like yours streamline operations and increase efficiency.

Would you be interested in checking it out? It's a quick checklist that covers:
- AI automation opportunities in your workflow
- Implementation best practices
- ROI tracking methods
- Common pitfalls to avoid

Let me know if you'd like me to send it your way!

Best,
[Your Name]""", language="text")
    
    with st.expander("🔗 Link Delivery Message"):
        st.code("""Hi [First Name],

Great to hear you're interested! Here's the AI Systems Implementation Checklist:

[YOUR LINK HERE]

This covers everything you need to get started with AI automation. Take a look and let me know if you have any questions - happy to chat about how it could work for your specific situation.

Best,
[Your Name]""", language="text")
    
    with st.expander("📧 Follow-up Sequence (4 Messages)"):
        st.markdown("**Follow-up 1 (3 days after link):**")
        st.code("""Hi [First Name],

Just wanted to check in - did you get a chance to look at the AI Systems Checklist I sent over?

I'd love to hear your thoughts or answer any questions you might have about implementing AI in your workflow.

Best,
[Your Name]""", language="text")
        
        st.markdown("**Follow-up 2 (5 days after FU1):**")
        st.code("""Hi [First Name],

I know things get busy! I wanted to follow up on the AI checklist and see if you had any specific questions about implementation.

I've helped [X number] of businesses in [their industry] implement similar systems - happy to share some specific examples if that would be helpful.

Best,
[Your Name]""", language="text")
        
        st.markdown("**Follow-up 3 (7 days after FU2):**")
        st.code("""Hi [First Name],

Quick question - are you currently working on any AI or automation projects? 

I'd love to offer a free 15-minute consultation to discuss how the checklist could be customized for your specific needs. No strings attached, just want to be helpful!

Would you have time for a quick call this week or next?

Best,
[Your Name]""", language="text")
        
        st.markdown("**Follow-up 4 - Final Message (7 days after FU3):**")
        st.code("""Hi [First Name],

I don't want to keep bothering you, so this will be my last message on this topic!

The offer for the free AI consultation is still open if you ever want to discuss how AI systems could help your business. Feel free to reach out anytime.

In the meantime, I'll continue sharing valuable content about AI and automation - hope you find it useful!

Best of luck with everything,
[Your Name]""", language="text")
    
    st.markdown("---")
    
    # Habit building guide
    st.markdown("### 🏆 Habit Building Strategy")
    
    with st.expander("📋 How to Build Lasting Habits", expanded=True):
        st.markdown("""
        **The 4 Laws of Behavior Change:**
        
        1. **Make it Obvious**
           - Set clear triggers and cues
           - Use implementation intentions: "When X happens, I will do Y"
           - Design your environment for success
        
        2. **Make it Attractive**
           - Pair habits with things you enjoy
           - Join a group where your desired behavior is normal
           - Create a motivation ritual
        
        3. **Make it Easy**
           - Reduce friction for good habits
           - Use the 2-minute rule: scale down to 2 minutes
           - Prepare your environment in advance
        
        4. **Make it Satisfying**
           - Use immediate rewards
           - Track your habits (like in this app!)
           - Never miss twice in a row
        
        **Habit Stacking:**
        - After [CURRENT HABIT], I will [NEW HABIT]
        - Example: "After I pour my morning coffee, I will send 20 LinkedIn connections"
        """)
    
    with st.expander("🎯 Recommended Daily Routine"):
        st.markdown("""
        **Morning Routine (60 minutes):**
        - 🧘 Meditation (10 min)
        - 📝 Gratitude journal (5 min)
        - 🔗 LinkedIn outreach - Part 1 (30 min)
        - 📚 Reading/Learning (15 min)
        
        **Midday Routine (30 minutes):**
        - 💪 Exercise/Movement (20 min)
        - 🔗 LinkedIn follow-ups (10 min)
        
        **Afternoon Routine (45 minutes):**
        - 🔗 LinkedIn outreach - Part 2 (30 min)
        - 📊 Update trackers (10 min)
        - 📝 Content creation (5 min)
        
        **Evening Routine (30 minutes):**
        - 📖 Deep work/Learning (20 min)
        - 🙏 Reflection & planning (10 min)
        """)
    
    with st.expander("💡 Pro Tips for Success"):
        st.markdown("""
        **LinkedIn Outreach:**
        - ✍️ Personalize every message
        - 📏 Keep it short (300 characters max)
        - 🎁 Provide value first
        - ⏰ Wait 24 hours after connection
        - 📅 Space out follow-ups
        
        **Habit Tracking:**
        - 📊 Track daily, no exceptions
        - 🎯 Focus on consistency over perfection
        - 🔄 Never miss twice in a row
        - 🎉 Celebrate small wins
        - 📈 Review weekly progress
        
        **Productivity:**
        - 🌅 Do hardest tasks in the morning
        - ⏰ Use time blocking
        - 📱 Minimize distractions
        - 🎯 Focus on one thing at a time
        - 💪 Take regular breaks
        """)
    
    st.markdown("---")
    
    # Download templates
    st.markdown("### 📥 Download Templates")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Daily Tracker Template")
        sample_daily = create_empty_daily_tracker()
        csv_sample_daily = io.StringIO()
        sample_daily.to_csv(csv_sample_daily, index=False)
        st.download_button(
            label="📥 Download Daily Tracker Template",
            data=csv_sample_daily.getvalue(),
            file_name="daily_tracker_template.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        st.markdown("#### Habit Log Template")
        sample_habits = create_empty_habit_log()
        csv_sample_habits = io.StringIO()
        sample_habits.to_csv(csv_sample_habits, index=False)
        st.download_button(
            label="📥 Download Habit Log Template",
            data=csv_sample_habits.getvalue(),
            file_name="habit_log_template.csv",
            mime="text/csv",
            use_container_width=True
        )

# TAB 9: SETTINGS
with tab9:
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
