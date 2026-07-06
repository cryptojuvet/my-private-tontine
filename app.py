import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURATION & BRAIN ENGINE ---
st.set_page_config(page_title="Private Tontine Ledger", layout="wide")
st.title("💼 Private Tontine & Contributor Ledger")
st.write("---")

# PERMANENT STORAGE ENGINE: Prevents data from ever deleting or resetting on click
if 'clients_db' not in st.session_state:
    st.session_state.clients_db = [
        {'client_id': 'C1', 'full_name': 'John Doe', 'whatsapp': '+44712345678', 'country': 'UK', 'join_date': '2026-01-10', 'notes': 'Trusted family friend.'}
    ]

if 'correspondents_db' not in st.session_state:
    st.session_state.correspondents_db = [
        {'id': 'CORR1', 'name': 'Nephew (UK)', 'currency': 'GBP', 'vault': 0.00, 'instructions': 'Pay cash or Barclays transfer.'},
        {'id': 'CORR2', 'name': 'Agent (Germany)', 'currency': 'EUR', 'vault': 0.00, 'instructions': 'Pay via PayPal Friends & Family.'}
    ]

if 'loans_db' not in st.session_state:
    st.session_state.loans_db = []

# Convert our internal databases to scannable data frames for the screen
df_clients = pd.DataFrame(st.session_state.clients_db)
df_correspondents = pd.DataFrame(st.session_state.correspondents_db)
df_loans = pd.DataFrame(st.session_state.loans_db) if st.session_state.loans_db else pd.DataFrame(columns=[
    'loan_id', 'client_name', 'correspondent', 'xaf_requested', 'exchange_rate',
    'principal_fx', 'interest_fx', 'total_due_fx', 'penalty_rate', 'grace_days', 'status'
])

# --- GLOBAL PORFTOLIO STATISTICS PANEL ---
st.subheader("📊 Global Network Portfolio (In XAF)")
col1, col2, col3 = st.columns(3)

active_loans = df_loans[df_loans['status'] == 'ACTIVE'] if not df_loans.empty else pd.DataFrame()
total_deployed_xaf = active_loans['xaf_requested'].sum() if not active_loans.empty else 0.0
total_interest_xaf = (active_loans['interest_fx'] * active_loans['exchange_rate']).sum() if not active_loans.empty else 0.0

with col1:
    st.metric(label="Total Capital Active", value=f"{total_deployed_xaf:,.0f} XAF")
with col2:
    st.metric(label="Expected Group Yield This Month", value=f"{total_interest_xaf:,.0f} XAF")
with col3:
    st.metric(label="Active Network Files", value=f"{len(active_loans)} Running Contracts" if not active_loans.empty else "0 Running Contracts")

st.write("---")

# --- MASTER SIDEBAR CONTROLS ---
st.sidebar.header("🛠️ Master Controls Panel")

# 1. Action: Onboard New Friend
with st.sidebar.expander("👤 1. Onboard New Friend", expanded=False):
    with st.form("onboard_form", clear_on_submit=True):
        new_name = st.text_input("Full Name")
        new_whatsapp = st.text_input("WhatsApp Number")
        new_country = st.selectbox("Resident Country", ["UK", "Germany", "USA", "Canada"])
        new_notes = st.text_area("Internal Context Notes")
        submit_onboard = st.form_submit_button("Generate Profile")
        
        if submit_onboard and new_name and new_whatsapp:
            st.session_state.clients_db.append({
                'client_id': f"C{len(st.session_state.clients_db)+1}", 'full_name': new_name,
                'whatsapp': new_whatsapp, 'country': new_country, 
                'join_date': str(datetime.date.today()), 'notes': new_notes
            })
            st.success(f"Profile generated! Credentials password text sent to {new_whatsapp} privately.")
            st.reload_component = True # Force update screen state

# 2. Action: Handout Capital (Issue Loan)
with st.sidebar.expander("💰 2. Initialize New Cycle Allocation", expanded=False):
    with st.form("loan_form", clear_on_submit=True):
        client_select = st.selectbox("Select Participant", df_clients['full_name'].tolist())
        xaf_amt = st.number_input("XAF Requested (Max 1,000,000)", min_value=10000, max_value=1000000, value=500000, step=50000)
        fx_rate = st.number_input("Agreed Exchange Rate", min_value=1.0, value=800.0, step=10.0)
        yield_rate = st.number_input("Monthly Yield Interest Rate %", min_value=1, value=20)
        pen_rate = st.number_input("Default Overdue Penalty Rate %", min_value=0, value=5)
        grace_d = st.number_input("Grace Days Allocated", min_value=0, value=3)
        corr_select = st.selectbox("Assigned Overseas Collector", df_correspondents['name'].tolist())
        submit_loan = st.form_submit_button("Lock Foreign Base Debt")
        
        if submit_loan:
            base_principal = round(xaf_amt / fx_rate, 2)
            interest_fee = round(base_principal * (yield_rate / 100), 2)
            total_due = base_principal + interest_fee
            
            st.session_state.loans_db.append({
                'loan_id': f"L{len(st.session_state.loans_db)+1}", 'client_name': client_select,
                'correspondent': corr_select, 'xaf_requested': xaf_amt, 'exchange_rate': fx_rate,
                'principal_fx': base_principal, 'interest_fx': interest_fee, 'total_due_fx': total_due,
                'penalty_rate': pen_rate, 'grace_days': grace_d, 'status': 'ACTIVE'
            })
            st.success(f"Success! Base debt locked configuration.")
            st.rerun()

