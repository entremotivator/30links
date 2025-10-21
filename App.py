import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import io

# Page configuration
st.set_page_config(page_title="LinkedIn Outreach Tracker", page_icon="💼", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .big-metric {
        font-size: 3em;
        font-weight: bold;
        text-align: center;
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
</style>
""", unsafe_allow_html=True)

# Google Sheets URLs
DAILY_TRACKER_SHEET_ID = "1UkuTf8VwGPIilTxhTEdP9K-zdtZFnThazFdGyxVYfmg"
LEADS_DATABASE_SHEET_ID = "1eLEFvyV1_f74UC1g5uQ-xA7A62sK8Pog27KIjw_Sk3Y"
DAILY_TRACKER_SHEET_NAME = "daily_tracker_20251021"
LEADS_SHEET_NAME = "Sheet1"  # Adjust if needed

# Function to get CSV export URL
def get_sheet_csv_url(sheet_id, gid=0):
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

# Function to get sheet data by name
def get_sheet_by_name(sheet_id, sheet_name):
    # First try to get all sheets to find the gid
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
    except:
        pass
    
    # Fallback to default sheet
    try:
        url = get_sheet_csv_url(sheet_id, 0)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
    except:
        pass
    
    return None

# Function to load daily tracker data
@st.cache_data(ttl=60)
def load_daily_tracker():
    try:
        df = get_sheet_by_name(DAILY_TRACKER_SHEET_ID, DAILY_TRACKER_SHEET_NAME)
        if df is not None and not df.empty:
            # Clean column names
            df.columns = df.columns.str.strip()
            # Convert numeric columns
            numeric_cols = ['Connections_Sent', 'Connections_Accepted', 'Initial_Messages_Sent', 
                          'Interested_Responses', 'Links_Sent', 'Follow_Up_1', 'Follow_Up_2', 
                          'Follow_Up_3', 'Follow_Up_4', 'Conversions']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            return df
        return None
    except Exception as e:
        st.error(f"Error loading daily tracker: {str(e)}")
        return None

# Function to load leads database
@st.cache_data(ttl=60)
def load_leads_database():
    try:
        df = get_sheet_by_name(LEADS_DATABASE_SHEET_ID, LEADS_SHEET_NAME)
        if df is not None and not df.empty:
            # Clean column names
            df.columns = df.columns.str.strip()
            # Parse success column
            if 'success' in df.columns:
                df['success'] = df['success'].astype(str).str.lower() == 'true'
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            return df
        return None
    except Exception as e:
        st.error(f"Error loading leads database: {str(e)}")
        return None

# Title
st.title("💼 LinkedIn Outreach Tracker")
st.markdown("### *Track your daily LinkedIn outreach activities and lead pipeline*")

# Sidebar
st.sidebar.header("📊 Data Sources")
st.sidebar.markdown(f"**Daily Tracker Sheet:** `{DAILY_TRACKER_SHEET_NAME}`")
st.sidebar.markdown(f"**Leads Database:** Connected")

# Refresh button
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Quick Links")
st.sidebar.markdown(f"[📈 Open Daily Tracker](https://docs.google.com/spreadsheets/d/{DAILY_TRACKER_SHEET_ID}/edit)")
st.sidebar.markdown(f"[👥 Open Leads Database](https://docs.google.com/spreadsheets/d/{LEADS_DATABASE_SHEET_ID}/edit)")

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ About")
st.sidebar.info("""
This tracker reads directly from your Google Sheets:
- Real-time data sync
- No authentication needed
- Auto-refreshes every 60 seconds
- Edit sheets directly in Google
""")

# Load data
with st.spinner("Loading data from Google Sheets..."):
    daily_df = load_daily_tracker()
    leads_df = load_leads_database()

if daily_df is None and leads_df is None:
    st.error("❌ Could not load data from Google Sheets. Please check your sheet permissions (should be 'Anyone with link can view')")
    st.stop()

# Main dashboard
st.markdown("## 📊 Today's Overview")

# Current date
today = datetime.now().strftime("%Y-%m-%d")
st.caption(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")

# Today's stats from daily tracker
today_stats = {}
if daily_df is not None and 'Date' in daily_df.columns:
    today_row = daily_df[daily_df['Date'].astype(str) == today]
    if not today_row.empty:
        today_stats = today_row.iloc[0].to_dict()

# Display today's metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("### 📤 Connections Sent")
    st.markdown(f"<div class='big-metric'>{today_stats.get('Connections_Sent', 0)}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card success-card">', unsafe_allow_html=True)
    st.markdown("### ✅ Accepted")
    st.markdown(f"<div class='big-metric'>{today_stats.get('Connections_Accepted', 0)}</div>", unsafe_allow_html=True)
    if today_stats.get('Connections_Sent', 0) > 0:
        acceptance_rate = (today_stats.get('Connections_Accepted', 0) / today_stats.get('Connections_Sent', 1)) * 100
        st.markdown(f"<center>{acceptance_rate:.1f}% rate</center>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card info-card">', unsafe_allow_html=True)
    st.markdown("### 💬 Messages Sent")
    st.markdown(f"<div class='big-metric'>{today_stats.get('Initial_Messages_Sent', 0)}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card warning-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 Conversions")
    st.markdown(f"<div class='big-metric'>{today_stats.get('Conversions', 0)}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Secondary metrics
st.markdown("## 📈 Detailed Activity")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("😊 Interested Responses", today_stats.get('Interested_Responses', 0))
    st.metric("🔗 Links Sent", today_stats.get('Links_Sent', 0))

with col2:
    st.metric("📧 Follow-up 1", today_stats.get('Follow_Up_1', 0))
    st.metric("📧 Follow-up 2", today_stats.get('Follow_Up_2', 0))

with col3:
    st.metric("📧 Follow-up 3", today_stats.get('Follow_Up_3', 0))
    st.metric("📧 Follow-up 4", today_stats.get('Follow_Up_4', 0))

# Notes section
if 'Notes' in today_stats and pd.notna(today_stats.get('Notes')) and str(today_stats.get('Notes')).strip():
    st.markdown("### 📝 Today's Notes")
    st.info(today_stats.get('Notes'))

st.markdown("---")

# 30-Day Performance
st.markdown("## 📅 30-Day Performance")

if daily_df is not None and not daily_df.empty:
    # Calculate totals
    total_connections_sent = daily_df['Connections_Sent'].sum()
    total_connections_accepted = daily_df['Connections_Accepted'].sum()
    total_messages = daily_df['Initial_Messages_Sent'].sum()
    total_conversions = daily_df['Conversions'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Connections Sent", f"{total_connections_sent:,}")
    with col2:
        st.metric("Total Accepted", f"{total_connections_accepted:,}")
        if total_connections_sent > 0:
            acceptance_rate = (total_connections_accepted / total_connections_sent) * 100
            st.caption(f"Acceptance Rate: {acceptance_rate:.1f}%")
    with col3:
        st.metric("Total Messages", f"{total_messages:,}")
    with col4:
        st.metric("Total Conversions", f"{total_conversions:,}")
        if total_messages > 0:
            conversion_rate = (total_conversions / total_messages) * 100
            st.caption(f"Conversion Rate: {conversion_rate:.1f}%")
    
    # Chart
    st.markdown("### 📊 Daily Activity Chart")
    
    chart_df = daily_df[['Date', 'Connections_Sent', 'Connections_Accepted', 'Initial_Messages_Sent', 'Conversions']].copy()
    chart_df = chart_df.set_index('Date')
    
    st.line_chart(chart_df)

st.markdown("---")

# Leads Database Analysis
st.markdown("## 👥 Leads Database Insights")

if leads_df is not None and not leads_df.empty:
    # Success metrics
    if 'success' in leads_df.columns:
        successful_leads = leads_df[leads_df['success'] == True]
        total_leads = len(leads_df)
        successful_count = len(successful_leads)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Leads", f"{total_leads:,}")
        with col2:
            st.metric("Successful Outreach", f"{successful_count:,}")
            if total_leads > 0:
                success_rate = (successful_count / total_leads) * 100
                st.caption(f"{success_rate:.1f}% success rate")
        with col3:
            if 'connection_status' in leads_df.columns:
                connected = leads_df[leads_df['connection_status'].notna()].shape[0]
                st.metric("Connections Made", f"{connected:,}")
        with col4:
            if 'timestamp' in leads_df.columns:
                today_leads = leads_df[leads_df['timestamp'].dt.date == datetime.now().date()]
                st.metric("Today's Leads", f"{len(today_leads):,}")
    
    # Search terms analysis
    if 'search_term' in leads_df.columns:
        st.markdown("### 🔍 Top Search Terms")
        search_terms = leads_df['search_term'].value_counts().head(10)
        st.bar_chart(search_terms)
    
    # Location analysis
    if 'profile_location' in leads_df.columns or 'location' in leads_df.columns:
        st.markdown("### 🌍 Top Locations")
        location_col = 'profile_location' if 'profile_location' in leads_df.columns else 'location'
        locations = leads_df[location_col].value_counts().head(10)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(locations)
        with col2:
            st.dataframe(locations.reset_index().rename(columns={'index': 'Location', location_col: 'Count'}))
    
    # Recent leads
    st.markdown("### 🆕 Recent Leads")
    
    display_cols = ['timestamp', 'profile_name', 'profile_location', 'connection_status', 'success']
    available_cols = [col for col in display_cols if col in leads_df.columns]
    
    if available_cols:
        recent_leads = leads_df.sort_values('timestamp', ascending=False).head(10) if 'timestamp' in leads_df.columns else leads_df.head(10)
        st.dataframe(recent_leads[available_cols], use_container_width=True)
    
    # Detailed lead view
    with st.expander("🔍 View All Leads Data"):
        st.dataframe(leads_df, use_container_width=True, height=400)

else:
    st.warning("No leads data available")

# Daily tracker detailed view
st.markdown("---")
st.markdown("## 📋 Daily Tracker History")

if daily_df is not None and not daily_df.empty:
    with st.expander("📊 View All Daily Data", expanded=False):
        st.dataframe(daily_df, use_container_width=True, height=400)
else:
    st.warning("No daily tracker data available")

# Footer
st.markdown("---")
st.caption("💡 **Tip:** Data refreshes automatically every 60 seconds. Click 'Refresh Data' for immediate updates.")
st.caption("📝 **Note:** To update data, edit the Google Sheets directly. Changes will appear after refresh.")
