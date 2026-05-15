import streamlit as st
import random
from supabase import create_client, Client

# --- SETUP ---
st.set_page_config(page_title="VeshGarage Tycoon", page_icon="🏎️", layout="wide")

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- GAME DATA ---
CARS = {
    "Honda Civic": {"price": 5000, "income": 50},
    "Toyota Supra": {"price": 25000, "income": 400},
    "Nissan GTR": {"price": 80000, "income": 1500},
    "Lamborghini Huracan": {"price": 250000, "income": 6000},
    "Bugatti Chiron": {"price": 1000000, "income": 30000},
}

# --- DATABASE FUNCTIONS ---
def get_player(email):
    res = supabase.table("players").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None

def create_player(email, username):
    player = {"email": email, "username": username, "cash": 10000, "garage": []}
    supabase.table("players").insert(player).execute()
    return player

def update_player(email, data):
    supabase.table("players").update(data).eq("email", email).execute()

# --- LOGIN CHECK ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- AUTO LOGIN AFTER MAGIC LINK ---
if st.session_state.user is None:
    session = supabase.auth.get_session()
    if session and session.user:
        st.session_state.user = session.user
        st.rerun()

# --- MAIN APP ---
if st.session_state.user:
    # --- LOGGED IN: SHOW GAME ---
    user_email = st.session_state.user.email
    player = get_player(user_email)

    if not player:
        player = create_player(user_email, st.session_state.user.user_metadata.get("username", "Player"))

    # --- SIDEBAR ---
    st.sidebar.title(f"🏁 {player['username']}'s Garage")
    st.sidebar.metric("💰 Cash", f"${player['cash']:,}")
    st.sidebar.write(f"**Email:** {user_email}")
    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    # --- GAME TABS ---
    tab1, tab2, tab3 = st.tabs(["🏠 Garage", "🛒 Dealership", "🏁 Race"])

    with tab1:
        st.header("Your Garage")
        if player['garage']:
            total_income = 0
            for car_name in player['garage']:
                income = CARS[car_name]['income']
                total_income += income
                st.write(f"**{car_name}** - Earns ${income}/hr")
            st.success(f"Total Passive Income: ${total_income}/hr")
        else:
            st.info("Your garage is empty. Buy a car from the Dealership!")

    with tab2:
        st.header("Dealership")
        for car_name, data in CARS.items():
            col1, col2, col3 = st.columns([2,1,1])
            col1.write(f"**{car_name}**")
            col2.write(f"${data['price']:,}")
            if col3.button("Buy", key=car_name):
                if player['cash'] >= data['price']:
                    new_cash = player['cash'] - data['price']
                    new_garage = player['garage'] + [car_name]
                    update_player(user_email, {"cash": new_cash, "garage": new_garage})
                    st.success(f"You bought a {car_name}!")
                    st.rerun()
                else:
                    st.error("Not enough cash!")

    with tab3:
        st.header("Street Race")
        if player['garage']:
            if st.button("Start Race", type="primary"):
                if random.random() > 0.5:
                    winnings = random.randint(500, 5000)
                    new_cash = player['cash'] + winnings
                    update_player(user_email, {"cash": new_cash})
                    st.balloons()
                    st.success(f"You won the race! +${winnings}")
                    st.rerun()
                else:
                    st.error("You lost! Better luck next time.")
        else:
            st.warning("You need a car to race. Buy one first!")

else:
    # --- LOGIN SCREEN: Email Magic Link ---
    st.title("🏎️ VeshGarage Tycoon")
    st.subheader("Build your car empire")

    email = st.text_input("Email", placeholder="enzo@garage.com")
    username = st.text_input("CEO Name", placeholder="Enzo", key="username_input")

    if st.button("Send Magic Link", type="primary", use_container_width=True):
        if email and username:
            try:
                supabase.auth.sign_in_with_otp({
                    "email": email,
                    "options": {
                        "data": {"username": username},
                        "email_redirect_to": "https://veshgarage-uokcxr1bytjdq4s7x4tgbvg.streamlit.app"
                    }
                })
                st.success(f"Magic link sent to {email}!")
                st.info("**For testing:** Go to Supabase → Authentication → Users → Click 3 dots → Generate confirmation link → Open link")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Enter email and CEO name")
