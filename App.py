import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import io
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(page_title="LinkedIn Outreach Tracker Pro", page_icon="🚀", layout="wide")

# Custom CSS
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
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets Configuration
DAILY_TRACKER_SHEET_ID = "1UkuTf8VwGPIilTxhTEdP9K-zdtZFnThazFdGyxVYfmg"
LEADS_DATABASE_SHEET_ID = "1eLEFvyV1_f74UC1g5uQ-xA7A62sK8Pog27KIjw_Sk3Y"
DAILY_TRACKER_SHEET_NAME = "daily_tracker_20251021"
LEADS_SHEET_NAME = "Sheet1"

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
    try:
        df = get_sheet_by_name(LEADS_DATABASE_SHEET_ID, LEADS_SHEET_NAME)
        if df is not None and not df.empty:
            df.columns = df.columns.str.strip()
            if 'success' in df.columns:
                df['success'] = df['success'].astype(str).str.lower() == 'true'
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            return df
        return create_empty_leads_database()
    except:
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
    return pd.DataFrame({
        'Name': [],
        'LinkedIn_URL': [],
        'Date_Connected': [],
        'Connection_Status': [],
        'Stage': [],
        'Initial_Message_Sent': [],
        'Interested': [],
        'Link_Sent_Date': [],
        'Follow_Up_1_Date': [],
        'Follow_Up_2_Date': [],
        'Follow_Up_3_Date': [],
        'Follow_Up_4_Date': [],
        'Converted': [],
        'Notes': []
    })

# Initialize session state
if 'daily_tracker' not in st.session_state:
    st.session_state.daily_tracker = load_daily_tracker()

if 'leads_database' not in st.session_state:
    st.session_state.leads_database = create_empty_leads_database()

if 'challenge_start_date' not in st.session_state:
    st.session_state.challenge_start_date = datetime.now().strftime("%Y-%m-%d")

if 'sheets_data' not in st.session_state:
    st.session_state.sheets_data = None

if 'leads_sheets_data' not in st.session_state:
    st.session_state.leads_sheets_data = None

# Helper function
def get_current_day():
    days_elapsed = (datetime.now() - datetime.strptime(st.session_state.challenge_start_date, "%Y-%m-%d")).days + 1
    return min(max(days_elapsed, 1), 30)

# Title
st.markdown('<div class="linkedin-blue"><h1>🚀 LinkedIn Outreach Tracker Pro</h1><p>30-Day Challenge: 40 Connection Requests Daily + AI Systems Offer Follow-up | Google Sheets Integrated</p></div>', unsafe_allow_html=True)

# Sidebar
st.sidebar.header("☁️ Google Sheets Sync")

# Sync status
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("⬇️ Load Sheets", use_container_width=True):
        st.cache_data.clear()
        daily_data = load_daily_tracker()
        leads_data = load_leads_database()
        if daily_data is not None:
            st.session_state.sheets_data = daily_data
            st.sidebar.success("✅ Daily tracker loaded!")
        if leads_data is not None:
            st.session_state.leads_sheets_data = leads_data
            st.sidebar.success("✅ Leads data loaded!")
        st.rerun()

with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Quick Links")
st.sidebar.markdown(f"[📈 Daily Tracker Sheet](https://docs.google.com/spreadsheets/d/{DAILY_TRACKER_SHEET_ID}/edit)")
st.sidebar.markdown(f"[👥 Leads Database Sheet](https://docs.google.com/spreadsheets/d/{LEADS_DATABASE_SHEET_ID}/edit)")

# Load data
daily_df = st.session_state.sheets_data if st.session_state.sheets_data is not None else st.session_state.daily_tracker
leads_df = st.session_state.leads_sheets_data if st.session_state.leads_sheets_data is not None else load_leads_database()

# Challenge info
current_day = get_current_day()
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Challenge Overview")
st.sidebar.markdown(f"**📅 Day {current_day} of 30**")
st.sidebar.progress(current_day / 30)
st.sidebar.markdown(f"**Started:** {st.session_state.challenge_start_date}")

