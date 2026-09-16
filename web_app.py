from flask import Flask, render_template_string, request, redirect, url_for, session
from calculator import MoneyCalculator
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import re

app = Flask(__name__)

# =========================================================
# SECURITY
# =========================================================

app.secret_key = os.environ.get(
    "RS_TRADER_SECRET",
    "RS-Trader-Local-Secret-2026-Change-This"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

DB_FILE = "rs_trader_auth.db"

SECRET_CODES = [
    "RS-7K9M-X2Q8-P4ZT",
    "RS-3N6V-H8Q2-W5YK",
    "RS-9P4X-T7LM-C2RA",
    "RS-6Q8Z-M3VK-Y7NP",
    "RS-2H5K-R9XD-F6TW",
]

TELEGRAM_USERNAME = "@RSTrader087"
TELEGRAM_URL = "https://t.me/RSTrader087"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            activation_code TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            used INTEGER DEFAULT 0,
            owner_username TEXT
        )
    """)

    # Upgrade old database if owner_username column does not exist
    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(activation_codes)"
        ).fetchall()
    ]

    if "owner_username" not in columns:
        conn.execute(
            "ALTER TABLE activation_codes ADD COLUMN owner_username TEXT"
        )

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
# HELPERS
# =========================================================

def login_required():

    return (
        session.get("logged_in", False)
        and session.get("activated", False)
    )


def valid_username(username):

    return (
        3 <= len(username) <= 30
        and re.fullmatch(
            r"[A-Za-z0-9_.-]+",
            username
        ) is not None
    )


def valid_password(password):

    return len(password) >= 6


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

    font-family:Inter,Arial,sans-serif;
}

.auth-wrapper{
    width:min(440px,92%);
}

.brand{
    text-align:center;
    margin-bottom:24px;
}

.logo{
    width:62px;
    height:62px;

    margin:auto;

    display:flex;
    align-items:center;
    justify-content:center;

    border-radius:18px;

    font-size:21px;
    font-weight:900;

    background:
        linear-gradient(
            135deg,
            #2563eb,
            #7c3aed
        );

    box-shadow:
        0 15px 45px rgba(37,99,235,.30);
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

    border:1px solid rgba(148,163,184,.12);
    border-radius:20px;

    box-shadow:
        0 25px 70px rgba(0,0,0,.45);
}

.card-icon{
    width:48px;
    height:48px;

    display:flex;
    align-items:center;
    justify-content:center;

    margin-bottom:16px;

    border-radius:13px;

    color:#60a5fa;

    background:rgba(59,130,246,.08);

    border:1px solid rgba(59,130,246,.16);

    font-size:19px;
}

h2{
    margin:0;
    font-size:19px;
}

.subtitle{
    margin:7px 0 22px;

    color:#64748b;

    font-size:10px;

    line-height:1.6;
}

.field{
    margin-bottom:14px;
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
    height:46px;

    padding:0 13px;

    background:#060b14;

    color:#fff;

    border:1px solid #263449;

    border-radius:10px;

    outline:none;

    font-size:13px;

    transition:.2s;
}

.input:focus{
    border-color:#3b82f6;

    box-shadow:
        0 0 0 3px rgba(59,130,246,.09);
}

.main-button{
    width:100%;
    height:47px;

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

    font-size:11px;
    font-weight:850;

    cursor:pointer;

    transition:.18s;
}

.main-button:hover{
    filter:brightness(1.08);
    transform:translateY(-1px);
}

.secondary-button{
    width:100%;
    height:44px;

    margin-top:9px;

    border:1px solid #263449;
    border-radius:10px;

    color:#cbd5e1;

    background:#0b1220;

    font-size:10px;
    font-weight:800;

    cursor:pointer;
}

.error{
    margin-bottom:16px;

    padding:11px 12px;

    border-radius:9px;

    color:#fca5a5;

    background:rgba(239,68,68,.08);

    border:1px solid rgba(239,68,68,.20);

    font-size:10px;

    line-height:1.5;
}

.success{
    margin-bottom:16px;

    padding:11px 12px;

    border-radius:9px;

    color:#86efac;

    background:rgba(34,197,94,.08);

    border:1px solid rgba(34,197,94,.20);

    font-size:10px;

    line-height:1.5;
}

.links{
    display:flex;
    justify-content:space-between;
    gap:10px;

    margin-top:17px;
}

.links a{
    color:#64748b;

    text-decoration:none;

    font-size:9px;

    font-weight:700;
}

.links a:hover{
    color:#60a5fa;
}

.security{
    margin-top:20px;

    padding-top:17px;

    border-top:1px solid rgba(148,163,184,.08);

    text-align:center;

    color:#475569;

    font-size:9px;

    letter-spacing:.3px;
}

.footer{
    text-align:center;

    margin-top:18px;

    color:#334155;

    font-size:8px;

    letter-spacing:1px;
}
"""


# =========================================================
# LOGIN PAGE
# =========================================================

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

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

        <h1>RS Trader</h1>

        <p>Professional Trading System</p>

    </div>


    <div class="card">

        <div class="card-icon">
            ◈
        </div>

        <h2>Welcome Back</h2>

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

            <a href="/register">
                CREATE ACCOUNT
            </a>

            <a href="/forgot-password">
                FORGOT PASSWORD?
            </a>

        </div>


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
# REGISTER PAGE
# =========================================================

