from flask import Flask, render_template_string, request, redirect, url_for, session
from app.ui.core.calculators.calculator import MoneyCalculator
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import re
from datetime import datetime

# =========================================================
# RS TRADER MONEY MANAGEMENT SYSTEM
# FINAL PUBLIC WEB VERSION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "RS_TRADER_SECRET",
    "RS-Trader-Local-Secret-2026-Change-This"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "rs_trader_auth.db")

# =========================================================
# BRAND / SUPPORT
# =========================================================

TELEGRAM_USERNAME = "@RSTrader087"
TELEGRAM_URL = "https://t.me/RSTrader087"

# =========================================================
# PAYMENT METHODS
# DEMO DETAILS FOR NOW
# =========================================================

PAYMENT_METHODS = {

    "bkash": {
        "name": "bKash",
        "label": "Demo bKash Number",
        "account": "01XXXXXXXXX",
        "amount": "৳100",
        "note": "DEMO ONLY — Real bKash number will be added later."
    },

    "nagad": {
        "name": "Nagad",
        "label": "Demo Nagad Number",
        "account": "01XXXXXXXXX",
        "amount": "৳100",
        "note": "DEMO ONLY — Real Nagad number will be added later."
    },

    "binance": {
        "name": "Binance",
        "label": "Demo Binance ID",
        "account": "DEMO-BINANCE-ID-2026",
        "amount": "$1",
        "note": "DEMO ONLY — Real Binance ID will be added later."
    }

}

# =========================================================
# ACTIVATION CODES
# =========================================================

SECRET_CODES = [
    "RS-7K9M-X2Q8-P4ZT",
    "RS-3N6V-H8Q2-W5YK",
    "RS-9P4X-T7LM-C2RA",
    "RS-6Q8Z-M3VK-Y7NP",
    "RS-2H5K-R9XD-F6TW",
]

# =========================================================
# CALCULATOR
# =========================================================

calculator = MoneyCalculator(
    starting_capital=114,
    payout=85,
    profit_target_percent=5,
    stop_loss_percent=7.5,
    max_loss_streak=3,
    planned_wins=5,
    base_risk_percent=1,
)

# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    # USERS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            activation_code TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ACTIVATION CODES
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            used INTEGER DEFAULT 0,
            owner_username TEXT
        )
    """)

    # PAYMENT REQUESTS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payment_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            method TEXT NOT NULL,
            account TEXT NOT NULL,
            amount TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Existing database upgrade
    activation_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(activation_codes)"
        ).fetchall()
    ]

    if "owner_username" not in activation_columns:
        conn.execute(
            """
            ALTER TABLE activation_codes
            ADD COLUMN owner_username TEXT
            """
        )

    # Insert activation codes
    for code in SECRET_CODES:

        conn.execute(
            """
            INSERT OR IGNORE INTO activation_codes
            (code, used, owner_username)
            VALUES (?, 0, NULL)
            """,
            (code,)
        )

    conn.commit()
    conn.close()


init_db()

# =========================================================
# HELPERS
# =========================================================

def login_required():

    return (
        session.get("logged_in", False)
        and
        session.get("activated", False)
    )


def valid_username(username):

    return (
        3 <= len(username) <= 30
        and
        re.fullmatch(
            r"[A-Za-z0-9_.-]+",
            username
        ) is not None
    )


def valid_password(password):

    return len(password) >= 6


def get_auth_context():

    return {
        "telegram_username": TELEGRAM_USERNAME,
        "telegram_url": TELEGRAM_URL,
    }


# =========================================================
# SVG ICONS
# =========================================================

TELEGRAM_SVG = """
<svg viewBox="0 0 48 48"
     xmlns="http://www.w3.org/2000/svg">

    <circle
        cx="24"
        cy="24"
        r="24"
        fill="#229ED9"
    />

    <path
        d="M36.9 11.9 30.5 37c-.5 1.8-1.6 2.2-3.2 1.4l-8.9-6.6-4.3 4.1c-.5.5-.9.9-1.8.9l.6-9.1 16.6-15c.7-.6-.2-.9-1.1-.3L8 25.1l-8.6-2.7c-1.9-.6-1.9-1.9.4-2.8L33.5 7.5c1.6-.6 3.1.4 2.5 4.4l.9 0z"
        fill="white"
        transform="translate(6 2) scale(.75)"
    />

</svg>
"""

BKASH_SVG = """
<svg viewBox="0 0 48 48"
     xmlns="http://www.w3.org/2000/svg">

    <circle
        cx="24"
        cy="24"
        r="24"
        fill="#E2136E"
    />

    <text
        x="24"
        y="31"
        text-anchor="middle"
        font-family="Arial,sans-serif"
        font-size="18"
        font-weight="900"
        fill="white"
    >b</text>

</svg>
"""

NAGAD_SVG = """
<svg viewBox="0 0 48 48"
     xmlns="http://www.w3.org/2000/svg">

    <circle
        cx="24"
        cy="24"
        r="24"
        fill="#F7941D"
    />

    <text
        x="24"
        y="31"
        text-anchor="middle"
        font-family="Arial,sans-serif"
        font-size="19"
        font-weight="900"
        fill="white"
    >N</text>

</svg>
"""

BINANCE_SVG = """
<svg viewBox="0 0 48 48"
     xmlns="http://www.w3.org/2000/svg">

    <circle
        cx="24"
        cy="24"
        r="24"
        fill="#F3BA2F"
    />

    <g fill="white">

        <path d="M24 8 29.4 13.4 24 18.8 18.6 13.4z"/>

        <path d="M15 17 20.4 22.4 15 27.8 9.6 22.4z"/>

        <path d="M33 17 38.4 22.4 33 27.8 27.6 22.4z"/>

        <path d="M24 26 29.4 31.4 24 36.8 18.6 31.4z"/>

        <path d="M24 20 27.7 23.7 24 27.4 20.3 23.7z"/>

    </g>

</svg>
"""

LOCK_SVG = """
<svg viewBox="0 0 48 48"
     xmlns="http://www.w3.org/2000/svg">

    <rect
        x="10"
        y="20"
        width="28"
        height="20"
        rx="5"
        fill="currentColor"
    />

    <path
        d="M16 20v-6a8 8 0 0 1 16 0v6"
        fill="none"
        stroke="currentColor"
        stroke-width="4"
        stroke-linecap="round"
    />

</svg>
"""

CHECK_SVG = """
<svg viewBox="0 0 64 64"
     xmlns="http://www.w3.org/2000/svg">

    <circle
        cx="32"
        cy="32"
        r="30"
        fill="currentColor"
    />

    <path
        d="M18 33.5 27 42l19-21"
        fill="none"
        stroke="white"
        stroke-width="6"
        stroke-linecap="round"
        stroke-linejoin="round"
    />

</svg>
"""

# =========================================================
# AUTH CSS
# =========================================================

AUTH_CSS = """

*{
    box-sizing:border-box;
}

body{
    margin:0;
    min-height:100vh;

    display:flex;
    align-items:center;
    justify-content:center;

    padding:20px 12px;

    background:
        radial-gradient(
            circle at 15% 10%,
            rgba(37,99,235,.17),
            transparent 32%
        ),
        radial-gradient(
            circle at 85% 85%,
            rgba(124,58,237,.15),
            transparent 30%
        ),
        #050811;

    color:#f8fafc;

    font-family:
        Inter,
        Arial,
        sans-serif;
}

.auth-wrapper{
    width:min(500px,94%);
}

.brand{
    text-align:center;
    margin-bottom:22px;
}

.logo{
    width:62px;
    height:62px;

    margin:auto;

    display:flex;
    align-items:center;
    justify-content:center;

    border-radius:18px;

    font-size:22px;
    font-weight:950;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #7c3aed
        );

    box-shadow:
        0 15px 45px
        rgba(37,99,235,.30);
}

.brand h1{
    margin:14px 0 4px;

    font-size:26px;
    letter-spacing:-.6px;
}

.brand p{
    margin:0;

    color:#64748b;

    font-size:9px;

    letter-spacing:1.3px;

    text-transform:uppercase;
}

.card{
    padding:30px;

    background:
        linear-gradient(
            145deg,
            rgba(15,23,42,.98),
            rgba(8,13,24,.99)
        );

    border:
        1px solid
        rgba(148,163,184,.12);

    border-radius:22px;

    box-shadow:
        0 25px 70px
        rgba(0,0,0,.45);
}

.card-icon{
    width:49px;
    height:49px;

    display:flex;
    align-items:center;
    justify-content:center;

    margin-bottom:16px;

    border-radius:13px;

    color:#60a5fa;

    background:
        rgba(59,130,246,.08);

    border:
        1px solid
        rgba(59,130,246,.16);

    font-size:19px;
}