# Quick stats
total_sent = daily_df['Connections_Sent'].sum() if 'Connections_Sent' in daily_df.columns else 0
total_accepted = daily_df['Connections_Accepted'].sum() if 'Connections_Accepted' in daily_df.columns else 0
total_interested = daily_df['Interested_Responses'].sum() if 'Interested_Responses' in daily_df.columns else 0
total_conversions = daily_df['Conversions'].sum() if 'Conversions' in daily_df.columns else 0

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Total Progress")
st.sidebar.metric("Connections Sent", f"{int(total_sent)}/1,200", f"{int(total_sent/12)}%")
st.sidebar.metric("Accepted", int(total_accepted))
st.sidebar.metric("Interested", int(total_interested))
st.sidebar.metric("Conversions", int(total_conversions))

if total_sent > 0:
    acceptance_rate = (total_accepted / total_sent) * 100
    interest_rate = (total_interested / total_accepted * 100) if total_accepted > 0 else 0
    conversion_rate = (total_conversions / total_interested * 100) if total_interested > 0 else 0
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Conversion Funnel")
    st.sidebar.markdown(f"**Acceptance:** {acceptance_rate:.1f}%")
    st.sidebar.markdown(f"**Interest:** {interest_rate:.1f}%")
    st.sidebar.markdown(f"**Conversion:** {conversion_rate:.1f}%")

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

csv_leads = io.StringIO()
leads_df.to_csv(csv_leads, index=False)
st.sidebar.download_button(
    label="📥 Download Leads Database",
    data=csv_leads.getvalue(),
    file_name=f"leads_database_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=True
)

# Upload
uploaded_daily = st.sidebar.file_uploader("📤 Upload Daily Tracker", type=['csv'], key="daily")
if uploaded_daily:
    st.session_state.daily_tracker = pd.read_csv(uploaded_daily)
    st.sidebar.success("✅ Loaded!")

uploaded_leads = st.sidebar.file_uploader("📤 Upload Leads DB", type=['csv'], key="leads")
if uploaded_leads:
    st.session_state.leads_database = pd.read_csv(uploaded_leads)
    st.sidebar.success("✅ Loaded!")

# Main Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard", 
    "📅 Daily Tracker", 
    "👥 Leads Database",
    "☁️ Google Sheets View",
    "✅ Daily Checklist", 
    "📈 Analytics",
    "📖 Templates & Guide"
])

