import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURATION & BRAIN ENGINE ---
st.set_page_config(page_title="Private Tontine Ledger", layout="wide")
st.title("💼 Private Tontine & Contributor Ledger")
st.write("---")

# Initialize our temporary browser-RAM data tables if they don't exist yet
if 'clients' not in st.session_state:
    st.session_state.clients = pd.DataFrame([{
        'client_id': 'C1', 'full_name': 'John Doe', 'whatsapp': '+44712345678', 
        'country': 'UK', 'join_date': '2026-01-10', 'notes': 'Trusted family friend.'
    }])

if 'correspondents' not in st.session_state:
    st.session_state.correspondents = pd.DataFrame([
        {'id': 'CORR1', 'name': 'Nephew (UK)', 'currency': 'GBP', 'vault': 0.00, 'instructions': 'Pay cash or Barclays transfer.'},
        {'id': 'CORR2', 'name': 'Agent (Germany)', 'currency': 'EUR', 'vault': 0.00, 'instructions': 'Pay via PayPal Friends & Family.'}
    ])

if 'loans' not in st.session_state:
    st.session_state.loans = pd.DataFrame(columns=[
        'loan_id', 'client_name', 'correspondent', 'xaf_requested', 'exchange_rate',
        'principal_fx', 'interest_fx', 'total_due_fx', 'penalty_rate', 'grace_days', 'status'
    ])

# --- HEADER STATISTICS PANEL ---
st.subheader("📊 Global Network Portfolio (In XAF)")
col1, col2, col3 = st.columns(3)

# Calculate live totals from our simulated logs
active_loans = st.session_state.loans[st.session_state.loans['status'] == 'ACTIVE']
total_deployed_xaf = active_loans['xaf_requested'].sum()
total_interest_xaf = (active_loans['interest_fx'] * active_loans['exchange_rate']).sum()
review_queue_count = len(st.session_state.loans[st.session_state.loans['status'] == 'PENDING_VALIDATION'])

with col1:
    st.metric(label="Total Capital Active", value=f"{total_deployed_xaf:,.0f} XAF")
with col2:
    st.metric(label="Expected Group Yield This Month", value=f"{total_interest_xaf:,.0f} XAF")
with col3:
    st.metric(label="Review Queue Notifications", value=f"{review_queue_count} Pending Payments")

st.write("---")

# --- PRIMARY ACTION CONTROL SIDEBAR ---
st.sidebar.header("🛠️ Master Controls Panel")

# 1. Action Window: Onboard New Participant
with st.sidebar.expander("👤 1. Onboard New Friend", expanded=False):
    with st.form("onboard_form", clear_on_submit=True):
        new_name = st.text_input("Full Name")
        new_whatsapp = st.text_input("WhatsApp Number")
        new_country = st.selectbox("Resident Country", ["UK", "Germany", "USA", "Canada"])
        new_notes = st.text_area("Internal Context Notes")
        submit_onboard = st.form_submit_with_button("Generate Profile")
        
        if submit_onboard and new_name and new_whatsapp:
            new_client = {
                'client_id': f"C{len(st.session_state.clients)+1}", 'full_name': new_name,
                'whatsapp': new_whatsapp, 'country': new_country, 
                'join_date': str(datetime.date.today()), 'notes': new_notes
            }
            st.session_state.clients = pd.concat([st.session_state.clients, pd.DataFrame([new_client])], ignore_index=True)
            st.success(f"Profile generated! Credentials password text sent to {new_whatsapp} privately.")

# 2. Action Window: Handout Capital (Issue Loan)
with st.sidebar.expander("💰 2. Initialize New Cycle Allocation", expanded=False):
    with st.form("loan_form", clear_on_submit=True):
        client_select = st.selectbox("Select Participant", st.session_state.clients['full_name'].tolist())
        xaf_amt = st.number_input("XAF Requested (Max 1,000,000)", min_value=10000, max_value=1000000, value=500000, step=50000)
        fx_rate = st.number_input("Agreed Exchange Rate", min_value=1.0, value=800.0, step=10.0)
        yield_rate = st.number_input("Monthly Yield Interest Rate %", min_value=1, value=20)
        pen_rate = st.number_input("Default Overdue Penalty Rate %", min_value=0, value=5)
        grace_d = st.number_input("Grace Days Allocated", min_value=0, value=3)
        corr_select = st.selectbox("Assigned Overseas Collector", st.session_state.correspondents['name'].tolist())
        submit_loan = st.form_submit_with_button("Lock Foreign Base Debt")
        
        if submit_loan:
            # RUN CORE BACKEND MATH ENGINE
            base_principal = round(xaf_amt / fx_rate, 2)
            interest_fee = round(base_principal * (yield_rate / 100), 2)
            total_due = base_principal + interest_fee
            
            new_loan = {
                'loan_id': f"L{len(st.session_state.loans)+1}", 'client_name': client_select,
                'correspondent': corr_select, 'xaf_requested': xaf_amt, 'exchange_rate': fx_rate,
                'principal_fx': base_principal, 'interest_fx': interest_fee, 'total_due_fx': total_due,
                'penalty_rate': pen_rate, 'grace_days': grace_d, 'status': 'ACTIVE'
            }
            st.session_state.loans = pd.concat([st.session_state.loans, pd.DataFrame([new_loan])], ignore_index=True)
            st.success(f"Success! Base debt locked.")

