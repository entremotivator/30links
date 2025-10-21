import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(page_title="LinkedIn Outreach Tracker", page_icon="🤝", layout="wide")

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

# Title
st.markdown('<div class="linkedin-blue"><h1>🤝 LinkedIn Lead Outreach Tracker</h1><p>30-Day Challenge: 40 Connection Requests Daily + AI Systems Offer Follow-up</p></div>', unsafe_allow_html=True)

# Initialize session state
if 'daily_tracker' not in st.session_state:
    start_date = datetime.now()
    dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
    
    st.session_state.daily_tracker = pd.DataFrame({
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

if 'leads_database' not in st.session_state:
    st.session_state.leads_database = pd.DataFrame({
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

if 'challenge_start_date' not in st.session_state:
    st.session_state.challenge_start_date = datetime.now().strftime("%Y-%m-%d")

# Helper function to calculate days elapsed
def get_current_day():
    days_elapsed = (datetime.now() - datetime.strptime(st.session_state.challenge_start_date, "%Y-%m-%d")).days + 1
    return min(days_elapsed, 30)

# Sidebar
st.sidebar.header("📊 Challenge Overview")
current_day = get_current_day()
st.sidebar.markdown(f"### 📅 Day {current_day} of 30")
st.sidebar.progress(current_day / 30)
st.sidebar.markdown(f"**Started:** {st.session_state.challenge_start_date}")

# Quick stats in sidebar
total_sent = st.session_state.daily_tracker['Connections_Sent'].sum()
total_accepted = st.session_state.daily_tracker['Connections_Accepted'].sum()
total_interested = st.session_state.daily_tracker['Interested_Responses'].sum()
total_conversions = st.session_state.daily_tracker['Conversions'].sum()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Total Progress")
st.sidebar.metric("Connection Requests", f"{int(total_sent)}/1,200", f"{int(total_sent/12)}%")
st.sidebar.metric("Accepted", int(total_accepted))
st.sidebar.metric("Interested in AI Systems", int(total_interested))
st.sidebar.metric("Conversions", int(total_conversions))

if total_sent > 0:
    acceptance_rate = (total_accepted / total_sent) * 100
    interest_rate = (total_interested / total_accepted * 100) if total_accepted > 0 else 0
    conversion_rate = (total_conversions / total_interested * 100) if total_interested > 0 else 0
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Conversion Funnel")
    st.sidebar.markdown(f"**Acceptance Rate:** {acceptance_rate:.1f}%")
    st.sidebar.markdown(f"**Interest Rate:** {interest_rate:.1f}%")
    st.sidebar.markdown(f"**Conversion Rate:** {conversion_rate:.1f}%")

st.sidebar.markdown("---")

# Export/Import
st.sidebar.markdown("### 💾 Data Management")

# Export daily tracker
csv_daily = io.StringIO()
st.session_state.daily_tracker.to_csv(csv_daily, index=False)
st.sidebar.download_button(
    label="📥 Download Daily Tracker",
    data=csv_daily.getvalue(),
    file_name=f"daily_tracker_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=True
)

# Export leads database
csv_leads = io.StringIO()
st.session_state.leads_database.to_csv(csv_leads, index=False)
st.sidebar.download_button(
    label="📥 Download Leads Database",
    data=csv_leads.getvalue(),
    file_name=f"leads_database_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=True
)

# Upload files
uploaded_daily = st.sidebar.file_uploader("📤 Upload Daily Tracker", type=['csv'], key="daily")
if uploaded_daily:
    st.session_state.daily_tracker = pd.read_csv(uploaded_daily)
    st.sidebar.success("✅ Daily tracker loaded!")

uploaded_leads = st.sidebar.file_uploader("📤 Upload Leads Database", type=['csv'], key="leads")
if uploaded_leads:
    st.session_state.leads_database = pd.read_csv(uploaded_leads)
    st.sidebar.success("✅ Leads database loaded!")

# Main Dashboard
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📅 Daily Tracker", "👥 Leads Database", "✅ Daily Checklist", "📖 Templates & Guide"])

# TAB 1: DASHBOARD
with tab1:
    st.markdown("## 🎯 Performance Dashboard")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 🔗 Connections Sent")
        st.markdown(f"<div class='big-metric'>{int(total_sent)}</div>", unsafe_allow_html=True)
        st.markdown(f"<center>Goal: 1,200</center>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ✅ Accepted")
        st.markdown(f"<div class='big-metric'>{int(total_accepted)}</div>", unsafe_allow_html=True)
        acceptance = (total_accepted/total_sent*100) if total_sent > 0 else 0
        st.markdown(f"<center>{acceptance:.1f}% rate</center>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("### 💡 Interested")
        st.markdown(f"<div class='big-metric'>{int(total_interested)}</div>", unsafe_allow_html=True)
        st.markdown(f"<center>Want AI checklist</center>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("### 🎉 Conversions")
        st.markdown(f"<div class='big-metric'>{int(total_conversions)}</div>", unsafe_allow_html=True)
        conv_rate = (total_conversions/total_interested*100) if total_interested > 0 else 0
        st.markdown(f"<center>{conv_rate:.1f}% rate</center>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Pipeline Visualization
    st.markdown("## 🔄 Lead Pipeline")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown('<div class="stage-card">', unsafe_allow_html=True)
        st.markdown("**1️⃣ Connections Sent**")
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
        st.metric("", int(st.session_state.daily_tracker['Initial_Messages_Sent'].sum()))
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
    
    # Weekly Performance
    st.markdown("## 📈 Weekly Performance")
    
    df_weekly = st.session_state.daily_tracker.copy()
    df_weekly['Week'] = ((df_weekly['Day'] - 1) // 7) + 1
    
    weekly_summary = df_weekly.groupby('Week').agg({
        'Connections_Sent': 'sum',
        'Connections_Accepted': 'sum',
        'Interested_Responses': 'sum',
        'Conversions': 'sum'
    }).reset_index()
    
    weekly_summary['Week'] = 'Week ' + weekly_summary['Week'].astype(str)
    
    st.dataframe(weekly_summary, use_container_width=True)
    
    # Daily average
    avg_daily = total_sent / current_day if current_day > 0 else 0
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if avg_daily >= 40:
            st.markdown(f'<div class="success-box">✅ <b>On Track!</b> Daily average: {avg_daily:.1f} connections</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warning-box">⚠️ <b>Below Target</b> Daily average: {avg_daily:.1f} connections (Goal: 40)</div>', unsafe_allow_html=True)
    
    with col2:
        remaining = 1200 - total_sent
        days_left = 30 - current_day
        needed_daily = remaining / days_left if days_left > 0 else 0
        st.markdown(f'<div class="stage-card"><b>To reach 1,200:</b> Send {needed_daily:.0f} connections/day for {days_left} days</div>', unsafe_allow_html=True)

# TAB 2: DAILY TRACKER
with tab2:
    st.markdown("## 📅 Daily Activity Tracker")
    st.markdown("*Track your daily outreach activities and progress*")
    
    # Quick entry for today
    st.markdown("### ⚡ Quick Entry - Today")
    
    today_idx = current_day - 1
    if today_idx < 30:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            connections_today = st.number_input("Connections Sent Today", 0, 100, 
                                               int(st.session_state.daily_tracker.loc[today_idx, 'Connections_Sent']),
                                               key="today_connections")
            accepted_today = st.number_input("Connections Accepted", 0, 100,
                                            int(st.session_state.daily_tracker.loc[today_idx, 'Connections_Accepted']),
                                            key="today_accepted")
        
        with col2:
            messages_today = st.number_input("Initial Messages Sent", 0, 100,
                                            int(st.session_state.daily_tracker.loc[today_idx, 'Initial_Messages_Sent']),
                                            key="today_messages")
            interested_today = st.number_input("Interested Responses", 0, 100,
                                              int(st.session_state.daily_tracker.loc[today_idx, 'Interested_Responses']),
                                              key="today_interested")
        
        with col3:
            links_today = st.number_input("Links Sent", 0, 100,
                                         int(st.session_state.daily_tracker.loc[today_idx, 'Links_Sent']),
                                         key="today_links")
            conversions_today = st.number_input("Conversions", 0, 100,
                                               int(st.session_state.daily_tracker.loc[today_idx, 'Conversions']),
                                               key="today_conversions")
        
        if st.button("💾 Save Today's Progress", type="primary", use_container_width=True):
            st.session_state.daily_tracker.loc[today_idx, 'Connections_Sent'] = connections_today
            st.session_state.daily_tracker.loc[today_idx, 'Connections_Accepted'] = accepted_today
            st.session_state.daily_tracker.loc[today_idx, 'Initial_Messages_Sent'] = messages_today
            st.session_state.daily_tracker.loc[today_idx, 'Interested_Responses'] = interested_today
            st.session_state.daily_tracker.loc[today_idx, 'Links_Sent'] = links_today
            st.session_state.daily_tracker.loc[today_idx, 'Conversions'] = conversions_today
            st.success("✅ Today's progress saved!")
            st.rerun()
    
    st.markdown("---")
    
    # Full tracker view
    st.markdown("### 📊 All 30 Days")
    
    edited_df = st.data_editor(
        st.session_state.daily_tracker,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "Day": st.column_config.NumberColumn("Day", disabled=True),
            "Date": st.column_config.TextColumn("Date", disabled=True),
            "Connections_Sent": st.column_config.NumberColumn("Sent", min_value=0, max_value=100),
            "Connections_Accepted": st.column_config.NumberColumn("Accepted", min_value=0, max_value=100),
            "Initial_Messages_Sent": st.column_config.NumberColumn("Messaged", min_value=0, max_value=100),
            "Interested_Responses": st.column_config.NumberColumn("Interested", min_value=0, max_value=100),
            "Links_Sent": st.column_config.NumberColumn("Links", min_value=0, max_value=100),
            "Follow_Up_1": st.column_config.NumberColumn("FU1", min_value=0, max_value=100),
            "Follow_Up_2": st.column_config.NumberColumn("FU2", min_value=0, max_value=100),
            "Follow_Up_3": st.column_config.NumberColumn("FU3", min_value=0, max_value=100),
            "Follow_Up_4": st.column_config.NumberColumn("FU4", min_value=0, max_value=100),
            "Conversions": st.column_config.NumberColumn("Conversions", min_value=0, max_value=100),
            "Notes": st.column_config.TextColumn("Notes", width="large")
        }
    )
    
    if st.button("💾 Update All Changes"):
        st.session_state.daily_tracker = edited_df
        st.success("✅ All changes saved!")

# TAB 3: LEADS DATABASE
with tab3:
    st.markdown("## 👥 Leads Database Management")
    st.markdown("*Track individual leads through the entire pipeline*")
    
    # Add new lead
    with st.expander("➕ Add New Lead", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Name")
            new_linkedin = st.text_input("LinkedIn URL")
            new_status = st.selectbox("Connection Status", ["Pending", "Accepted", "Declined"])
        with col2:
            new_stage = st.selectbox("Current Stage", [
                "Connection Sent",
                "Connection Accepted",
                "Initial Message Sent",
                "Interested in AI Systems",
                "Link Sent",
                "Follow-up 1",
                "Follow-up 2",
                "Follow-up 3",
                "Follow-up 4",
                "Converted",
                "Not Interested"
            ])
            new_notes = st.text_area("Notes")
        
        if st.button("➕ Add Lead"):
            if new_name and new_linkedin:
                new_lead = pd.DataFrame({
                    'Name': [new_name],
                    'LinkedIn_URL': [new_linkedin],
                    'Date_Connected': [datetime.now().strftime("%Y-%m-%d")],
                    'Connection_Status': [new_status],
                    'Stage': [new_stage],
                    'Initial_Message_Sent': [False],
                    'Interested': [False],
                    'Link_Sent_Date': [''],
                    'Follow_Up_1_Date': [''],
                    'Follow_Up_2_Date': [''],
                    'Follow_Up_3_Date': [''],
                    'Follow_Up_4_Date': [''],
                    'Converted': [False],
                    'Notes': [new_notes]
                })
                st.session_state.leads_database = pd.concat([st.session_state.leads_database, new_lead], ignore_index=True)
                st.success(f"✅ Added {new_name} to database!")
                st.rerun()
            else:
                st.error("Please enter name and LinkedIn URL")
    
    st.markdown("---")
    
    # Filter leads
    st.markdown("### 🔍 Filter Leads")
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        stage_filter = st.multiselect("Filter by Stage", [
            "All",
            "Connection Sent",
            "Connection Accepted",
            "Initial Message Sent",
            "Interested in AI Systems",
            "Link Sent",
            "Follow-up 1",
            "Follow-up 2",
            "Follow-up 3",
            "Follow-up 4",
            "Converted",
            "Not Interested"
        ], default=["All"])
    
    with filter_col2:
        connection_filter = st.multiselect("Filter by Connection Status", 
                                          ["All", "Pending", "Accepted", "Declined"],
                                          default=["All"])
    
    # Display filtered leads
    if len(st.session_state.leads_database) > 0:
        filtered_df = st.session_state.leads_database.copy()
        
        if "All" not in stage_filter and len(stage_filter) > 0:
            filtered_df = filtered_df[filtered_df['Stage'].isin(stage_filter)]
        
        if "All" not in connection_filter and len(connection_filter) > 0:
            filtered_df = filtered_df[filtered_df['Connection_Status'].isin(connection_filter)]
        
        st.markdown(f"**Showing {len(filtered_df)} leads**")
        
        edited_leads = st.data_editor(
            filtered_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "LinkedIn_URL": st.column_config.LinkColumn("LinkedIn Profile"),
                "Date_Connected": st.column_config.DateColumn("Connected"),
                "Connection_Status": st.column_config.SelectboxColumn("Status", 
                    options=["Pending", "Accepted", "Declined"]),
                "Stage": st.column_config.SelectboxColumn("Stage",
                    options=[
                        "Connection Sent",
                        "Connection Accepted",
                        "Initial Message Sent",
                        "Interested in AI Systems",
                        "Link Sent",
                        "Follow-up 1",
                        "Follow-up 2",
                        "Follow-up 3",
                        "Follow-up 4",
                        "Converted",
                        "Not Interested"
                    ]),
                "Initial_Message_Sent": st.column_config.CheckboxColumn("Messaged"),
                "Interested": st.column_config.CheckboxColumn("Interested"),
                "Converted": st.column_config.CheckboxColumn("Converted"),
                "Notes": st.column_config.TextColumn("Notes", width="large")
            }
        )
        
        if st.button("💾 Save Lead Updates"):
            # Update the main database with filtered changes
            for idx, row in edited_leads.iterrows():
                if idx in st.session_state.leads_database.index:
                    st.session_state.leads_database.loc[idx] = row
            st.success("✅ Lead database updated!")
    else:
        st.info("No leads in database yet. Add your first lead above!")

# TAB 4: DAILY CHECKLIST
with tab4:
    st.markdown("## ✅ Daily Outreach Checklist")
    st.markdown(f"### Day {current_day} of 30")
    
    st.markdown('<div class="stage-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 Today's Goals")
    st.markdown("""
    - [ ] Send 40 connection requests with personalized messages
    - [ ] Check for newly accepted connections
    - [ ] Send initial AI Systems Checklist offer to new connections
    - [ ] Follow up with interested leads
    - [ ] Send checklist links to those who responded
    - [ ] Send follow-up messages (4-message sequence)
    - [ ] Track conversions and update database
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Action items based on pipeline
    if len(st.session_state.leads_database) > 0:
        st.markdown("## 📋 Action Items Today")
        
        # New acceptances to message
        to_message = st.session_state.leads_database[
            (st.session_state.leads_database['Connection_Status'] == 'Accepted') &
            (st.session_state.leads_database['Initial_Message_Sent'] == False)
        ]
        
        if len(to_message) > 0:
            st.markdown(f'<div class="warning-box">⚠️ <b>{len(to_message)} new connections</b> waiting for initial AI Systems message</div>', unsafe_allow_html=True)
            with st.expander(f"View {len(to_message)} leads to message"):
                st.dataframe(to_message[['Name', 'LinkedIn_URL', 'Date_Connected']], use_container_width=True)
        
        # Interested leads to send link
        to_send_link = st.session_state.leads_database[
            (st.session_state.leads_database['Interested'] == True) &
            (st.session_state.leads_database['Link_Sent_Date'].astype(str) == '')
        ]
        
        if len(to_send_link) > 0:
            st.markdown(f'<div class="warning-box">💡 <b>{len(to_send_link)} interested leads</b> waiting for checklist link</div>', unsafe_allow_html=True)
            with st.expander(f"View {len(to_send_link)} leads to send link"):
                st.dataframe(to_send_link[['Name', 'LinkedIn_URL', 'Stage']], use_container_width=True)
        
        # Follow-ups needed
        for follow_up_num in range(1, 5):
            stage_name = f"Follow-up {follow_up_num}"
            leads_needing_followup = st.session_state.leads_database[
                st.session_state.leads_database['Stage'] == stage_name
            ]
            
            if len(leads_needing_followup) > 0:
                st.markdown(f'<div class="stage-card">📧 <b>{len(leads_needing_followup)} leads</b> ready for Follow-up {follow_up_num}</div>', unsafe_allow_html=True)
                with st.expander(f"View leads for Follow-up {follow_up_num}"):
                    st.dataframe(leads_needing_followup[['Name', 'LinkedIn_URL', 'Link_Sent_Date']], use_container_width=True)
    
    else:
        st.info("Start adding leads to your database to see action items!")
    
    st.markdown("---")
    
    # Quick stats
    st.markdown("## 📊 Today's Progress")
    today_idx = current_day - 1
    if today_idx < 30:
        today_data = st.session_state.daily_tracker.iloc[today_idx]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Connections Sent", int(today_data['Connections_Sent']), 
                     f"Goal: 40 ({int(today_data['Connections_Sent']/40*100)}%)")
        with col2:
            st.metric("Messages Sent", int(today_data['Initial_Messages_Sent']))
        with col3:
            st.metric("Links Sent", int(today_data['Links_Sent']))
        with col4:
            st.metric("Conversions", int(today_data['Conversions']))

# TAB 5: TEMPLATES & GUIDE
with tab5:
    st.markdown("## 📖 Message Templates & Strategy Guide")
    
    st.markdown("### 🤝 Connection Request Message Template")
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
    
    st.markdown("#### Follow-up 1 (3 days after link)")
    st.code("""Hi [First Name],

Just wanted to check in - did you get a chance to look at the AI Systems Checklist I sent over?

I'd love to hear your thoughts or answer any questions you might have about implementing AI in your workflow.

Best,
[Your Name]""", language="text")
    
    st.markdown("#### Follow-up 2 (5 days after FU1)")
    st.code("""Hi [First Name],

I know things get busy! I wanted to follow up on the AI checklist and see if you had any specific questions about implementation.

I've helped [X number] of businesses in [their industry] implement similar systems - happy to share some specific examples if that would be helpful.

Best,
[Your Name]""", language="text")
    
    st.markdown("#### Follow-up 3 (7 days after FU2)")
    st.code("""Hi [First Name],

Quick question - are you currently working on any AI or automation projects? 

I'd love to offer a free 15-minute consultation to discuss how the checklist could be customized for your specific needs. No strings attached, just want to be helpful!

Would you have time for a quick call this week or next?

Best,
[Your Name]""", language="text")
    
    st.markdown("#### Follow-up 4 - Final Message (7 days after FU3)")
    st.code("""Hi [First Name],

I don't want to keep bothering you, so this will be my last message on this topic!

The offer for the free AI consultation is still open if you ever want to discuss how AI systems could help your business. Feel free to reach out anytime.

In the meantime, I'll continue sharing valuable content about AI and automation - hope you find it useful!

Best of luck with everything,
[Your Name]""", language="text")
    
    st.markdown("---")
    
    st.markdown("### 🎯 Strategy Guide")
    
    with st.expander("📋 Daily Workflow"):
        st.markdown("""
        **Morning (30-45 minutes):**
        1. Send 20 connection requests with personalized messages
        2. Check for accepted connections from previous days
        3. Send initial AI Systems Checklist offer to new connections
        
        **Midday (15-20 minutes):**
        4. Check for responses to your initial messages
        5. Send checklist links to interested leads
        6. Mark interested leads in your database
        
        **Afternoon (30-45 minutes):**
        7. Send remaining 20 connection requests
        8. Send scheduled follow-up messages (FU1, FU2, FU3, FU4)
        9. Update your tracker with all activities
        
        **Evening (10 minutes):**
        10. Review day's performance
        11. Plan tomorrow's target list
        12. Update notes for leads that need attention
        """)
    
    with st.expander("🎯 Targeting Strategy"):
        st.markdown("""
        **Ideal LinkedIn Profiles to Target:**
        - Business owners in service industries
        - Marketing directors/managers
        - Operations managers
        - Tech-savvy professionals
        - Companies with 10-500 employees
        - Industries: Marketing, Real Estate, Consulting, E-commerce, Professional Services
        
        **How to Find Them:**
        1. Use LinkedIn Sales Navigator (if available)
        2. Search by job titles: "Founder", "CEO", "Marketing Director", "Operations Manager"
        3. Join relevant LinkedIn groups in your niche
        4. Check who's engaging with AI/automation content
        5. Look at connections of your current clients
        """)
    
    with st.expander("💡 Best Practices"):
        st.markdown("""
        **Connection Request Tips:**
        - Personalize every message (mention their company, role, or recent post)
        - Keep it short (300 characters max)
        - Don't pitch immediately - focus on value
        - Use their first name
        
        **Messaging Tips:**
        - Wait 24 hours after connection before sending initial message
        - Always provide value first
        - Use questions to engage
        - Keep messages conversational, not salesy
        - Space out follow-ups (don't be pushy)
        
        **Tracking Tips:**
        - Update your database daily
        - Set calendar reminders for follow-ups
        - Note any personal details for future conversations
        - Track what messaging works best
        - Adjust templates based on response rates
        """)
    
    with st.expander("⚠️ LinkedIn Limits & Safety"):
        st.markdown("""
        **LinkedIn Connection Limits:**
        - Free account: ~100 requests per week
        - Premium/Sales Navigator: ~200-400 requests per week
        - Daily limit: 40-50 connection requests (stay at 40 to be safe)
        - Withdraw pending requests after 2 weeks
        
        **Avoid Getting Flagged:**
        - Don't copy-paste identical messages
        - Vary your connection request messages
        - Don't send too many requests in a short burst
        - Maintain a good acceptance rate (aim for 30%+)
        - Respond to messages from your connections
        - Engage with content (like, comment) to appear authentic
        
        **Warning Signs:**
        - If LinkedIn warns about connection limits, stop for 24 hours
        - If acceptance rate drops below 20%, improve targeting/messaging
        - If you get "We couldn't send your invitation" errors, take a break
        """)
    
    with st.expander("📊 Success Metrics to Track"):
        st.markdown("""
        **Key Performance Indicators:**
        - **Connection Acceptance Rate:** Target 30-40%
        - **Message Response Rate:** Target 15-25%
        - **Interest Rate:** Target 10-20% of messaged leads
        - **Link Click Rate:** Track in your analytics
        - **Conversion Rate:** Target 5-15% of interested leads
        
        **Weekly Goals:**
        - Week 1: Focus on volume (280 connections sent)
        - Week 2: Optimize messaging based on response rates
        - Week 3: Refine targeting and follow-up sequence
        - Week 4: Scale what's working, hit 1,200 total connections
        
        **What Success Looks Like After 30 Days:**
        - 1,200 connection requests sent
        - 360-480 connections accepted (30-40% rate)
        - 54-120 interested leads (15-25% of accepted)
        - 10-30 conversions (download checklist + engaged)
        """)
    
    st.markdown("---")
    
    st.markdown("### 📥 Sample CSV Templates")
    
    st.markdown("#### Daily Tracker CSV Template")
    sample_daily = pd.DataFrame({
        'Day': list(range(1, 31)),
        'Date': [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)],
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
    
    csv_sample_daily = io.StringIO()
    sample_daily.to_csv(csv_sample_daily, index=False)
    st.download_button(
        label="📥 Download Daily Tracker Template",
        data=csv_sample_daily.getvalue(),
        file_name="daily_tracker_template.csv",
        mime="text/csv"
    )
    
    st.markdown("#### Leads Database CSV Template")
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
        mime="text/csv"
    )
    
    st.markdown("---")
    
    st.markdown("### 🚀 Getting Started Checklist")
    st.markdown("""
    - [ ] Set up your LinkedIn profile professionally (clear photo, compelling headline)
    - [ ] Prepare your AI Systems Checklist and landing page
    - [ ] Create tracking system (this app!)
    - [ ] Develop your target list (who to connect with)
    - [ ] Customize message templates with your personal voice
    - [ ] Set daily calendar reminders for outreach blocks
    - [ ] Commit to 30 days of consistent action
    - [ ] Start with Day 1: Send your first 40 connection requests!
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><b>🔥 30-Day LinkedIn Outreach Challenge 🔥</b></p>
    <p>Consistency is key! Show up every day and the results will follow.</p>
    <p style='font-size: 0.9em;'>💡 Pro Tip: Block out 1-2 hours daily for LinkedIn outreach. Make it a non-negotiable habit!</p>
</div>
""", unsafe_allow_html=True)