# TAB 1: DASHBOARD
with tab1:
    st.markdown("## 🎯 Performance Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
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
        st.markdown(f"<center>Want AI checklist</center>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card warning-card">', unsafe_allow_html=True)
        st.markdown("### 🎉 Conversions")
        st.markdown(f"<div class='big-metric'>{int(total_conversions)}</div>", unsafe_allow_html=True)
        conv_rate = (total_conversions/total_interested*100) if total_interested > 0 else 0
        st.markdown(f"<center>{conv_rate:.1f}% rate</center>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Pipeline
    st.markdown("## 🔄 Lead Pipeline")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    messages_sent = daily_df['Initial_Messages_Sent'].sum() if 'Initial_Messages_Sent' in daily_df.columns else 0
    
    with col1:
        st.markdown('<div class="stage-card">', unsafe_allow_html=True)
        st.markdown("**1️⃣ Sent**")
        st.metric("", int(total_sent))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="stage-card">', unsafe_allow_html=True)
        st.markdown("**2️⃣ Accepted**")
        st.metric("", int(total_accepted))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="stage-card">', unsafe_allow_html=True)
        st.markdown("**3️⃣ Messaged**")
        st.metric("", int(messages_sent))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="stage-card">', unsafe_allow_html=True)
        st.markdown("**4️⃣ Interested**")
        st.metric("", int(total_interested))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col5:
        st.markdown('<div class="stage-card">', unsafe_allow_html=True)
        st.markdown("**5️⃣ Converted**")
        st.metric("", int(total_conversions))
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Daily Activity Trend")
        if 'Date' in daily_df.columns and 'Connections_Sent' in daily_df.columns:
            fig = px.line(daily_df, x='Date', y=['Connections_Sent', 'Connections_Accepted', 'Conversions'],
                         title='Daily Performance', labels={'value': 'Count', 'variable': 'Metric'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Conversion Funnel")
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
    
    # Weekly summary
    st.markdown("## 📈 Weekly Performance")
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
    
    # Progress indicators
    avg_daily = total_sent / current_day if current_day > 0 else 0
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if avg_daily >= 40:
            st.markdown(f'<div class="success-box">✅ <b>On Track!</b> Daily avg: {avg_daily:.1f}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warning-box">⚠️ <b>Below Target</b> Daily avg: {avg_daily:.1f} (Goal: 40)</div>', unsafe_allow_html=True)
    
    with col2:
        remaining = 1200 - total_sent
        days_left = 30 - current_day
        needed_daily = remaining / days_left if days_left > 0 else 0
        st.markdown(f'<div class="stage-card"><b>To reach 1,200:</b> {needed_daily:.0f}/day for {days_left} days</div>', unsafe_allow_html=True)

# TAB 2: DAILY TRACKER
with tab2:
    st.markdown("## 📅 Daily Activity Tracker")
    
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
        
        if st.button("💾 Save Today's Progress", type="primary", use_container_width=True):
            daily_df.loc[today_idx, 'Connections_Sent'] = conn_today
            daily_df.loc[today_idx, 'Connections_Accepted'] = acc_today
            daily_df.loc[today_idx, 'Initial_Messages_Sent'] = msg_today
            daily_df.loc[today_idx, 'Interested_Responses'] = int_today
            daily_df.loc[today_idx, 'Links_Sent'] = link_today
            daily_df.loc[today_idx, 'Conversions'] = conv_today
            st.session_state.daily_tracker = daily_df
            st.success("✅ Saved!")
    
    st.markdown("---")
    st.markdown("### 📊 Full 30-Day View")
    st.dataframe(daily_df, use_container_width=True, height=400)

# TAB 3: LEADS DATABASE
with tab3:
    st.markdown("## 👥 Leads Database Management")
    
    with st.expander("➕ Add New Lead", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Name")
            new_linkedin = st.text_input("LinkedIn URL")
            new_status = st.selectbox("Status", ["Pending", "Accepted", "Declined"])
        with col2:
            new_stage = st.selectbox("Stage", [
                "Connection Sent", "Connection Accepted", "Initial Message Sent",
                "Interested in AI Systems", "Link Sent", "Follow-up 1", "Follow-up 2",
                "Follow-up 3", "Follow-up 4", "Converted", "Not Interested"
            ])
            new_notes = st.text_area("Notes")
        
        if st.button("➕ Add Lead"):
            if new_name and new_linkedin:
                new_lead = pd.DataFrame({
                    'Name': [new_name], 'LinkedIn_URL': [new_linkedin],
                    'Date_Connected': [datetime.now().strftime("%Y-%m-%d")],
                    'Connection_Status': [new_status], 'Stage': [new_stage],
                    'Initial_Message_Sent': [False], 'Interested': [False],
                    'Link_Sent_Date': [''], 'Follow_Up_1_Date': [''],
                    'Follow_Up_2_Date': [''], 'Follow_Up_3_Date': [''],
                    'Follow_Up_4_Date': [''], 'Converted': [False], 'Notes': [new_notes]
                })
                st.session_state.leads_database = pd.concat([st.session_state.leads_database, new_lead], ignore_index=True)
                st.success(f"✅ Added {new_name}!")
                st.rerun()
    
    st.markdown("---")
    
    if len(st.session_state.leads_database) > 0:
        st.markdown("### Current Leads")
        st.dataframe(st.session_state.leads_database, use_container_width=True, height=400)
    else:
        st.info("No leads yet. Add your first lead above!")

# TAB 4: GOOGLE SHEETS VIEW
with tab4:
    st.markdown("## ☁️ Google Sheets Live Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Daily Tracker from Sheets")
        if daily_df is not None and not daily_df.empty:
            st.dataframe(daily_df, use_container_width=True, height=400)
            
            # Show today's data from sheets
            st.markdown("#### Today's Google Sheets Data")
            today_date = datetime.now().strftime("%Y-%m-%d")
            if 'Date' in daily_df.columns:
                today_row = daily_df[daily_df['Date'].astype(str) == today_date]
                if not today_row.empty:
                    st.json(today_row.iloc[0].to_dict())
                else:
                    st.info("No data for today yet")
        else:
            st.warning("No daily tracker data loaded from Google Sheets")
    
    with col2:
        st.markdown("### 👥 Leads from Sheets")
        if leads_df is not None and not leads_df.empty:
            st.dataframe(leads_df.head(20), use_container_width=True, height=400)
            
            # Success metrics from leads
            if 'success' in leads_df.columns:
                successful = leads_df[leads_df['success'] == True]
                st.metric("Successful Outreach", len(successful))
                st.metric("Total Leads", len(leads_df))
        else:
            st.warning("No leads data loaded from Google Sheets")
    
    st.markdown("---")
    st.info("💡 Data auto-refreshes every 60 seconds. Click 'Load Sheets' or 'Refresh' in sidebar for immediate update.")

# TAB 5: DAILY CHECKLIST
with tab5:
    st.markdown("## ✅ Daily Outreach Checklist")
    st.markdown(f"### Day {current_day} of 30")
    
    st.markdown('<div class="stage-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 Today's Goals")
    st.markdown("""
    - [ ] Send 40 connection requests with personalized messages
    - [ ] Check for newly accepted connections
    - [ ] Send initial AI Systems Checklist offer
    - [ ] Follow up with interested leads
    - [ ] Send checklist links
    - [ ] Send follow-up messages (4-sequence)
    - [ ] Track conversions and update database
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Action items
    if len(st.session_state.leads_database) > 0:
        st.markdown("## 📋 Action Items")
        
        to_message = st.session_state.leads_database[
            (st.session_state.leads_database['Connection_Status'] == 'Accepted') &
            (st.session_state.leads_database['Initial_Message_Sent'] == False)
        ]
        
        if len(to_message) > 0:
            st.markdown(f'<div class="warning-box">⚠️ {len(to_message)} connections need initial message</div>', unsafe_allow_html=True)
    
    # Today's stats
    st.markdown("## 📊 Today's Progress")
    if today_idx < len(daily_df):
        today_data = daily_df.iloc[today_idx]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sent", int(today_data.get('Connections_Sent', 0)), f"Goal: 40")
        with col2:
            st.metric("Messaged", int(today_data.get('Initial_Messages_Sent', 0)))
        with col3:
            st.metric("Links", int(today_data.get('Links_Sent', 0)))
        with col4:
            st.metric("Conversions", int(today_data.get('Conversions', 0)))

# TAB 6: ANALYTICS
with tab6:
    st.markdown("## 📈 Advanced Analytics & Insights")
    
    # Performance metrics
    st.markdown("### 🎯 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if total_sent > 0:
            acceptance_rate = (total_accepted / total_sent) * 100
            st.metric("Acceptance Rate", f"{acceptance_rate:.1f}%", 
                     "Target: 30-40%", 
                     delta_color="normal" if acceptance_rate >= 30 else "off")
    
    with col2:
        if total_accepted > 0:
            message_rate = (messages_sent / total_accepted) * 100
            st.metric("Message Rate", f"{message_rate:.1f}%",
                     "% of accepted messaged")
    
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
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Cumulative Progress")
        if 'Day' in daily_df.columns:
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
        st.markdown("### 📈 Conversion Rates by Week")
        if 'Day' in daily_df.columns:
            weekly_df = daily_df.copy()
            weekly_df['Week'] = ((weekly_df['Day'] - 1) // 7) + 1
            
            weekly_rates = weekly_df.groupby('Week').apply(
                lambda x: pd.Series({
                    'Acceptance_Rate': (x['Connections_Accepted'].sum() / x['Connections_Sent'].sum() * 100) if x['Connections_Sent'].sum() > 0 else 0,
                    'Interest_Rate': (x['Interested_Responses'].sum() / x['Connections_Accepted'].sum() * 100) if x['Connections_Accepted'].sum() > 0 else 0,
                    'Conversion_Rate': (x['Conversions'].sum() / x['Interested_Responses'].sum() * 100) if x['Interested_Responses'].sum() > 0 else 0
                })
            ).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=weekly_rates['Week'], y=weekly_rates['Acceptance_Rate'], name='Acceptance %'))
            fig.add_trace(go.Bar(x=weekly_rates['Week'], y=weekly_rates['Interest_Rate'], name='Interest %'))
            fig.add_trace(go.Bar(x=weekly_rates['Week'], y=weekly_rates['Conversion_Rate'], name='Conversion %'))
            fig.update_layout(barmode='group', title='Weekly Conversion Rates (%)')
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed breakdown
    st.markdown("### 🔍 Detailed Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Follow-up Performance")
        followup_data = {
            'Stage': ['Follow-up 1', 'Follow-up 2', 'Follow-up 3', 'Follow-up 4'],
            'Count': [
                daily_df['Follow_Up_1'].sum() if 'Follow_Up_1' in daily_df.columns else 0,
                daily_df['Follow_Up_2'].sum() if 'Follow_Up_2' in daily_df.columns else 0,
                daily_df['Follow_Up_3'].sum() if 'Follow_Up_3' in daily_df.columns else 0,
                daily_df['Follow_Up_4'].sum() if 'Follow_Up_4' in daily_df.columns else 0
            ]
        }
        fig = px.bar(followup_data, x='Stage', y='Count', title='Follow-up Messages Sent')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Best Performing Days")
        if 'Conversions' in daily_df.columns:
            top_days = daily_df.nlargest(5, 'Conversions')[['Day', 'Date', 'Conversions', 'Connections_Sent']]
            st.dataframe(top_days, use_container_width=True)
    
    # Heatmap
    st.markdown("### 🔥 Activity Heatmap")
    if 'Day' in daily_df.columns:
        heatmap_df = daily_df[['Day', 'Connections_Sent', 'Connections_Accepted', 
                               'Initial_Messages_Sent', 'Conversions']].set_index('Day').T
        
        fig = px.imshow(heatmap_df, 
                       labels=dict(x="Day", y="Metric", color="Count"),
                       title="30-Day Activity Heatmap",
                       aspect="auto",
                       color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Projections
    st.markdown("### 🎯 Goal Projections")
    
    if current_day > 0 and total_sent > 0:
        avg_daily_sent = total_sent / current_day
        projected_total = avg_daily_sent * 30
        
        avg_acceptance = acceptance_rate if total_sent > 0 else 0
        projected_accepted = projected_total * (avg_acceptance / 100)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Projected Totals (30 days)")
            st.metric("Projected Connections Sent", f"{int(projected_total):,}")
            st.metric("Projected Accepted", f"{int(projected_accepted):,}")
        
        with col2:
            st.markdown("#### Gap to Goal")
            gap = 1200 - projected_total
            if gap > 0:
                st.metric("Shortfall", f"{int(gap):,}", delta=f"Need {gap/(30-current_day):.0f}/day", delta_color="inverse")
            else:
                st.metric("Surplus", f"{int(abs(gap)):,}", delta="On track! 🎉", delta_color="normal")
        
        with col3:
            st.markdown("#### Success Probability")
            success_prob = min(100, (projected_total / 1200) * 100)
            st.metric("Goal Achievement", f"{success_prob:.0f}%")
            
            if success_prob >= 100:
                st.success("✅ On track to exceed goal!")
            elif success_prob >= 80:
                st.info("📈 On track to meet goal!")
            else:
                st.warning("⚠️ Need to increase daily activity")
    
    # Google Sheets specific analytics
    if leads_df is not None and not leads_df.empty:
        st.markdown("---")
        st.markdown("### 👥 Leads Database Analytics (from Google Sheets)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'success' in leads_df.columns:
                success_count = leads_df['success'].sum()
                total_leads_count = len(leads_df)
                success_rate_leads = (success_count / total_leads_count * 100) if total_leads_count > 0 else 0
                st.metric("Successful Outreach", f"{success_count:,}")
                st.metric("Success Rate", f"{success_rate_leads:.1f}%")
        
        with col2:
            if 'timestamp' in leads_df.columns:
                today_leads = leads_df[leads_df['timestamp'].dt.date == datetime.now().date()]
                this_week = leads_df[leads_df['timestamp'] >= (datetime.now() - timedelta(days=7))]
                st.metric("Today's Leads", len(today_leads))
                st.metric("This Week's Leads", len(this_week))
        
        with col3:
            if 'connection_status' in leads_df.columns:
                connected = leads_df[leads_df['connection_status'].notna()].shape[0]
                st.metric("Connected Leads", connected)
        
        # Location breakdown
        if 'profile_location' in leads_df.columns or 'location' in leads_df.columns:
            st.markdown("#### 🌍 Geographic Distribution")
            location_col = 'profile_location' if 'profile_location' in leads_df.columns else 'location'
            top_locations = leads_df[location_col].value_counts().head(10)
            
            fig = px.bar(x=top_locations.values, y=top_locations.index, 
                        orientation='h', title='Top 10 Locations',
                        labels={'x': 'Count', 'y': 'Location'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Search term analysis
        if 'search_term' in leads_df.columns:
            st.markdown("#### 🔍 Top Search Terms")
            search_terms = leads_df['search_term'].value_counts().head(10)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.pie(values=search_terms.values, names=search_terms.index,
                           title='Search Term Distribution')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.dataframe(search_terms.reset_index().rename(
                    columns={'index': 'Search Term', 'search_term': 'Count'}))

# TAB 7: TEMPLATES & GUIDE
with tab7:
    st.markdown("## 📖 Message Templates & Strategy Guide")
    
    # Templates
    st.markdown("### 🤝 Connection Request Message")
    st.code("""Hi [First Name],

I noticed your work in [their industry/role] and thought we should connect. I help businesses implement AI automation systems and would love to share insights.

Looking forward to connecting!

[Your Name]""", language="text")
    
    st.markdown("---")
    
    st.markdown("### 💡 Initial Message - AI Systems Checklist Offer")
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
    
    st.markdown("---")
    
    st.markdown("### 🔗 Link Delivery Message")
    st.code("""Hi [First Name],

Great to hear you're interested! Here's the AI Systems Implementation Checklist:

[YOUR LINK HERE]

This covers everything you need to get started with AI automation. Take a look and let me know if you have any questions - happy to chat about how it could work for your specific situation.

Best,
[Your Name]""", language="text")
    
    st.markdown("---")
    
    st.markdown("### 📧 Follow-up Sequence (4 Messages)")
    
    with st.expander("📩 Follow-up 1 (3 days after link)", expanded=True):
        st.code("""Hi [First Name],

Just wanted to check in - did you get a chance to look at the AI Systems Checklist I sent over?

I'd love to hear your thoughts or answer any questions you might have about implementing AI in your workflow.

Best,
[Your Name]""", language="text")
    
    with st.expander("📩 Follow-up 2 (5 days after FU1)"):
        st.code("""Hi [First Name],

I know things get busy! I wanted to follow up on the AI checklist and see if you had any specific questions about implementation.

I've helped [X number] of businesses in [their industry] implement similar systems - happy to share some specific examples if that would be helpful.

Best,
[Your Name]""", language="text")
    
    with st.expander("📩 Follow-up 3 (7 days after FU2)"):
        st.code("""Hi [First Name],

Quick question - are you currently working on any AI or automation projects? 

I'd love to offer a free 15-minute consultation to discuss how the checklist could be customized for your specific needs. No strings attached, just want to be helpful!

Would you have time for a quick call this week or next?

Best,
[Your Name]""", language="text")
    
    with st.expander("📩 Follow-up 4 - Final Message (7 days after FU3)"):
        st.code("""Hi [First Name],

I don't want to keep bothering you, so this will be my last message on this topic!

The offer for the free AI consultation is still open if you ever want to discuss how AI systems could help your business. Feel free to reach out anytime.

In the meantime, I'll continue sharing valuable content about AI and automation - hope you find it useful!

Best of luck with everything,
[Your Name]""", language="text")
    
    st.markdown("---")
    
    # Strategy guide
    st.markdown("### 🎯 Complete Strategy Guide")
    
    with st.expander("📋 Daily Workflow (90 minutes total)"):
        st.markdown("""
        **Morning Block (30-45 minutes):**
        1. ☕ Send 20 connection requests with personalized messages
        2. ✅ Check for accepted connections from previous days
        3. 💬 Send initial AI Systems Checklist offer to new connections
        
        **Midday Block (15-20 minutes):**
        4. 📧 Check for responses to your initial messages
        5. 🔗 Send checklist links to interested leads
        6. ✏️ Mark interested leads in your database
        
        **Afternoon Block (30-45 minutes):**
        7. 🔗 Send remaining 20 connection requests
        8. 📤 Send scheduled follow-up messages (FU1, FU2, FU3, FU4)
        9. 📊 Update your tracker with all activities
        
        **Evening Review (10 minutes):**
        10. 📈 Review day's performance
        11. 🎯 Plan tomorrow's target list
        12. 📝 Update notes for leads needing attention
        """)
    
    with st.expander("🎯 Targeting Strategy"):
        st.markdown("""
        **Ideal LinkedIn Profiles:**
        - 👔 Business owners in service industries
        - 📱 Marketing directors/managers
        - ⚙️ Operations managers
        - 💡 Tech-savvy professionals
        - 🏢 Companies with 10-500 employees
        - 🎯 Industries: Marketing, Real Estate, Consulting, E-commerce, Professional Services
        
        **How to Find Them:**
        1. 🔍 Use LinkedIn Sales Navigator (if available)
        2. 🔎 Search by titles: "Founder", "CEO", "Marketing Director", "Operations Manager"
        3. 👥 Join relevant LinkedIn groups in your niche
        4. 💬 Check who's engaging with AI/automation content
        5. 🤝 Look at connections of your current clients
        6. 🏷️ Search hashtags: #AIAutomation #BusinessGrowth #DigitalTransformation
        """)
    
    with st.expander("💡 Best Practices & Pro Tips"):
        st.markdown("""
        **Connection Request Tips:**
        - ✍️ Personalize every message (mention their company, role, or recent post)
        - 📏 Keep it short (300 characters max)
        - 🎁 Don't pitch immediately - focus on value
        - 👤 Use their first name
        - 🎯 Reference something specific from their profile
        
        **Messaging Tips:**
        - ⏰ Wait 24 hours after connection before initial message
        - 💎 Always provide value first
        - ❓ Use questions to engage
        - 💬 Keep messages conversational, not salesy
        - 📅 Space out follow-ups (don't be pushy)
        - 😊 Use a friendly, helpful tone
        
        **Tracking Tips:**
        - 📊 Update your database daily (consistency is key!)
        - 📅 Set calendar reminders for follow-ups
        - 📝 Note personal details for future conversations
        - 📈 Track what messaging works best
        - 🔄 Adjust templates based on response rates
        - 🎯 A/B test different approaches
        """)
    
    with st.expander("⚠️ LinkedIn Limits & Safety Guidelines"):
        st.markdown("""
        **LinkedIn Connection Limits:**
        - 🆓 Free account: ~100 requests per week
        - 💼 Premium/Sales Navigator: ~200-400 requests per week
        - 📊 Daily limit: 40-50 connection requests (stay at 40 to be safe)
        - 🗑️ Withdraw pending requests after 2 weeks
        
        **Avoid Getting Flagged:**
        - ❌ Don't copy-paste identical messages
        - 🔄 Vary your connection request messages
        - ⏱️ Don't send too many requests in a short burst
        - ✅ Maintain good acceptance rate (aim for 30%+)
        - 💬 Respond to messages from your connections
        - 👍 Engage with content (like, comment) to appear authentic
        - 🎭 Act natural - LinkedIn algorithms detect bot behavior
        
        **Warning Signs:**
        - ⚠️ If LinkedIn warns about limits, stop for 24 hours
        - 📉 If acceptance rate drops below 20%, improve targeting/messaging
        - 🚫 If you get "We couldn't send your invitation" errors, take a break
        - 👁️ Watch for any restriction notifications
        """)
    
    with st.expander("📊 Success Metrics to Track"):
        st.markdown("""
        **Key Performance Indicators:**
        - 📈 **Connection Acceptance Rate:** Target 30-40%
        - 💬 **Message Response Rate:** Target 15-25%
        - 💡 **Interest Rate:** Target 10-20% of messaged leads
        - 🔗 **Link Click Rate:** Track in your analytics
        - 🎯 **Conversion Rate:** Target 5-15% of interested leads
        
        **Weekly Goals:**
        - 🗓️ Week 1: Focus on volume (280 connections sent)
        - 📊 Week 2: Optimize messaging based on response rates
        - 🎯 Week 3: Refine targeting and follow-up sequence
        - 🚀 Week 4: Scale what's working, hit 1,200 total
        
        **What Success Looks Like After 30 Days:**
        - ✅ 1,200 connection requests sent
        - 🤝 360-480 connections accepted (30-40% rate)
        - 💬 54-120 interested leads (15-25% of accepted)
        - 🎉 10-30 conversions (engaged with checklist)
        - 💼 5-10 qualified sales conversations
        """)
    
    with st.expander("🚀 Advanced Tactics"):
        st.markdown("""
        **Boosting Your Results:**
        - 📸 **Optimize Your Profile:** Professional photo, compelling headline, value-focused summary
        - 📝 **Content Strategy:** Post valuable AI/automation content 2-3x per week
        - 💬 **Engagement:** Comment thoughtfully on prospects' posts before connecting
        - 🎥 **Video Messages:** Use LinkedIn video for follow-ups (higher response rates)
        - 🏷️ **Lead Magnets:** Create multiple valuable resources (checklists, templates, guides)
        - 📱 **Multi-channel:** Combine LinkedIn with email outreach for better results
        
        **Personalization at Scale:**
        - 🔍 Research in batches: Spend 30 mins researching 20 profiles
        - 📋 Create templates with [brackets] for easy personalization
        - 🏢 Group by industry and use industry-specific templates
        - 🎯 Reference recent posts/activities (shows you're not spamming)
        - 💼 Mention mutual connections when possible
        
        **Follow-up Optimization:**
        - 📅 Track days between each touch point
        - 📊 Test different follow-up intervals
        - 💡 Add value in each follow-up (don't just "check in")
        - 🎁 Share relevant articles or resources
        - ❓ Ask specific questions that require a response
        """)
    
    st.markdown("---")
    
    # CSV Templates
    st.markdown("### 📥 Download CSV Templates")
    
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
        st.markdown("#### Leads Database Template")
        sample_leads = pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith'],
            'LinkedIn_URL': ['https://linkedin.com/in/johndoe', 'https://linkedin.com/in/janesmith'],
            'Date_Connected': ['2024-01-01', '2024-01-02'],
            'Connection_Status': ['Accepted', 'Pending'],
            'Stage': ['Initial Message Sent', 'Connection Sent'],
            'Initial_Message_Sent': [True, False],
            'Interested': [False, False],
            'Link_Sent_Date': ['', ''],
            'Follow_Up_1_Date': ['', ''],
            'Follow_Up_2_Date': ['', ''],
            'Follow_Up_3_Date': ['', ''],
            'Follow_Up_4_Date': ['', ''],
            'Converted': [False, False],
            'Notes': ['CEO of marketing agency', 'Found through AI automation group']
        })
        csv_sample_leads = io.StringIO()
        sample_leads.to_csv(csv_sample_leads, index=False)
        st.download_button(
            label="📥 Download Leads Database Template",
            data=csv_sample_leads.getvalue(),
            file_name="leads_database_template.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Getting started checklist
    st.markdown("### 🚀 30-Day Challenge Getting Started Checklist")
    st.markdown("""
    #### Pre-Launch (Day 0):
    - [ ] 📸 Set up LinkedIn profile professionally (clear photo, compelling headline)
    - [ ] 📄 Prepare your AI Systems Checklist and landing page
    - [ ] 🔗 Set up tracking links (use Bitly or similar for analytics)
    - [ ] 📊 Set up this tracker and test Google Sheets integration
    - [ ] 📝 Customize message templates with your personal voice
    - [ ] 🎯 Create initial target list (200+ prospects)
    - [ ] 📅 Set daily calendar reminders for outreach blocks
    - [ ] 💪 Commit mentally to 30 days of consistent action
    
    #### Week 1 Goals:
    - [ ] 🎯 Send 280 connection requests (40/day × 7 days)
    - [ ] 📊 Achieve 25%+ acceptance rate
    - [ ] 💬 Message all accepted connections within 24 hours
    - [ ] 📝 Refine messaging based on initial responses
    
    #### Week 2-4 Goals:
    - [ ] 📈 Maintain or increase acceptance rate
    - [ ] 🔄 Implement full follow-up sequence
    - [ ] 🎯 Hit 1,200 total connections by Day 30
    - [ ] 💼 Generate 10+ qualified sales conversations
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><b>🔥 30-Day LinkedIn Outreach Challenge Pro 🔥</b></p>
    <p>⚡ Powered by Google Sheets Integration | Real-time Analytics | Complete Template Library</p>
    <p style='font-size: 1.1em; margin-top: 15px;'><b>Consistency is key! Show up every day and the results will follow.</b></p>
    <p style='font-size: 0.9em; margin-top: 10px;'>💡 Pro Tip: Block out 90 minutes daily for LinkedIn outreach. Make it a non-negotiable habit!</p>
    <p style='font-size: 0.85em; margin-top: 15px; color: #999;'>📊 Data syncs from Google Sheets every 60 seconds | 💾 Download backups regularly | 🎯 Track everything!</p>
</div>
""", unsafe_allow_html=True)