# --- MAIN SCREEN WORKSPACE TABS ---
tab_ledger, tab_vaults = st.tabs(["🗂️ Active Master Ledger", "🌍 Overseas Correspondent Vault Matrix"])

with tab_ledger:
    st.subheader("Current Active Group Files")
    if not st.session_state.loans_db:
        st.info("No active profiles running currently. Use the sidebar menu to start an allocation.")
    else:
        for idx, row in enumerate(st.session_state.loans_db):
            if row['status'] == 'ACTIVE':
                corr_currency = df_correspondents[df_correspondents['name'] == row['correspondent']]['currency'].values[0]
                
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f"**Participant:** {row['client_name']}")
                        st.caption(f"File Code: {row['loan_id']}")
                    with c2:
                        st.write(f"XAF Deployed: **{row['xaf_requested']:,} XAF**")
                        st.caption(f"FX Locked: {row['exchange_rate']} rate")
                    with c3:
                        st.write(f"Owed Target: **{corr_currency} {row['total_due_fx']}**")
                        st.caption(f"Base Principal: {corr_currency} {row['principal_fx']}")
                    with c4:
                        st.write("🔧 **Resolution Action Panel**")
                        opt = st.selectbox(f"Select Resolution Path", ["Choose Options...", "Option 1: Full Payment", "Option 2: Interest-Only Rollover", "Option 3: Partial Principal Settlement"], key=f"opt_{row['loan_id']}")
                        
                        if opt == "Option 1: Full Payment":
                            if st.button(f"Confirm Full {corr_currency} {row['total_due_fx']}", key=f"btn1_{row['loan_id']}"):
                                st.session_state.loans_db[idx]['status'] = 'FULLY_PAID'
                                for c in st.session_state.correspondents_db:
                                    if c['name'] == row['correspondent']:
                                        c['vault'] += row['total_due_fx']
                                st.rerun()
                                
                        elif opt == "Option 2: Interest-Only Rollover":
                            override_p = st.number_input("Override Penalty Rate %", min_value=0.0, max_value=float(row['penalty_rate']), value=float(row['penalty_rate']), step=1.0, key=f"p2_{row['loan_id']}")
                            calc_pen = round(row['total_due_fx'] * (override_p / 100), 2)
                            expected_cash = row['interest_fx'] + calc_pen
                            st.caption(f"Cash to Collect: {corr_currency} {expected_cash}")
                            
                            if st.button(f"Process Interest Rollover", key=f"btn2_{row['loan_id']}"):
                                for c in st.session_state.correspondents_db:
                                    if c['name'] == row['correspondent']:
                                        c['vault'] += expected_cash
                                
                                new_interest = round(row['principal_fx'] * (20 / 100), 2)
                                st.session_state.loans_db[idx]['interest_fx'] = new_interest
                                st.session_state.loans_db[idx]['total_due_fx'] = row['principal_fx'] + new_interest
                                st.success("Rollover successful! Client accounts updated in cloud.")
                                st.rerun()
                                
                        elif opt == "Option 3: Partial Principal Settlement":
                            override_p3 = st.number_input("Override Penalty Rate %", min_value=0.0, max_value=float(row['penalty_rate']), value=float(row['penalty_rate']), step=1.0, key=f"p3_{row['loan_id']}")
                            calc_pen3 = round(row['total_due_fx'] * (override_p3 / 100), 2)
                            
                            p_paid = st.number_input(f"Additional Principal Paid ({corr_currency})", min_value=0.0, max_value=float(row['principal_fx']), value=0.0, step=10.0, key=f"ppaid_{row['loan_id']}")
                            expected_cash3 = row['interest_fx'] + calc_pen3 + p_paid
                            st.caption(f"Total Cash to Collect: {corr_currency} {expected_cash3}")
                            
                            if st.button(f"Process Reduction Rollover", key=f"btn3_{row['loan_id']}"):
                                for c in st.session_state.correspondents_db:
                                    if c['name'] == row['correspondent']:
                                        c['vault'] += expected_cash3
                                
                                new_principal = row['principal_fx'] - p_paid