h2{
    margin:0;

    font-size:20px;
}

.subtitle{
    margin:
        7px 0 22px;

    color:#64748b;

    font-size:10px;

    line-height:1.65;
}

.field{
    margin-bottom:15px;
}

label{
    display:block;

    margin-bottom:7px;

    color:#94a3b8;

    font-size:9px;

    font-weight:800;

    letter-spacing:.8px;

    text-transform:uppercase;
}

.input{
    width:100%;

    height:48px;

    padding:0 13px;

    background:#060b14;

    color:#fff;

    border:
        1px solid
        #263449;

    border-radius:10px;

    outline:none;

    font-size:13px;

    transition:.2s;
}

.input:focus{
    border-color:#3b82f6;

    box-shadow:
        0 0 0 3px
        rgba(59,130,246,.09);
}

.main-button{
    width:100%;

    min-height:49px;

    margin-top:5px;

    border:0;

    border-radius:11px;

    color:#fff;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #4f46e5
        );

    font-size:12px;

    font-weight:900;

    letter-spacing:.35px;

    cursor:pointer;

    transition:.18s;
}

.main-button:hover{
    filter:brightness(1.08);

    transform:
        translateY(-1px);
}

.error{
    margin-bottom:16px;

    padding:11px 12px;

    border-radius:9px;

    color:#fca5a5;

    background:
        rgba(239,68,68,.08);

    border:
        1px solid
        rgba(239,68,68,.20);

    font-size:10px;

    line-height:1.5;
}

.success{
    margin-bottom:16px;

    padding:11px 12px;

    border-radius:9px;

    color:#86efac;

    background:
        rgba(34,197,94,.08);

    border:
        1px solid
        rgba(34,197,94,.20);

    font-size:10px;

    line-height:1.5;
}

.links{
    display:flex;

    justify-content:space-between;

    align-items:center;

    gap:10px;

    margin-top:18px;
}

.links a{
    color:#64748b;

    text-decoration:none;

    font-size:10px;

    font-weight:800;

    transition:.18s;
}

.links a:hover{
    color:#60a5fa;
}

.create-account-link{
    color:#93c5fd !important;

    font-size:15px !important;

    font-weight:950 !important;
}

.support-box{
    display:flex;

    align-items:center;

    gap:12px;

    margin-top:20px;

    padding:14px;

    border-radius:15px;

    background:
        linear-gradient(
            135deg,
            rgba(34,158,217,.12),
            rgba(37,99,235,.06)
        );

    border:
        1px solid
        rgba(34,158,217,.23);

    text-decoration:none;

    transition:.2s;
}

.support-box:hover{
    transform:
        translateY(-1px);

    border-color:
        rgba(34,158,217,.40);
}

.telegram-icon{
    width:46px;
    height:46px;

    flex:0 0 46px;
}

.telegram-icon svg{
    width:100%;
    height:100%;
}

.support-title{
    display:block;

    color:#e2e8f0;

    font-size:13px;

    font-weight:900;
}

.support-user{
    display:block;

    margin-top:3px;

    color:#8fd5f7;

    font-size:11px;

    font-weight:800;
}

.security{
    margin-top:20px;

    padding-top:16px;

    border-top:
        1px solid
        rgba(148,163,184,.08);

    text-align:center;

    color:#475569;

    font-size:9px;

    line-height:1.5;
}

.footer{
    text-align:center;

    margin-top:18px;

    color:#334155;

    font-size:8px;

    letter-spacing:1px;
}

@media(max-width:520px){

    .auth-wrapper{
        width:96%;
    }

    .card{
        padding:23px 18px;

        border-radius:19px;
    }

    .links{
        flex-direction:column;

        align-items:center;
    }

    .create-account-link{
        font-size:15px !important;
    }

}

"""

# =========================================================
# LOGIN HTML
# =========================================================

LOGIN_HTML = """

<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>RS Trader • Sign In</title>

<style>
""" + AUTH_CSS + """
</style>

</head>

<body>

<div class="auth-wrapper">

<div class="brand">

<div class="logo">
RS
</div>

<h1>
RS Trader
</h1>

<p>
Professional Trading System
</p>

</div>


<div class="card">


<div class="card-icon">
◈
</div>


<h2>
Welcome Back
</h2>


<div class="subtitle">
Sign in to securely access your trading dashboard.
</div>


{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}


{% if success %}

<div class="success">
{{ success }}
</div>

{% endif %}


<form method="POST">


<div class="field">

<label>
Username
</label>

<input
    class="input"
    type="text"
    name="username"
    placeholder="Enter your username"
    autocomplete="username"
    required
>

</div>


<div class="field">

<label>
Password
</label>

<input
    class="input"
    type="password"
    name="password"
    placeholder="Enter your password"
    autocomplete="current-password"
    required
>

</div>


<button
    class="main-button"
    type="submit"
>
SIGN IN
</button>


</form>


<div class="links">


<a
    href="/register"
    class="create-account-link"
>
CREATE ACCOUNT
</a>


<a href="/forgot-password">
FORGOT PASSWORD?
</a>


</div>


<a
    class="support-box"
    href="{{ telegram_url }}"
    target="_blank"
    rel="noopener noreferrer"
>


<span class="telegram-icon">
{{ telegram_svg|safe }}
</span>


<span>

<span class="support-title">
Can't create an account?
</span>

<span class="support-user">
Contact {{ telegram_username }}
</span>

</span>


</a>


<div class="security">
🔒 Secure RS Trader Access
</div>


</div>


<div class="footer">
RS TRADER • MONEY MANAGEMENT
</div>


</div>

</body>

</html>

"""

# =========================================================
# REGISTER HTML
# =========================================================

REGISTER_HTML = """

<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>RS Trader • Create Account</title>

<style>
""" + AUTH_CSS + """
</style>

</head>

<body>

<div class="auth-wrapper">


<div class="brand">

<div class="logo">
RS
</div>

<h1>
RS Trader
</h1>

<p>
Create Your Account
</p>

</div>


<div class="card">


<div class="card-icon">
+
</div>


<h2>
Create Account
</h2>


<div class="subtitle">
Create your RS Trader account and continue to activation.
</div>


{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}


<form method="POST">


<div class="field">

<label>
Username
</label>

<input
    class="input"
    type="text"
    name="username"
    placeholder="Choose a username"
    maxlength="30"
    autocomplete="username"
    required
>

</div>


<div class="field">

<label>
Password
</label>

<input
    class="input"
    type="password"
    name="password"
    placeholder="Create a password"
    autocomplete="new-password"
    required
>

</div>


<div class="field">

<label>
Confirm Password
</label>

<input
    class="input"
    type="password"
    name="confirm_password"
    placeholder="Confirm your password"
    autocomplete="new-password"
    required
>

</div>


<button
    class="main-button"
    type="submit"
>
CREATE ACCOUNT
</button>


</form>


<div class="links"
     style="justify-content:center;">

<a
    href="/login"
    class="create-account-link"
>
← BACK TO LOGIN
</a>

</div>


<a
    class="support-box"
    href="{{ telegram_url }}"
    target="_blank"
    rel="noopener noreferrer"
>


<span class="telegram-icon">
{{ telegram_svg|safe }}
</span>


<span>

<span class="support-title">
Need help creating an account?
</span>

<span class="support-user">
Contact {{ telegram_username }}
</span>

</span>


</a>


<div class="security">
Password must contain at least 6 characters.
</div>


</div>


<div class="footer">
RS TRADER • SECURE ACCOUNT
</div>


</div>

</body>

</html>

"""

# =========================================================
# ACTIVATION HTML
# =========================================================

ACTIVATE_HTML = """

<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>RS Trader • Activate Account</title>

<style>

*{
    box-sizing:border-box;
}

body{

    margin:0;

    min-height:100vh;

    padding:
        20px 12px 35px;

    color:#f8fafc;

    font-family:
        Inter,
        Arial,
        sans-serif;

    background:

        radial-gradient(
            circle at 10% 5%,
            rgba(37,99,235,.16),
            transparent 28%
        ),

        radial-gradient(
            circle at 90% 90%,
            rgba(124,58,237,.13),
            transparent 30%
        ),

        #050811;
}

.container{

    width:min(
        100%,
        800px
    );

    margin:auto;
}

.brand{

    text-align:center;

    margin-bottom:20px;
}

.logo{

    width:60px;
    height:60px;

    margin:auto;

    display:flex;

    align-items:center;
    justify-content:center;

    border-radius:18px;

    font-size:21px;
    font-weight:950;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #7c3aed
        );

    box-shadow:
        0 15px 42px
        rgba(37,99,235,.30);
}

