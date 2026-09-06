import os
import sqlite3
import secrets
import hashlib
import hmac
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

DB_FILE = "weathergpt.db"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)

OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
OTP_COOLDOWN_SECONDS = int(os.getenv("OTP_COOLDOWN_SECONDS", "60"))


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            google_id TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_tables()


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OTPRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class GoogleRequest(BaseModel):
    credential: str


def hash_password(password):
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        210000
    )

    return salt.hex() + ":" + password_hash.hex()


def verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split(":")

        salt = bytes.fromhex(salt_hex)

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            210000
        )

        return hmac.compare_digest(
            new_hash.hex(),
            hash_hex
        )

    except Exception:
        return False


def hash_otp(otp):
    return hashlib.sha256(
        otp.encode()
    ).hexdigest()


def create_session(response, user):
    session_data = f"{user['id']}:{secrets.token_urlsafe(32)}"

    response.set_cookie(
        key="weathergpt_session",
        value=session_data,
        httponly=True,
        samesite="none",
        secure=True,
        max_age=60 * 60 * 24 * 7
    )


def send_email_otp(email, otp):

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="SMTP email settings are not configured in .env"
        )

    message = EmailMessage()

    message["Subject"] = "WeatherGPT - Email Verification OTP"
    message["From"] = SMTP_FROM
    message["To"] = email

    message.set_content(
        f"""
WeatherGPT Email Verification

Your verification OTP is:

{otp}

This OTP will expire in {OTP_EXPIRY_MINUTES} minutes.

If you did not request this code, please ignore this email.

WeatherGPT India
"""
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:

            server.starttls()

            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            server.send_message(message)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to send OTP email: {str(e)}"
        )


@router.post("/register")
def register(data: RegisterRequest):

    if len(data.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters"
        )

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (data.email,)
    ).fetchone()

    if existing:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    password_hash = hash_password(data.password)

    now = datetime.now(
        timezone.utc
    ).isoformat()

    cursor = conn.execute(
        """
        INSERT INTO users
        (name, email, password_hash, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            data.name,
            data.email,
            password_hash,
            now
        )
    )

    conn.commit()

    user_id = cursor.lastrowid

    conn.close()

    return {
        "message": "Account created successfully",
        "user": {
            "id": user_id,
            "name": data.name,
            "email": data.email
        }
    }


@router.post("/login")
def login(
    data: LoginRequest,
    response: Response
):

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (data.email,)
    ).fetchone()

    conn.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user["password_hash"]:

        raise HTTPException(
            status_code=401,
            detail="This account uses Google login"
        )

    if not verify_password(
        data.password,
        user["password_hash"]
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    create_session(
        response,
        user
    )

    return {
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    }


@router.post("/send-otp")
def send_otp(data: OTPRequest):

    email = data.email

    conn = get_db()

    last_otp = conn.execute(
        """
        SELECT created_at
        FROM otps
        WHERE email = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (email,)
    ).fetchone()

    if last_otp:

        created_time = datetime.fromisoformat(
            last_otp["created_at"]
        )

        current_time = datetime.now(
            timezone.utc
        )

        difference = (
            current_time - created_time
        ).total_seconds()

        if difference < OTP_COOLDOWN_SECONDS:

            conn.close()

            remaining = int(
                OTP_COOLDOWN_SECONDS - difference
            )

            raise HTTPException(
                status_code=429,
                detail=f"Please wait {remaining} seconds before requesting another OTP"
            )

    otp = str(
        secrets.randbelow(900000) + 100000
    )

    otp_hash = hash_otp(otp)

    now = datetime.now(
        timezone.utc
    )

    expires = (
        now +
        timedelta(
            minutes=OTP_EXPIRY_MINUTES
        )
    )

    conn.execute(
        """
        INSERT INTO otps
        (email, otp_hash, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            email,
            otp_hash,
            expires.isoformat(),
            now.isoformat()
        )
    )

    conn.commit()
    conn.close()

    send_email_otp(
        email,
        otp
    )

    return {
        "message": "OTP sent successfully"
    }


@router.post("/verify-otp")
def verify_otp(
    data: VerifyOTPRequest,
    response: Response
):

    conn = get_db()

    otp_record = conn.execute(
        """
        SELECT *
        FROM otps
        WHERE email = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (data.email,)
    ).fetchone()

    if not otp_record:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="OTP not found. Please request a new OTP."
        )

    expires_at = datetime.fromisoformat(
        otp_record["expires_at"]
    )

    if datetime.now(
        timezone.utc
    ) > expires_at:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="OTP has expired. Please request a new OTP."
        )

    if not hmac.compare_digest(
        hash_otp(data.otp),
        otp_record["otp_hash"]
    ):

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (data.email,)
    ).fetchone()

    if not user:

        now = datetime.now(
            timezone.utc
        ).isoformat()

        cursor = conn.execute(
            """
            INSERT INTO users
            (name, email, created_at)
            VALUES (?, ?, ?)
            """,
            (
                data.email.split("@")[0],
                data.email,
                now
            )
        )

        conn.commit()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        ).fetchone()

    conn.execute(
        "DELETE FROM otps WHERE email = ?",
        (data.email,)
    )

    conn.commit()
    conn.close()

    create_session(
        response,
        user
    )

    return {
        "message": "OTP verified successfully",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    }


@router.post("/google")
def google_login(
    data: GoogleRequest,
    response: Response
):

    if not GOOGLE_CLIENT_ID:

        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID is not configured in .env"
        )

    try:

        google_user = id_token.verify_oauth2_token(
            data.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid Google login token"
        )

    google_id = google_user.get("sub")
    email = google_user.get("email")
    name = google_user.get("name")

    if not email:

        raise HTTPException(
            status_code=400,
            detail="Google account email was not provided"
        )

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    if not user:

        now = datetime.now(
            timezone.utc
        ).isoformat()

        cursor = conn.execute(
            """
            INSERT INTO users
            (name, email, google_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                name or email.split("@")[0],
                email,
                google_id,
                now
            )
        )

        conn.commit()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        ).fetchone()

    else:

        if not user["google_id"]:

            conn.execute(
                """
                UPDATE users
                SET google_id = ?
                WHERE id = ?
                """,
                (
                    google_id,
                    user["id"]
                )
            )

            conn.commit()

            user = conn.execute(
                """
                SELECT *
                FROM users
                WHERE id = ?
                """,
                (user["id"],)
            ).fetchone()

    conn.close()

    create_session(
        response,
        user
    )

    return {
        "message": "Google login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    }


@router.post("/logout")
def logout(response: Response):

    response.delete_cookie(
        key="weathergpt_session"
    )

    return {
        "message": "Logged out successfully"
    }