REGISTER_HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

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

        <h1>RS Trader</h1>

        <p>Create Your Account</p>

    </div>


    <div class="card">

        <div class="card-icon">
            +
        </div>

        <h2>Create Account</h2>

        <div class="subtitle">
            Create your own username and password.
            Your activation code will be required next.
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
                    autocomplete="username"
                    maxlength="30"
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


        <div class="links">

            <a href="/login">
                ← BACK TO LOGIN
            </a>

        </div>


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
# ACTIVATION PAGE
# =========================================================

ACTIVATE_HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>RS Trader • Activation</title>

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

        <h1>RS Trader</h1>

        <p>Account Activation</p>

    </div>


    <div class="card">

        <div class="card-icon">
            🔐
        </div>

        <h2>Activate Your Account</h2>

        <div class="subtitle">
            Enter your unique activation code to unlock
            the RS Trader dashboard.
        </div>


        {% if error %}

        <div class="error">
            {{ error }}
        </div>

        {% endif %}


        <form method="POST">

            <div class="field">

                <label>
                    Activation Code
                </label>

                <input
                    class="input"
                    type="text"
                    name="code"
                    placeholder="RS-XXXX-XXXX-XXXX"
                    autocomplete="off"
                    required
                >

            </div>


            <button
                class="main-button"
                type="submit"
            >
                ACTIVATE ACCOUNT
            </button>

        </form>


        <div class="security">
            Each activation code belongs to one account only.
        </div>

    </div>

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
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>RS Trader • Reset Password</title>

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

        <h1>RS Trader</h1>

        <p>Password Recovery</p>

    </div>


    <div class="card">

        <div class="card-icon">
            ↻
        </div>

        <h2>Reset Password</h2>

        <div class="subtitle">
            Enter your username and your assigned activation code
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
                    autocomplete="username"
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
                    autocomplete="new-password"
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
                    autocomplete="new-password"
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


        <div class="links">

            <a href="/login">
                ← BACK TO LOGIN
            </a>

        </div>


        <div class="security">
            Your activation code remains assigned to your account.
        </div>

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


/* SUPPORT TELEGRAM */

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
    background:rgba(59,130,246,.17);

    border-color:rgba(59,130,246,.35);

    transform:translateY(-1px);
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

    box-shadow:0 5px 15px rgba(34,158,217,.25);
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

    background:rgba(34,197,94,.07);

    border:1px solid rgba(34,197,94,.16);

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

    box-shadow:0 0 12px #22c55e;
}


/* CARDS */

.cards{
    display:grid;

    grid-template-columns:repeat(4,1fr);

    gap:14px;

    margin-bottom:15px;
}

.card{
    background:rgba(15,23,42,.88);

    border:1px solid rgba(148,163,184,.09);

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

    border:1px solid rgba(59,130,246,.48);

    box-shadow:
        0 0 0 1px rgba(59,130,246,.05),
        0 15px 45px rgba(37,99,235,.15);
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

    background:rgba(239,68,68,.08);

    border:1px solid rgba(239,68,68,.20);

    font-size:10px;
}


/* STATUS */

.status-box{
    margin-bottom:15px;

    background:rgba(15,23,42,.88);

    border:1px solid rgba(148,163,184,.09);

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

    grid-template-columns:repeat(4,1fr);

    gap:12px;

    margin-bottom:15px;
}

.stat{
    background:rgba(15,23,42,.78);

    border:1px solid rgba(148,163,184,.07);

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

    border:1px solid rgba(148,163,184,.10);

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

    grid-template-columns:1fr 1fr;

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
    transform:translateY(-2px);

    filter:brightness(1.08);
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

    background:rgba(59,130,246,.10);

    border:1px solid rgba(59,130,246,.18);

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

    grid-template-columns:repeat(3,1fr);

    gap:16px;
}

.setting-field{
    padding:14px;

    border-radius:13px;

    background:rgba(8,13,24,.75);

    border:1px solid rgba(148,163,184,.08);
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

    border:1px solid #263449;

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
    padding:0 10px;

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

    border:1px solid #263449;
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
        grid-template-columns:1fr 1fr;
    }

    .stats{
        grid-template-columns:1fr 1fr;
    }

    .settings-grid{
        grid-template-columns:1fr 1fr;
    }

    .header-right{
        gap:6px;
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

            <h1>RS Trader</h1>

            <p>Money Management System</p>

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

            ${{ "%.2f"|format(calculator.total_profit_loss) }}

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


    <form method="POST" action="/trade">

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


    <form method="POST" action="/settings">

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


    <form method="POST" action="/reset">

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
        return redirect(url_for("login"))

    if not session.get("activated"):
        return redirect(url_for("activate"))

    return redirect(url_for("dashboard"))


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("logged_in") and session.get("activated"):
        return redirect(url_for("dashboard"))

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
            (username,)
        ).fetchone()

        conn.close()

        if (
            user
            and check_password_hash(
                user["password_hash"],
                password
            )
        ):

            session["logged_in"] = True
            session["username"] = user["username"]

            if user["activation_code"]:

                session["activated"] = True

                return redirect(
                    url_for("dashboard")
                )

            return redirect(
                url_for("activate")
            )

        return render_template_string(
            LOGIN_HTML,
            error="Invalid username or password.",
            success=None
        )

    return render_template_string(
        LOGIN_HTML,
        error=None,
        success=None
    )