.brand h1{

    margin:
        13px 0 4px;

    font-size:25px;
}

.brand p{

    margin:0;

    color:#64748b;

    font-size:9px;

    text-transform:uppercase;

    letter-spacing:1.2px;
}

.card{

    padding:25px;

    border-radius:24px;

    background:
        linear-gradient(
            145deg,
            rgba(15,23,42,.98),
            rgba(8,13,24,.99)
        );

    border:
        1px solid
        rgba(148,163,184,.11);

    box-shadow:
        0 25px 75px
        rgba(0,0,0,.43);
}

.hero{

    display:flex;

    align-items:center;

    gap:14px;

    margin-bottom:23px;
}

.hero-icon{

    width:53px;

    height:53px;

    flex:0 0 53px;

    display:flex;

    align-items:center;

    justify-content:center;

    border-radius:15px;

    color:#60a5fa;

    background:
        rgba(59,130,246,.09);

    border:
        1px solid
        rgba(59,130,246,.17);
}

.hero-icon svg{

    width:30px;
    height:30px;
}

.hero h2{

    margin:0;

    font-size:23px;
}

.hero p{

    margin:
        5px 0 0;

    color:#64748b;

    font-size:11px;

    line-height:1.5;
}

.alert{

    margin-bottom:15px;

    padding:
        11px 12px;

    border-radius:10px;

    color:#fca5a5;

    background:
        rgba(239,68,68,.08);

    border:
        1px solid
        rgba(239,68,68,.20);

    font-size:10px;
}

.section{

    margin-top:21px;
}

.section-title{

    display:flex;

    align-items:center;

    justify-content:space-between;

    gap:10px;

    margin-bottom:10px;
}

.section-title h3{

    margin:0;

    font-size:14px;

    font-weight:900;
}

.section-title span{

    color:#475569;

    font-size:9px;

    font-weight:800;

    letter-spacing:.8px;

    text-transform:uppercase;
}

.code-box{

    padding:15px;

    border-radius:15px;

    background:
        rgba(255,255,255,.025);

    border:
        1px solid
        rgba(255,255,255,.07);
}

.input-label{

    display:block;

    margin-bottom:7px;

    color:#94a3b8;

    font-size:9px;

    font-weight:800;

    text-transform:uppercase;

    letter-spacing:.7px;
}

.code-input{

    width:100%;

    height:50px;

    padding:
        0 13px;

    outline:none;

    border-radius:10px;

    border:
        1px solid
        #263449;

    background:#060b14;

    color:white;

    font-size:13px;

    letter-spacing:.6px;

    text-transform:uppercase;
}

.code-input:focus{

    border-color:#3b82f6;

    box-shadow:
        0 0 0 3px
        rgba(59,130,246,.09);
}

.activate-btn{

    width:100%;

    height:49px;

    margin-top:10px;

    border:0;

    border-radius:11px;

    color:white;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #4f46e5
        );

    font-size:11px;

    font-weight:900;

    cursor:pointer;
}

.payment-grid{

    display:grid;

    grid-template-columns:
        repeat(
            3,
            1fr
        );

    gap:11px;
}

.payment-card{

    width:100%;

    text-align:left;

    padding:14px;

    border-radius:16px;

    border:
        1px solid
        rgba(255,255,255,.07);

    background:
        rgba(255,255,255,.025);

    color:white;

    cursor:pointer;

    transition:.18s;
}

.payment-card:hover{

    transform:
        translateY(-2px);

    border-color:
        rgba(255,255,255,.16);
}

.payment-card.active{

    border-color:
        rgba(96,165,250,.72);

    background:
        rgba(59,130,246,.07);

    box-shadow:
        0 0 0 2px
        rgba(96,165,250,.08);
}

.payment-logo{

    width:46px;
    height:46px;

    margin-bottom:9px;
}

.payment-logo svg{

    width:100%;
    height:100%;
}

.payment-name{

    font-size:13px;

    font-weight:900;
}

.payment-price{

    margin-top:4px;

    color:#86efac;

    font-size:11px;

    font-weight:900;
}

.payment-panel{

    display:none;

    margin-top:12px;

    padding:16px;

    border-radius:17px;

    border:
        1px solid
        rgba(59,130,246,.17);

    background:
        linear-gradient(
            135deg,
            rgba(59,130,246,.07),
            rgba(99,102,241,.04)
        );
}

.payment-panel.show{

    display:block;
}

.payment-head{

    display:flex;

    align-items:center;

    gap:10px;

    margin-bottom:13px;
}

.payment-head-logo{

    width:41px;
    height:41px;
}

.payment-head-logo svg{

    width:100%;
    height:100%;
}

.payment-head strong{

    display:block;

    font-size:14px;
}

.payment-head small{

    display:block;

    margin-top:2px;

    color:#64748b;

    font-size:9px;
}

.amount-box{

    padding:13px;

    margin-bottom:12px;

    border-radius:13px;

    background:
        rgba(34,197,94,.07);

    border:
        1px solid
        rgba(34,197,94,.17);
}

.amount-label{

    display:block;

    color:#64748b;

    font-size:8px;

    font-weight:900;

    text-transform:uppercase;

    letter-spacing:1px;
}

.amount-value{

    display:block;

    margin-top:3px;

    color:#86efac;

    font-size:25px;

    font-weight:950;
}

.demo-label{

    display:block;

    margin-bottom:7px;

    color:#f4c542;

    font-size:8px;

    font-weight:900;

    letter-spacing:1px;
}

.account-box{

    display:flex;

    align-items:center;

    gap:8px;

    padding:11px;

    border-radius:11px;

    background:
        rgba(0,0,0,.15);

    border:
        1px solid
        rgba(255,255,255,.06);
}

.account{

    flex:1;

    overflow:hidden;

    text-overflow:ellipsis;

    white-space:nowrap;

    font-size:13px;

    font-weight:900;
}

.copy-btn{

    padding:
        8px 10px;

    border:0;

    border-radius:8px;

    background:
        rgba(59,130,246,.13);

    color:#bfdbfe;

    font-size:8px;

    font-weight:900;

    cursor:pointer;
}

.payment-note{

    margin-top:7px;

    color:#64748b;

    font-size:9px;

    line-height:1.5;
}

.confirm-btn{

    width:100%;

    min-height:50px;

    margin-top:13px;

    border:0;

    border-radius:11px;

    background:
        linear-gradient(
            135deg,
            #22c55e,
            #16a34a
        );

    color:#03120a;

    font-size:11px;

    font-weight:950;

    cursor:pointer;
}

.support{

    display:flex;

    align-items:center;

    gap:12px;

    padding:14px;

    border-radius:16px;

    text-decoration:none;

    border:
        1px solid
        rgba(34,158,217,.20);

    background:
        linear-gradient(
            135deg,
            rgba(34,158,217,.11),
            rgba(37,99,235,.05)
        );

    transition:.18s;
}

.support:hover{

    transform:
        translateY(-2px);

    border-color:
        rgba(34,158,217,.40);
}

.support-logo{

    width:47px;

    height:47px;

    flex:0 0 47px;
}

.support-logo svg{

    width:100%;

    height:100%;
}

.support strong{

    display:block;

    font-size:13px;
}

.support span{

    display:block;

    margin-top:3px;

    color:#8fd5f7;

    font-size:10px;

    font-weight:800;
}

.info{

    margin-top:17px;

    padding:13px;

    border-radius:12px;

    color:#64748b;

    background:
        rgba(255,255,255,.02);

    border:
        1px solid
        rgba(255,255,255,.05);

    font-size:9px;

    line-height:1.6;
}

.footer{

    margin-top:16px;

    text-align:center;

    color:#334155;

    font-size:8px;

    letter-spacing:.8px;
}

@media(max-width:650px){

    .payment-grid{

        grid-template-columns:1fr;
    }

    .card{

        padding:20px 15px;
    }

    .hero h2{

        font-size:21px;
    }

}

</style>

</head>

<body>


<div class="container">


<div class="brand">

<div class="logo">
RS
</div>

<h1>
RS Trader
</h1>

<p>
Account Activation
</p>

</div>


<div class="card">


<div class="hero">

<div class="hero-icon">
{{ lock_svg|safe }}
</div>

<div>

<h2>
Activate Your Account
</h2>

<p>
Enter your activation code or choose your payment method.
</p>

</div>

</div>


{% if error %}

<div class="alert">
{{ error }}
</div>

{% endif %}


<!-- ACTIVATION CODE -->

<div class="section">

<div class="section-title">

<h3>
Activation Code
</h3>

<span>
Instant Activation
</span>

</div>


<div class="code-box">

