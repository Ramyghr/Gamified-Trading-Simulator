import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings
import logging
import asyncio
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

logger = logging.getLogger(__name__)

class EmailUtil:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

    def decode_access_token(token: str = Depends(oauth2_scheme)):
        """
        Decode and verify a JWT access token.
        Returns the decoded payload if valid.
        Raises HTTP 401 if invalid or expired.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
            )
    async def send_email(self, to_email: str, subject: str, body: str):
        if not all([settings.SMTP_SERVER, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]):
            logger.warning("Email configuration missing. Would send email to %s: %s", to_email, subject)
            return

        try:
            message = MIMEMultipart()
            message["From"] = settings.SMTP_USERNAME
            message["To"] = to_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "html"))

            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_SERVER,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            logger.info("Email sent successfully to %s", to_email)
        except Exception as e:
            logger.error("Failed to send email to %s: %s", to_email, str(e))

    def send_verification_email(self, to_email: str, verification_token: str):
        verification_link = f"http://127.0.0.1:8000/verify-email?token={verification_token}"
        subject = "Verify Your Email - Trading Simulator"
        body = f"""
        <html>
            <body>
                <h2>Welcome to Trading Simulator!</h2>
                <p>Please verify your email address by clicking the link below:</p>
                <a href="{verification_link}" style="
                    background-color: #007bff; 
                    color: white; 
                    padding: 10px 20px; 
                    text-decoration: none; 
                    border-radius: 5px;
                    display: inline-block;
                    margin: 10px 0;
                ">Verify Email</a>
                <p>Or copy and paste this link in your browser:</p>
                <p>{verification_link}</p>
                <p>This link will expire in 30 minutes.</p>
            </body>
        </html>
        """
        asyncio.create_task(self.send_email(to_email, subject, body))

    def send_password_reset_email(self, to_email: str, reset_token: str):
        subject = "Reset Your Password - Trading Simulator"
        body = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>You requested to reset your password. Use the following token to reset it via the API:</p>
                <p><b>Token:</b> {reset_token}</p>
                <p>Send a POST request to <code>http://127.0.0.1:8000/user/reset-password</code> with this JSON body:</p>
                <pre>{{
  "token": "{reset_token}",
  "new_password": "YOUR_NEW_PASSWORD"
}}</pre>
                <p>This token will expire in 30 minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """
        asyncio.create_task(self.send_email(to_email, subject, body))