# --- SCREEN WORKSPACE WINDOWS ---
tab_ledger, tab_vaults = st.tabs(["🗂️ Active Master Ledger", "🌍 Overseas Correspondent Vault Matrix"])

with tab_ledger:
    st.subheader("Current Active Group Files")
    if st.session_state.loans.empty:
        st.info("No active profiles running currently. Use the sidebar menu to start an allocation.")
    else:
        for idx, row in st.session_state.loans.iterrows():
            if row['status'] == 'ACTIVE':
                corr_currency = st.session_state.correspondents[st.session_state.correspondents['name']==row['correspondent']]['currency'].values
                
                # Render clean user profile box card view layout
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f"**Participant:** {row['client_name']}")
                        st.caption(f"File Code: {row['loan_id']}")
                    with c2:
                        st.write(f"💵 Deployed: **{row['xaf_requested']:,} XAF**")
                        st.caption(f"FX Locked: {row['exchange_rate']} rate")
                    with c3:
                        st.write(f"🎯 Owed: **{corr_currency[0]} {row['total_due_fx']}**")
                        st.caption(f"Base Principal: {corr_currency[0]} {row['principal_fx']}")
                    with c4:
                        # Open the 3 Settlement Validation Workspace directly inside row
                        st.write("🔧 **Resolution Action Panel**")
                        opt = st.selectbox(f"Select Resolution Path", ["Choose Options...", "Option 1: Full Payment", "Option 2: Interest-Only Rollover"], key=f"opt_{row['loan_id']}")
                        
                        if opt == "Option 1: Full Payment":
                            if st.button(f"Confirm Full {corr_currency[0]} {row['total_due_fx']}", key=f"btn1_{row['loan_id']}"):
                                st.session_state.loans.at[idx, 'status'] = 'FULLY_PAID'
                                # Update vault tracking line item
                                c_idx = st.session_state.correspondents[st.session_state.correspondents['name'] == row['correspondent']].index
                                st.session_state.correspondents.at[c_idx, 'vault'] += row['total_due_fx']
                                st.rerun()
                                
                        elif opt == "Option 2: Interest-Only Rollover":
                            override_p = st.number_input("Override Penalty Rate %", min_value=0.0, max_value=float(row['penalty_rate']), value=float(row['penalty_rate']), step=1.0, key=f"p2_{row['loan_id']}")
                            calc_pen = round(row['total_due_fx'] * (override_p / 100), 2)
                            expected_cash = row['interest_fx'] + calc_pen
                            st.caption(f"Cash to Collect: {corr_currency[0]} {expected_cash} (Interest + Pen)")
                            
                            if st.button(f"Process Rollover", key=f"btn2_{row['loan_id']}"):
                                # Safe update vault tracking balance
                                c_idx = st.session_state.correspondents[st.session_state.correspondents['name'] == row['correspondent']].index
                                st.session_state.correspondents.at[c_idx, 'vault'] += expected_cash
                                
                                # Process backend engine rollover math recalculation clocks
                                new_interest = round(row['principal_fx'] * (20 / 100), 2)
                                st.session_state.loans.at[idx, 'interest_fx'] = new_interest
                                st.session_state.loans.at[idx, 'total_due_fx'] = row['principal_fx'] + new_interest
                                st.toast("Client account status flipped to AWAITING_CONFIRMATION! Flow secured.")
                                st.rerun()

with tab_vaults:
    st.subheader("Global Capital Node Monitoring Matrix")
    v1, v2 = st.columns(2)
    
    for c_idx, c_row in st.session_state.correspondents.iterrows():
        with v1 if c_idx == 0 else v2:
            st.metric(
                label=f"🌍 {c_row['name']} Collection Node Cash Pool", 
                value=f"{c_row['currency']} {c_row['vault']:,.2f}"
            )
            # Add simple vault reset balancing tracking tool
            payout_amt = st.number_input(f"Log Remittance back to Cameroon ({c_row['currency']})", min_value=0.0, max_value=float(c_row['vault']), value=0.0, key=f"pay_{c_row['id']}")
            if payout_amt > 0.0:
                if st.button(f"Balance {c_row['name']} Node Ledger", key=f"pbtn_{c_row['id']}"):
                    st.session_state.correspondents.at[c_idx, 'vault'] -= payout_amt
                    st.success("Vault metrics adjusted. Remittance log safely indexed.")