<form method="POST">

<label class="input-label">
Activation Code
</label>

<input
    class="code-input"
    type="text"
    name="code"
    placeholder="RS-XXXX-XXXX-XXXX"
    autocomplete="off"
    required
>


<button
    class="activate-btn"
    type="submit"
>
ACTIVATE ACCOUNT
</button>

</form>

</div>

</div>


<!-- PAYMENT METHODS -->

<div class="section">

<div class="section-title">

<h3>
Payment Method
</h3>

<span>
Choose One
</span>

</div>


<div class="payment-grid">


<button
    type="button"
    class="payment-card"
    id="payment-card-bkash"
    onclick="selectPayment('bkash')"
>

<div class="payment-logo">
{{ bkash_svg|safe }}
</div>

<div class="payment-name">
bKash
</div>

<div class="payment-price">
৳100
</div>

</button>


<button
    type="button"
    class="payment-card"
    id="payment-card-nagad"
    onclick="selectPayment('nagad')"
>

<div class="payment-logo">
{{ nagad_svg|safe }}
</div>

<div class="payment-name">
Nagad
</div>

<div class="payment-price">
৳100
</div>

</button>


<button
    type="button"
    class="payment-card"
    id="payment-card-binance"
    onclick="selectPayment('binance')"
>

<div class="payment-logo">
{{ binance_svg|safe }}
</div>

<div class="payment-name">
Binance
</div>

<div class="payment-price">
$1
</div>

</button>


</div>


<div
    class="payment-panel"
    id="payment-panel"
>


<div class="payment-head">

<div
    class="payment-head-logo"
    id="payment-logo"
></div>

<div>

<strong id="payment-title">
Payment Details
</strong>

<small>
Complete your payment using the selected method.
</small>

</div>

</div>


<div class="amount-box">

<span class="amount-label">
Amount Required
</span>

<span
    class="amount-value"
    id="payment-amount"
>
-
</span>

</div>


<span class="demo-label">
DEMO PAYMENT DETAILS
</span>


<div class="account-box">

<span
    class="account"
    id="payment-account"
>
-
</span>

<button
    class="copy-btn"
    type="button"
    onclick="copyPaymentAccount()"
>
COPY
</button>

</div>


<div
    class="payment-note"
    id="payment-note"
>
</div>


<form
    method="POST"
    action="/payment-confirm"
>

<input
    type="hidden"
    name="method"
    id="payment-method"
>


<button
    class="confirm-btn"
    type="submit"
>
I HAVE PAID • CONFIRM PAYMENT
</button>

</form>


</div>

</div>


<!-- TELEGRAM SUPPORT -->

<div class="section">

<div class="section-title">

<h3>
Support Telegram
</h3>

<span>
Contact Us
</span>

</div>


<a
    class="support"
    href="{{ telegram_url }}"
    target="_blank"
    rel="noopener noreferrer"
>

<div class="support-logo">
{{ telegram_svg|safe }}
</div>

<div>

<strong>
RS Trader Support
</strong>

<span>
{{ telegram_username }}
</span>

</div>

</a>

</div>


<div class="info">

<b>Payment Amount:</b>

bKash ৳100 • Nagad ৳100 • Binance $1

<br><br>

After completing payment, press
<b>CONFIRM PAYMENT</b>
and contact
<b>{{ telegram_username }}</b>
on Telegram.

<br><br>

The current payment numbers and Binance ID are
demo placeholders and can be replaced later.

</div>


</div>


<div class="footer">
RS TRADER • SECURE ACTIVATION SYSTEM
</div>


</div>


<script>

const paymentData = {

    bkash: {

        name: "bKash",

        amount: "৳100",

        account: "01XXXXXXXXX",

        note:
            "DEMO ONLY — Real bKash number will be added later.",

        logo:
            `{{ bkash_svg|safe }}`

    },


    nagad: {

        name: "Nagad",

        amount: "৳100",

        account: "01XXXXXXXXX",

        note:
            "DEMO ONLY — Real Nagad number will be added later.",

        logo:
            `{{ nagad_svg|safe }}`

    },


    binance: {

        name: "Binance",

        amount: "$1",

        account: "DEMO-BINANCE-ID-2026",

        note:
            "DEMO ONLY — Real Binance ID will be added later.",

        logo:
            `{{ binance_svg|safe }}`

    }

};


function selectPayment(method){

    const data =
        paymentData[method];

    if(!data){

        return;

    }


    document
        .querySelectorAll(".payment-card")
        .forEach(card => {

            card.classList.remove(
                "active"
            );

        });


    const selected =
        document.getElementById(
            "payment-card-" + method
        );


    if(selected){

        selected.classList.add(
            "active"
        );

    }


    document
        .getElementById(
            "payment-panel"
        )
        .classList.add(
            "show"
        );


    document
        .getElementById(
            "payment-title"
        )
        .textContent =
            data.name + " Payment";


    document
        .getElementById(
            "payment-amount"
        )
        .textContent =
            data.amount;


    document
        .getElementById(
            "payment-account"
        )
        .textContent =
            data.account;


    document
        .getElementById(
            "payment-note"
        )
        .textContent =
            data.note;


    document
        .getElementById(
            "payment-method"
        )
        .value =
            method;


    document
        .getElementById(
            "payment-logo"
        )
        .innerHTML =
            data.logo;


    document
        .getElementById(
            "payment-panel"
        )
        .scrollIntoView({

            behavior:"smooth",

            block:"center"

        });

}


async function copyPaymentAccount(){

    const account =
        document
            .getElementById(
                "payment-account"
            )
            .textContent;


    try{

        await navigator
            .clipboard
            .writeText(account);


        const btn =
            document
                .querySelector(
                    ".copy-btn"
                );


        const old =
            btn.textContent;


        btn.textContent =
            "COPIED";


        setTimeout(() => {

            btn.textContent =
                old;

        }, 1400);

    }

    catch(error){

        alert(
            "Copy is not available on this browser."
        );

    }

}

</script>


</body>

</html>

"""

# =========================================================
# PAYMENT CONFIRMATION PAGE
# =========================================================

PAYMENT_CONTACT_HTML = """

<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>RS Trader • Payment Confirmation</title>

<style>

*{
    box-sizing:border-box;
}

body{

    margin:0;

    min-height:100vh;

    display:flex;

    align-items:center;

    justify-content:center;

    padding:18px;

    background:
        radial-gradient(
            circle at top left,
            rgba(34,197,94,.13),
            transparent 28%
        ),
        radial-gradient(
            circle at bottom right,
            rgba(37,99,235,.13),
            transparent 30%
        ),
        #050811;

    color:white;

    font-family:
        Inter,
        Arial,
        sans-serif;
}

.card{

    width:min(
        100%,
        480px
    );

    padding:28px 22px;

    border-radius:24px;

    text-align:center;

    background:
        linear-gradient(
            145deg,
            rgba(15,23,42,.98),
            rgba(8,13,24,.99)
        );

    border:
        1px solid
        rgba(148,163,184,.11);

    box-shadow:
        0 25px 75px
        rgba(0,0,0,.43);
}

.check{

    width:72px;

    height:72px;

    margin:
        0 auto 17px;

    color:#22c55e;
}

.check svg{

    width:100%;
    height:100%;
}

h1{

    margin:0;

    font-size:25px;

}

.subtitle{

    margin:
        8px 0 20px;

    color:#64748b;

    font-size:11px;

    line-height:1.65;
}

.method{

    padding:12px;

    border-radius:12px;

    background:
        rgba(255,255,255,.025);

    border:
        1px solid
        rgba(255,255,255,.06);

    color:#cbd5e1;

    font-size:11px;

}

.amount{

    margin-top:11px;

    padding:14px;

    border-radius:13px;

    background:
        rgba(34,197,94,.07);

    border:
        1px solid
        rgba(34,197,94,.17);
}

.amount-label{

    display:block;

    color:#64748b;

    font-size:8px;

    text-transform:uppercase;

    font-weight:900;

    letter-spacing:1px;
}

.amount-value{

    display:block;

    margin-top:4px;

    color:#86efac;

    font-size:27px;

    font-weight:950;
}

.telegram{

    display:flex;

    align-items:center;

    gap:13px;

    margin-top:17px;

    padding:15px;

    border-radius:16px;

    text-decoration:none;

    text-align:left;

    background:
        linear-gradient(
            135deg,
            rgba(34,158,217,.12),
            rgba(37,99,235,.06)
        );

    border:
        1px solid
        rgba(34,158,217,.22);
}

.telegram-logo{

    width:50px;

    height:50px;

    flex:0 0 50px;
}

.telegram-logo svg{

    width:100%;
    height:100%;
}