# =========================================================
# CREATE ACCOUNT
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if session.get("logged_in"):
        return redirect(url_for("root"))

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

        if not valid_username(username):

            return render_template_string(
                REGISTER_HTML,
                error=(
                    "Username must be 3-30 characters and may "
                    "contain letters, numbers, _, - or ."
                )
            )

        if not valid_password(password):

            return render_template_string(
                REGISTER_HTML,
                error="Password must contain at least 6 characters."
            )

        if password != confirm_password:

            return render_template_string(
                REGISTER_HTML,
                error="Passwords do not match."
            )

        conn = get_db()

        existing = conn.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(username) = LOWER(?)
            """,
            (username,)
        ).fetchone()

        if existing:

            conn.close()

            return render_template_string(
                REGISTER_HTML,
                error="This username is already taken."
            )

        password_hash = generate_password_hash(
            password
        )

        conn.execute(
            """
            INSERT INTO users
            (username, password_hash)
            VALUES (?, ?)
            """,
            (
                username,
                password_hash
            )
        )

        conn.commit()
        conn.close()

        session["logged_in"] = True
        session["username"] = username
        session["activated"] = False

        return redirect(
            url_for("activate")
        )

    return render_template_string(
        REGISTER_HTML,
        error=None
    )


# =========================================================
# ACTIVATION
# =========================================================

@app.route("/activate", methods=["GET", "POST"])
def activate():

    if not session.get("logged_in"):
        return redirect(
            url_for("login")
        )

    username = session.get("username")

    if session.get("activated"):
        return redirect(
            url_for("dashboard")
        )

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
            (code,)
        ).fetchone()

        if row is None:

            conn.close()

            return render_template_string(
                ACTIVATE_HTML,
                error="Invalid activation code."
            )

        # Code already belongs to another account
        if (
            row["used"] == 1
            and row["owner_username"]
            and row["owner_username"] != username
        ):

            conn.close()

            return render_template_string(
                ACTIVATE_HTML,
                error="This activation code is already assigned to another account."
            )

        # Code is already assigned to current account
        if (
            row["used"] == 1
            and row["owner_username"] == username
        ):

            conn.close()

            session["activated"] = True

            return redirect(
                url_for("dashboard")
            )

        # Assign unused code to current account
        conn.execute(
            """
            UPDATE activation_codes
            SET used = 1,
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
        error=None
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

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

        if not username or not code:

            return render_template_string(
                FORGOT_HTML,
                error="Username and activation code are required.",
                success=None
            )

        if not valid_password(password):

            return render_template_string(
                FORGOT_HTML,
                error="New password must contain at least 6 characters.",
                success=None
            )

        if password != confirm_password:

            return render_template_string(
                FORGOT_HTML,
                error="Passwords do not match.",
                success=None
            )

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
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

        if user is None or activation is None:

            conn.close()

            return render_template_string(
                FORGOT_HTML,
                error="Username or activation code is incorrect.",
                success=None
            )

        new_hash = generate_password_hash(
            password
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

        return render_template_string(
            FORGOT_HTML,
            error=None,
            success=(
                "Password reset successfully. "
                "You can now sign in with your new password."
            )
        )

    return render_template_string(
        FORGOT_HTML,
        error=None,
        success=None
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():

        if not session.get("logged_in"):
            return redirect(
                url_for("login")
            )

        return redirect(
            url_for("activate")
        )

    return render_template_string(
        DASHBOARD_HTML,
        calculator=calculator,
        error=None,
        telegram_username=TELEGRAM_USERNAME,
        telegram_url=TELEGRAM_URL
    )


# =========================================================
# TRADE
# =========================================================

@app.route("/trade", methods=["POST"])
def trade():

    if not login_required():
        return redirect(
            url_for("login")
        )

    result = request.form.get(
        "result",
        ""
    ).upper()

    try:

        calculator.record_trade(result)

        return redirect(
            url_for("dashboard")
        )

    except (
        ValueError,
        RuntimeError
    ) as e:

        return render_template_string(
            DASHBOARD_HTML,
            calculator=calculator,
            error=str(e),
            telegram_username=TELEGRAM_USERNAME,
            telegram_url=TELEGRAM_URL
        )


# =========================================================
# SETTINGS
# =========================================================

@app.route("/settings", methods=["POST"])
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
    ) as e:

        return render_template_string(
            DASHBOARD_HTML,
            calculator=calculator,
            error=str(e),
            telegram_username=TELEGRAM_USERNAME,
            telegram_url=TELEGRAM_URL
        )


# =========================================================
# RESET
# =========================================================

@app.route("/reset", methods=["POST"])
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
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
       debug=False
    )