.telegram-title{

    display:block;

    font-size:13px;

    font-weight:900;
}

.telegram-user{

    display:block;

    margin-top:3px;

    color:#8fd5f7;

    font-size:11px;

    font-weight:800;
}

.note{

    margin-top:17px;

    padding:12px;

    border-radius:11px;

    color:#64748b;

    background:
        rgba(255,255,255,.02);

    border:
        1px solid
        rgba(255,255,255,.05);

    font-size:9px;

    line-height:1.6;
}

.back{

    display:inline-block;

    margin-top:17px;

    color:#64748b;

    font-size:10px;

    font-weight:800;

    text-decoration:none;
}

.back:hover{

    color:#93c5fd;
}

</style>

</head>

<body>


<div class="card">


<div class="check">
{{ check_svg|safe }}
</div>


<h1>
Payment Confirmation
</h1>


<div class="subtitle">

Your confirmation request has been submitted.
Contact RS Trader Support on Telegram to complete
the manual verification process.

</div>


<div class="method">

Selected Payment Method:

<b>
{{ payment_method }}
</b>

</div>


<div class="amount">

<span class="amount-label">
Payment Amount
</span>

<span class="amount-value">
{{ payment_amount }}
</span>

</div>


<a
    class="telegram"
    href="{{ telegram_url }}"
    target="_blank"
    rel="noopener noreferrer"
>

<div class="telegram-logo">
{{ telegram_svg|safe }}
</div>

<div>

<span class="telegram-title">
Open Telegram Support
</span>

<span class="telegram-user">
{{ telegram_username }}
</span>

</div>

</a>


<div class="note">

Payment verification is handled manually.

After opening Telegram, send your payment
information or screenshot to
{{ telegram_username }}.

</div>


<a
    class="back"
    href="{{ url_for('activate') }}"
>
← Back to Activation
</a>


</div>


</body>

</html>

"""

# =========================================================
# FORGOT PASSWORD
# =========================================================

FORGOT_HTML = """

<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>RS Trader • Password Recovery</title>

<style>
""" + AUTH_CSS + """
</style>

</head>

<body>

<div class="auth-wrapper">

<div class="brand">

<div class="logo">
RS
</div>

<h1>
RS Trader
</h1>

<p>
Password Recovery
</p>

</div>


<div class="card">

<div class="card-icon">
↻
</div>


<h2>
Reset Password
</h2>


<div class="subtitle">
Use your username and assigned activation code
to create a new password.
</div>


{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}


{% if success %}

<div class="success">
{{ success }}
</div>

{% endif %}


<form method="POST">


<div class="field">

<label>
Username
</label>

<input
    class="input"
    type="text"
    name="username"
    placeholder="Your username"
    required
>

</div>


<div class="field">

<label>
Activation Code
</label>

<input
    class="input"
    type="text"
    name="code"
    placeholder="Your activation code"
    autocomplete="off"
    required
>

</div>


<div class="field">

<label>
New Password
</label>

<input
    class="input"
    type="password"
    name="password"
    placeholder="Create new password"
    required
>

</div>


<div class="field">

<label>
Confirm New Password
</label>

<input
    class="input"
    type="password"
    name="confirm_password"
    placeholder="Confirm new password"
    required
>

</div>


<button
    class="main-button"
    type="submit"
>
RESET PASSWORD
</button>


</form>


<a
    class="support-box"
    href="{{ telegram_url }}"
    target="_blank"
    rel="noopener noreferrer"
>

<span class="telegram-icon">
{{ telegram_svg|safe }}
</span>

<span>

<span class="support-title">
Need Help?
</span>

<span class="support-user">
{{ telegram_username }}
</span>

</span>

</a>


<div class="links"
     style="justify-content:center;">

<a href="/login"
   class="create-account-link">
BACK TO LOGIN
</a>

</div>


<div class="security">
Your activation code remains assigned to your account.
</div>


</div>


<div class="footer">
RS TRADER • PASSWORD RECOVERY
</div>


</div>

</body>

</html>

"""

# =========================================================
# DASHBOARD HTML
# =========================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>RS Trader • Money Management</title>

<style>

*{
    box-sizing:border-box;
}

body{
    margin:0;

    min-height:100vh;

    background:
        radial-gradient(
            circle at 15% 0%,
            rgba(37,99,235,.12),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 15%,
            rgba(124,58,237,.10),
            transparent 28%
        ),
        #060912;

    color:#f8fafc;

    font-family:Inter,Arial,sans-serif;
}

.container{
    width:min(1100px,94%);

    margin:auto;

    padding:30px 0 50px;
}


/* HEADER */

.header{
    display:flex;

    justify-content:space-between;

    align-items:center;

    margin-bottom:28px;
}

.logo-area{
    display:flex;

    align-items:center;

    gap:14px;
}

.logo{
    width:52px;
    height:52px;

    border-radius:15px;

    display:flex;

    align-items:center;
    justify-content:center;

    font-size:18px;

    font-weight:900;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #7c3aed
        );

    box-shadow:
        0 10px 35px rgba(37,99,235,.30);
}

.title h1{
    margin:0;

    font-size:26px;

    letter-spacing:-.5px;
}

.title p{
    margin:4px 0 0;

    color:#64748b;

    font-size:11px;

    letter-spacing:1px;

    text-transform:uppercase;
}

.header-right{
    display:flex;

    align-items:center;

    gap:10px;
}


/* TELEGRAM */

.telegram{
    display:flex;

    align-items:center;

    gap:9px;

    padding:8px 13px;

    border-radius:22px;

    background:
        linear-gradient(
            135deg,
            rgba(37,99,235,.13),
            rgba(59,130,246,.07)
        );

    border:1px solid rgba(59,130,246,.22);

    color:#93c5fd;

    text-decoration:none;

    font-size:10px;

    font-weight:800;

    cursor:pointer;

    transition:.18s;
}

.telegram:hover{
    background:
        rgba(59,130,246,.17);

    border-color:
        rgba(59,130,246,.35);

    transform:
        translateY(-1px);
}

.telegram-logo{
    width:25px;
    height:25px;

    display:flex;

    align-items:center;
    justify-content:center;

    border-radius:50%;

    background:#229ED9;

    color:white;

    font-size:12px;

    font-weight:900;
}

.telegram-text{
    display:flex;

    flex-direction:column;

    gap:2px;
}

.telegram-title{
    color:#e2e8f0;

    font-size:9px;

    letter-spacing:.3px;
}

.telegram-user{
    color:#60a5fa;

    font-size:8px;

    font-weight:700;
}

.active{
    display:flex;

    align-items:center;

    gap:8px;

    padding:9px 13px;

    border-radius:20px;

    background:
        rgba(34,197,94,.07);

    border:
        1px solid
        rgba(34,197,94,.16);

    color:#86efac;

    font-size:10px;

    font-weight:800;

    letter-spacing:.8px;
}

.active-dot{
    width:7px;
    height:7px;

    border-radius:50%;

    background:#22c55e;

    box-shadow:
        0 0 12px #22c55e;
}


/* CARDS */

.cards{
    display:grid;

    grid-template-columns:
        repeat(4,1fr);

    gap:14px;

    margin-bottom:15px;
}

.card{
    background:
        rgba(15,23,42,.88);

    border:
        1px solid
        rgba(148,163,184,.09);

    border-radius:18px;

    padding:20px;

    box-shadow:
        0 15px 40px rgba(0,0,0,.22);

    backdrop-filter:blur(10px);
}

.card-label{
    color:#64748b;

    font-size:10px;

    text-transform:uppercase;

    letter-spacing:1px;

    font-weight:700;
}

.card-value{
    margin-top:9px;

    font-size:27px;

    font-weight:850;
}

.next-card{
    position:relative;

    overflow:hidden;

    background:
        linear-gradient(
            145deg,
            rgba(30,64,175,.38),
            rgba(15,23,42,.95)
        );

    border:
        1px solid
        rgba(59,130,246,.48);

    box-shadow:
        0 0 0 1px
        rgba(59,130,246,.05),
        0 15px 45px
        rgba(37,99,235,.15);
}

.next-value{
    color:#60a5fa;

    font-size:32px;
}


/* COLORS */

.green{
    color:#22c55e;
}

.red{
    color:#ef4444;
}

.blue{
    color:#60a5fa;
}

.yellow{
    color:#f59e0b;
}


/* ERROR */

.error{
    margin-bottom:15px;

    padding:12px 14px;

    border-radius:10px;

    color:#fca5a5;

    background:
        rgba(239,68,68,.08);

    border:
        1px solid
        rgba(239,68,68,.20);

    font-size:10px;
}


/* STATUS */

.status-box{
    margin-bottom:15px;

    background:
        rgba(15,23,42,.88);

    border:
        1px solid
        rgba(148,163,184,.09);

    border-radius:18px;

    padding:18px 20px;

    display:flex;

    justify-content:space-between;

    align-items:center;
}

.status-title{
    color:#64748b;

    font-size:9px;

    text-transform:uppercase;

    letter-spacing:1px;

    font-weight:700;
}

.status-value{
    margin-top:6px;

    font-size:15px;

    font-weight:850;
}


/* STATS */

.stats{
    display:grid;

    grid-template-columns:
        repeat(4,1fr);

    gap:12px;

    margin-bottom:15px;
}

.stat{
    background:
        rgba(15,23,42,.78);

    border:
        1px solid
        rgba(148,163,184,.07);

    border-radius:15px;

    padding:16px;
}

.stat-label{
    color:#64748b;

    font-size:9px;

    text-transform:uppercase;

    letter-spacing:.8px;

    font-weight:700;
}

.stat-value{
    margin-top:7px;

    font-size:21px;

    font-weight:850;
}


/* PANELS */

.panel{
    background:
        linear-gradient(
            145deg,
            rgba(15,23,42,.98),
            rgba(9,14,25,.98)
        );

    border:
        1px solid
        rgba(148,163,184,.10);

    border-radius:18px;

    padding:22px;

    margin-bottom:15px;
}

.panel-title{
    margin:0;

    font-size:17px;

    font-weight:800;
}

.panel-subtitle{
    margin:5px 0 19px;

    color:#64748b;

    font-size:10px;
}


/* TRADE */

.trade-buttons{
    display:grid;

    grid-template-columns:
        1fr 1fr;

    gap:13px;
}

button{
    border:0;

    color:white;

    padding:15px;

    border-radius:12px;

    cursor:pointer;

    font-size:13px;

    font-weight:850;

    transition:.18s ease;
}

button:hover{
    transform:
        translateY(-2px);

    filter:
        brightness(1.08);
}

.win{
    background:
        linear-gradient(
            135deg,
            #15803d,
            #22c55e
        );
}

.loss{
    background:
        linear-gradient(
            135deg,
            #b91c1c,
            #ef4444
        );
}


/* SETTINGS */

.settings-panel{
    padding:24px;
}

.settings-top{
    display:flex;

    justify-content:space-between;

    align-items:flex-start;

    margin-bottom:24px;
}

.settings-badge{
    display:inline-block;

    padding:5px 9px;

    margin-bottom:8px;

    border-radius:6px;

    background:
        rgba(59,130,246,.10);

    border:
        1px solid
        rgba(59,130,246,.18);

    color:#60a5fa;

    font-size:8px;

    font-weight:800;

    letter-spacing:1.2px;
}

.settings-icon{
    width:40px;
    height:40px;

    display:flex;

    align-items:center;
    justify-content:center;

    border-radius:11px;

    background:#0b1220;

    border:1px solid #263449;

    color:#60a5fa;
}

.settings-grid{
    display:grid;

    grid-template-columns:
        repeat(3,1fr);

    gap:16px;
}

.setting-field{
    padding:14px;

    border-radius:13px;

    background:
        rgba(8,13,24,.75);

    border:
        1px solid
        rgba(148,163,184,.08);
}

.setting-field label{
    display:block;

    margin-bottom:8px;

    color:#94a3b8;

    font-size:9px;

    font-weight:800;

    letter-spacing:.8px;

    text-transform:uppercase;
}

.input-wrap{
    display:flex;

    align-items:center;

    height:42px;

    background:#060b14;

    border:
        1px solid
        #263449;

    border-radius:9px;

    overflow:hidden;
}

.input-icon{
    width:34px;

    text-align:center;

    color:#60a5fa;

    font-size:13px;

    font-weight:900;
}

.input-wrap input{
    flex:1;

    width:auto;

    height:100%;

    padding:0 5px;

    border:0;

    background:transparent;

    color:#f8fafc;

    outline:none;

    font-size:13px;

    font-weight:700;
}

.input-unit{
    padding:
        0 10px;

    color:#475569;

    font-size:8px;

    font-weight:800;
}

.settings-save{
    width:100%;

    height:46px;

    margin-top:18px;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #4f46e5
        );
}

.reset{
    width:100%;

    height:40px;

    margin-top:10px;

    background:#111a2a;

    color:#cbd5e1;

    border:
        1px solid
        #263449;
}

.logout{
    display:block;

    width:max-content;

    margin:25px auto 0;

    color:#475569;

    text-decoration:none;

    font-size:9px;

    letter-spacing:.5px;
}

.logout:hover{
    color:#94a3b8;
}

.footer{
    text-align:center;

    color:#334155;

    font-size:9px;

    letter-spacing:.8px;

    margin-top:25px;
}


/* MOBILE */

@media(max-width:850px){

    .cards{
        grid-template-columns:
            1fr 1fr;
    }

    .stats{
        grid-template-columns:
            1fr 1fr;
    }

    .settings-grid{
        grid-template-columns:
            1fr 1fr;
    }

}

@media(max-width:550px){

    .container{
        width:92%;

        padding-top:20px;
    }

    .header{
        margin-bottom:20px;
    }

    .logo{
        width:45px;
        height:45px;
    }

    .title h1{
        font-size:21px;
    }

    .title p{
        font-size:9px;
    }

    .active{
        display:none;
    }

    .telegram{
        padding:7px 9px;
    }

    .telegram-title{
        font-size:8px;
    }

    .cards{
        gap:9px;
    }

    .card{
        padding:15px;

        border-radius:15px;
    }

    .card-value{
        font-size:21px;
    }

    .next-value{
        font-size:25px;
    }

    .status-box{
        padding:16px;
    }

    .panel{
        padding:17px;

        border-radius:15px;
    }

    .settings-panel{
        padding:17px;
    }

    .settings-grid{
        grid-template-columns:1fr;

        gap:10px;
    }

    .setting-field{
        padding:12px;
    }

    .trade-buttons{
        gap:9px;
    }

}

</style>

</head>


<body>

<div class="container">


<!-- HEADER -->

<div class="header">

    <div class="logo-area">

        <div class="logo">
            RS
        </div>

        <div class="title">

            <h1>
                RS Trader
            </h1>

            <p>
                Money Management System
            </p>

        </div>

    </div>


    <div class="header-right">


        <a
            class="telegram"
            href="{{ telegram_url }}"
            target="_blank"
            rel="noopener noreferrer"
            title="Contact RS Trader Support"
        >

            <span class="telegram-logo">
                ➤
            </span>

            <span class="telegram-text">

                <span class="telegram-title">
                    Support Telegram
                </span>

                <span class="telegram-user">
                    {{ telegram_username }}
                </span>

            </span>

        </a>


        <div class="active">

            <span class="active-dot"></span>

            ACTIVE

        </div>

    </div>

</div>


{% if error %}

<div class="error">
    {{ error }}
</div>

{% endif %}


<!-- MAIN CARDS -->

<div class="cards">


    <div class="card">

        <div class="card-label">
            Balance
        </div>

        <div class="card-value">
            ${{ "%.2f"|format(calculator.balance) }}
        </div>

    </div>


    <div class="card">

        <div class="card-label">
            Total P/L
        </div>

        <div class="card-value
            {% if calculator.total_profit_loss >= 0 %}
                green
            {% else %}
                red
            {% endif %}
        ">

            {% if calculator.total_profit_loss >= 0 %}
                +
            {% endif %}

            ${{ "%.2f"|format(
                calculator.total_profit_loss
            ) }}

        </div>

    </div>


    <div class="card next-card">

        <div class="card-label">
            Next Trade
        </div>

        <div class="card-value next-value">

            ${{ "%.2f"|format(
                calculator.calculate_next_amount()
            ) }}

        </div>

    </div>


    <div class="card">

        <div class="card-label">
            Profit Target
        </div>

        <div class="card-value blue">

            ${{ "%.2f"|format(
                calculator.profit_target_amount
            ) }}

        </div>

    </div>

</div>


<!-- STATUS -->

<div class="status-box">

    <div>

        <div class="status-title">
            Session Status
        </div>

        <div class="status-value">

            {% if calculator.session_stopped %}

                <span class="red">
                    {{ calculator.get_status() }}
                </span>

            {% elif calculator.loss_streak > 0 %}

                <span class="yellow">
                    {{ calculator.get_status() }}
                </span>

            {% else %}

                <span class="green">
                    {{ calculator.get_status() }}
                </span>

            {% endif %}

        </div>

    </div>


    <div>

        <div class="status-title">
            Stop Loss
        </div>

        <div class="status-value red">

            ${{ "%.2f"|format(
                calculator.stop_loss_amount
            ) }}

        </div>

    </div>

</div>


<!-- STATISTICS -->

<div class="stats">


    <div class="stat">

        <div class="stat-label">
            Trades
        </div>

        <div class="stat-value">
            {{ calculator.trade_number }}
        </div>

    </div>


    <div class="stat">

        <div class="stat-label">
            Wins
        </div>

        <div class="stat-value green">
            {{ calculator.win_count }}
        </div>

    </div>


    <div class="stat">

        <div class="stat-label">
            Losses
        </div>

        <div class="stat-value red">
            {{ calculator.loss_count }}
        </div>

    </div>


    <div class="stat">

        <div class="stat-label">
            Win Rate
        </div>

        <div class="stat-value blue">

            {% if calculator.trade_number > 0 %}

                {{ "%.1f"|format(
                    (calculator.win_count /
                    calculator.trade_number) * 100
                ) }}%

            {% else %}

                0.0%

            {% endif %}

        </div>

    </div>

</div>


<!-- TRADE CONTROL -->

<div class="panel">

    <h2 class="panel-title">
        Trade Control
    </h2>

    <p class="panel-subtitle">
        Record your latest trading result
    </p>


    <form
        method="POST"
        action="/trade"
    >

        <div class="trade-buttons">

            <button
                class="win"
                type="submit"
                name="result"
                value="WIN"
            >
                ✓ &nbsp; WIN
            </button>


            <button
                class="loss"
                type="submit"
                name="result"
                value="LOSS"
            >
                ✕ &nbsp; LOSS
            </button>

        </div>

    </form>

</div>


<!-- SETTINGS -->

<div class="panel settings-panel">


    <div class="settings-top">

        <div>

            <div class="settings-badge">
                RISK CONTROL
            </div>

            <h2 class="panel-title">
                Money Management
            </h2>

            <p class="panel-subtitle">
                Configure your trading risk parameters
            </p>

        </div>


        <div class="settings-icon">
            ⚙
        </div>

    </div>


    <form
        method="POST"
        action="/settings"
    >


        <div class="settings-grid">


            <div class="setting-field">

                <label>
                    Starting Capital
                </label>

                <div class="input-wrap">

                    <span class="input-icon">
                        $
                    </span>

                    <input
                        type="number"
                        step="0.01"
                        name="starting_capital"
                        value="{{ calculator.starting_capital }}"
                    >

                    <span class="input-unit">
                        USD
                    </span>

                </div>

            </div>


            <div class="setting-field">

                <label>
                    Payout
                </label>

                <div class="input-wrap">

                    <span class="input-icon">
                        ↗
                    </span>

                    <input
                        type="number"
                        step="0.01"
                        name="payout"
                        value="{{ calculator.payout * 100 }}"
                    >

                    <span class="input-unit">
                        %
                    </span>

                </div>

            </div>


            <div class="setting-field">

                <label>
                    Profit Target
                </label>

                <div class="input-wrap">

                    <span class="input-icon">
                        ✓
                    </span>

                    <input
                        type="number"
                        step="0.01"
                        name="profit_target_percent"
                        value="{{ calculator.profit_target_percent }}"
                    >

                    <span class="input-unit">
                        %
                    </span>

                </div>

            </div>


            <div class="setting-field">

                <label>
                    Stop Loss
                </label>

                <div class="input-wrap">

                    <span class="input-icon">
                        !
                    </span>

                    <input
                        type="number"
                        step="0.01"
                        name="stop_loss_percent"
                        value="{{ calculator.stop_loss_percent }}"
                    >

                    <span class="input-unit">
                        %
                    </span>

                </div>

            </div>


            <div class="setting-field">

                <label>
                    Max Loss Streak
                </label>

                <div class="input-wrap">

                    <span class="input-icon">
                        ↻
                    </span>

                    <input
                        type="number"
                        name="max_loss_streak"
                        value="{{ calculator.max_loss_streak }}"
                    >

                    <span class="input-unit">
                        TRADES
                    </span>

                </div>

            </div>


            <div class="setting-field">

                <label>
                    Base Risk
                </label>

                <div class="input-wrap">

                    <span class="input-icon">
                        ◈
                    </span>

                    <input
                        type="number"
                        step="0.01"
                        name="base_risk_percent"
                        value="{{ calculator.base_risk_percent }}"
                    >

                    <span class="input-unit">
                        %
                    </span>

                </div>

            </div>


        </div>


        <button
            class="settings-save"
            type="submit"
        >
            ✓ &nbsp; Save Configuration
        </button>


    </form>


    <form
        method="POST"
        action="/reset"
    >

        <button
            class="reset"
            type="submit"
        >
            Reset Session
        </button>

    </form>


</div>


<a
    class="logout"
    href="/logout"
>
    SIGN OUT
</a>


<div class="footer">
    RS TRADER • MONEY MANAGEMENT
</div>


</div>

</body>

</html>
"""


# =========================================================
# ROOT
# =========================================================

@app.route("/")
def root():

    if not session.get("logged_in"):

        return redirect(
            url_for("login")
        )

    if not session.get("activated"):

        return redirect(
            url_for("activate")
        )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if (
        session.get("logged_in")
        and
        session.get("activated")
    ):

        return redirect(
            url_for("dashboard")
        )


    error = None
    success = None


    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        conn = get_db()

        user = conn.execute(

            """
            SELECT *
            FROM users
            WHERE username = ?
            """,

            (
                username,
            )

        ).fetchone()

        conn.close()


        if (
            user
            and
            check_password_hash(
                user["password_hash"],
                password
            )
        ):

            session["logged_in"] = True

            session["username"] = (
                user["username"]
            )


            if user["activation_code"]:

                session["activated"] = True

                return redirect(
                    url_for("dashboard")
                )


            session["activated"] = False

            return redirect(
                url_for("activate")
            )


        error = (
            "Invalid username or password."
        )


    return render_template_string(

        LOGIN_HTML,

        error=error,

        success=success,

        telegram_username=
            TELEGRAM_USERNAME,

        telegram_url=
            TELEGRAM_URL,

        telegram_svg=
            TELEGRAM_SVG,

    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if session.get("logged_in"):

        return redirect(
            url_for("root")
        )


    error = None


    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        if not valid_username(
            username
        ):

            error = (
                "Username must be 3–30 characters "
                "and may contain letters, numbers, "
                "_, - or ."
            )


        elif not valid_password(
            password
        ):

            error = (
                "Password must contain at least 6 characters."
            )


        elif password != confirm_password:

            error = (
                "Passwords do not match."
            )


        else:

            conn = get_db()


            existing = conn.execute(

                """
                SELECT id
                FROM users
                WHERE LOWER(username) = LOWER(?)
                """,

                (
                    username,
                )

            ).fetchone()


            if existing:

                conn.close()

                error = (
                    "This username is already taken."
                )

            else:

                password_hash = (
                    generate_password_hash(
                        password
                    )
                )


                conn.execute(

                    """
                    INSERT INTO users
                    (
                        username,
                        password_hash,
                        activation_code
                    )
                    VALUES (?, ?, ?)
                    """,

                    (
                        username,
                        password_hash,
                        None
                    )

                )


                conn.commit()

                conn.close()


                session.clear()

                session["logged_in"] = True

                session["username"] = (
                    username
                )

                session["activated"] = False


                return redirect(
                    url_for("activate")
                )


    return render_template_string(

        REGISTER_HTML,

        error=error,

        telegram_username=
            TELEGRAM_USERNAME,

        telegram_url=
            TELEGRAM_URL,

        telegram_svg=
            TELEGRAM_SVG,

    )


# =========================================================
# ACTIVATION
# =========================================================

@app.route(
    "/activate",
    methods=["GET", "POST"]
)
def activate():

    if not session.get("logged_in"):

        return redirect(
            url_for("login")
        )


    username = session.get(
        "username"
    )


    if session.get("activated"):

        return redirect(
            url_for("dashboard")
        )


    error = None


    if request.method == "POST":

        code = request.form.get(
            "code",
            ""
        ).strip().upper()


        conn = get_db()


        row = conn.execute(

            """
            SELECT *
            FROM activation_codes
            WHERE code = ?
            """,

            (
                code,
            )

        ).fetchone()


        if row is None:

            conn.close()

            error = (
                "Invalid activation code."
            )


        elif (

            row["used"] == 1

            and
            row["owner_username"]

            and
            row["owner_username"] != username

        ):

            conn.close()

            error = (
                "This activation code is already "
                "assigned to another account."
            )


        elif (

            row["used"] == 1

            and
            row["owner_username"] == username

        ):

            conn.close()

            session["activated"] = True

            return redirect(
                url_for("dashboard")
            )


        else:

            conn.execute(

                """
                UPDATE activation_codes

                SET
                    used = 1,
                    owner_username = ?

                WHERE id = ?

                """,

                (
                    username,
                    row["id"]
                )

            )


            conn.execute(

                """
                UPDATE users

                SET activation_code = ?

                WHERE username = ?

                """,

                (
                    code,
                    username
                )

            )


            conn.commit()

            conn.close()


            session["activated"] = True


            return redirect(
                url_for("dashboard")
            )


    return render_template_string(

        ACTIVATE_HTML,

        error=error,

        telegram_username=
            TELEGRAM_USERNAME,

        telegram_url=
            TELEGRAM_URL,

        telegram_svg=
            TELEGRAM_SVG,

        lock_svg=
            LOCK_SVG,

        check_svg=
            CHECK_SVG,

        bkash_svg=
            BKASH_SVG,

        nagad_svg=
            NAGAD_SVG,

        binance_svg=
            BINANCE_SVG

    )


# =========================================================
# PAYMENT CONFIRMATION
# =========================================================

@app.route(
    "/payment-confirm",
    methods=["POST"]
)
def payment_confirm():

    if not session.get("logged_in"):

        return redirect(
            url_for("login")
        )


    if session.get("activated"):

        return redirect(
            url_for("dashboard")
        )


    method = request.form.get(
        "method",
        ""
    ).strip().lower()


    if method not in PAYMENT_METHODS:

        return redirect(
            url_for("activate")
        )


    payment = PAYMENT_METHODS[
        method
    ]


    username = session.get(
        "username",
        ""
    )


    conn = get_db()


    conn.execute(

        """
        INSERT INTO payment_requests
        (
            username,
            method,
            account,
            amount
        )
        VALUES (?, ?, ?, ?)
        """,

        (
            username,

            method,

            payment["account"],

            payment["amount"]
        )

    )


    conn.commit()

    conn.close()


    return render_template_string(

        PAYMENT_CONTACT_HTML,

        payment_method=
            payment["name"],

        payment_amount=
            payment["amount"],

        telegram_username=
            TELEGRAM_USERNAME,

        telegram_url=
            TELEGRAM_URL,

        telegram_svg=
            TELEGRAM_SVG,

        check_svg=
            CHECK_SVG

    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    error = None
    success = None


    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        code = request.form.get(
            "code",
            ""
        ).strip().upper()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        if not valid_password(
            password
        ):

            error = (
                "New password must contain at least 6 characters."
            )


        elif password != confirm_password:

            error = (
                "Passwords do not match."
            )


        else:

            conn = get_db()


            user = conn.execute(

                """
                SELECT *
                FROM users
                WHERE username = ?
                """,

                (
                    username,
                )

            ).fetchone()


            activation = conn.execute(

                """
                SELECT *
                FROM activation_codes
                WHERE code = ?
                AND used = 1
                AND owner_username = ?
                """,

                (
                    code,
                    username
                )

            ).fetchone()


            if (
                user is None
                or
                activation is None
            ):

                conn.close()

                error = (
                    "Username or activation code is incorrect."
                )

            else:

                new_hash = (
                    generate_password_hash(
                        password
                    )
                )


                conn.execute(

                    """
                    UPDATE users
                    SET password_hash = ?
                    WHERE username = ?
                    """,

                    (
                        new_hash,
                        username
                    )

                )


                conn.commit()

                conn.close()


                success = (
                    "Password reset successfully. "
                    "You can now sign in."
                )


    return render_template_string(

        FORGOT_HTML,

        error=error,

        success=success,

        telegram_username=
            TELEGRAM_USERNAME,

        telegram_url=
            TELEGRAM_URL,

        telegram_svg=
            TELEGRAM_SVG,

        check_svg=
            CHECK_SVG

    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not session.get("logged_in"):

        return redirect(
            url_for("login")
        )


    if not session.get("activated"):

        return redirect(
            url_for("activate")
        )


    return render_template_string(

        DASHBOARD_HTML,

        calculator=calculator,

        error=None,

        telegram_username=
            TELEGRAM_USERNAME,

        telegram_url=
            TELEGRAM_URL

    )


# =========================================================
# TRADE
# =========================================================

@app.route(
    "/trade",
    methods=["POST"]
)
def trade():

    if not login_required():

        return redirect(
            url_for("login")
        )


    result = request.form.get(
        "result",
        ""
    ).upper()


    if result not in (
        "WIN",
        "LOSS"
    ):

        return redirect(
            url_for("dashboard")
        )


    try:

        calculator.record_trade(
            result
        )

        return redirect(
            url_for("dashboard")
        )


    except (
        ValueError,
        RuntimeError
    ) as error:

        return render_template_string(

            DASHBOARD_HTML,

            calculator=calculator,

            error=str(error),

            telegram_username=
                TELEGRAM_USERNAME,

            telegram_url=
                TELEGRAM_URL

        )


# =========================================================
# SETTINGS
# =========================================================

@app.route(
    "/settings",
    methods=["POST"]
)
def settings():

    if not login_required():

        return redirect(
            url_for("login")
        )


    try:

        starting_capital = float(

            request.form.get(
                "starting_capital"
            )

        )


        payout = float(

            request.form.get(
                "payout"
            )

        )


        profit_target_percent = float(

            request.form.get(
                "profit_target_percent"
            )

        )


        stop_loss_percent = float(

            request.form.get(
                "stop_loss_percent"
            )

        )


        max_loss_streak = int(

            request.form.get(
                "max_loss_streak"
            )

        )


        base_risk_percent = float(

            request.form.get(
                "base_risk_percent"
            )

        )


        if starting_capital <= 0:

            raise ValueError(
                "Starting capital must be greater than 0."
            )


        if payout < 0:

            raise ValueError(
                "Payout cannot be negative."
            )


        if profit_target_percent < 0:

            raise ValueError(
                "Profit target cannot be negative."
            )


        if stop_loss_percent < 0:

            raise ValueError(
                "Stop loss cannot be negative."
            )


        if max_loss_streak < 0:

            raise ValueError(
                "Max loss streak cannot be negative."
            )


        if base_risk_percent < 0:

            raise ValueError(
                "Base risk cannot be negative."
            )


        calculator.update_settings(

            starting_capital,

            payout,

            profit_target_percent,

            stop_loss_percent,

            max_loss_streak,

            5,

            base_risk_percent

        )


        return redirect(
            url_for("dashboard")
        )


    except (
        ValueError,
        TypeError
    ) as error:


        return render_template_string(

            DASHBOARD_HTML,

            calculator=calculator,

            error=str(error),

            telegram_username=
                TELEGRAM_USERNAME,

            telegram_url=
                TELEGRAM_URL

        )


# =========================================================
# RESET
# =========================================================

@app.route(
    "/reset",
    methods=["POST"]
)
def reset():

    if not login_required():

        return redirect(
            url_for("login")
        )


    calculator.reset()


    return redirect(
        url_for("dashboard")
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "service": "RS Trader",
        "timestamp": datetime.utcnow().isoformat()
    }


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return """

<!DOCTYPE html>

<html>

<head>

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<title>404 • RS Trader</title>

<style>

body{

    margin:0;

    min-height:100vh;

    display:grid;

    place-items:center;

    background:#050811;

    color:white;

    font-family:system-ui,sans-serif;

}

div{

    text-align:center;

    padding:30px;

}

h1{

    margin:0;

    font-size:54px;

}

p{

    color:#64748b;

}

a{

    color:#60a5fa;

    text-decoration:none;

    font-weight:800;

}

</style>

</head>

<body>

<div>

<h1>
404
</h1>

<p>
Page not found.
</p>

<a href="/">
Go to RS Trader
</a>

</div>

</body>

</html>

""", 404


# =========================================================
# 500
# =========================================================

@app.errorhandler(500)
def server_error(error):

    return """

<!DOCTYPE html>

<html>

<head>

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<title>500 • RS Trader</title>

<style>

body{

    margin:0;

    min-height:100vh;

    display:grid;

    place-items:center;

    background:#050811;

    color:white;

    font-family:system-ui,sans-serif;

}

div{

    text-align:center;

    padding:30px;

}

h1{

    margin:0;

    font-size:54px;

}

p{

    color:#64748b;

}

a{

    color:#60a5fa;

    text-decoration:none;

    font-weight:800;

}

</style>

</head>

<body>

<div>

<h1>
500
</h1>

<p>
Something went wrong.
</p>

<a href="/">
Go to RS Trader
</a>

</div>

</body>

</html>

""", 500


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
