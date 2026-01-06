import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)


def _send_email_sync(email_to: str, subject: str, html_content: str):
    """
    A robust, synchronous function to send an email using Python's smtplib.
    This is designed to be called from a synchronous environment like a Celery worker.
    """
    msg = MIMEMultipart()
    msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    try:
        # Connect to the SMTP server with a timeout to prevent hanging.
        with smtplib.SMTP(
            settings.MAIL_SERVER, settings.MAIL_PORT, timeout=15
        ) as server:
            server.starttls()  # Upgrade the connection to a secure one
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent successfully to {email_to}")
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {e}", exc_info=True)
        # Re-raising the exception is important so Celery knows the task failed.
        raise


def send_acknowledgement_email_sync(email_to: str, name: str):
    """
    Builds and sends the acknowledgement email synchronously.
    Sent immediately after a user creates a pending appointment request.
    """

    # You can customize the project name here or pull from settings
    project_name = settings.PROJECT_NAME
    contact_email = "support@neurohue.com"  # Example placeholder

    subject = f"We've Received Your Request - {project_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f6f8; color: #333333; }}
            .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .header {{ background-color: #2c3e50; padding: 30px 20px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px; font-weight: 500; }}
            .content {{ padding: 40px 30px; line-height: 1.6; color: #555555; }}
            .greeting {{ font-size: 20px; color: #2c3e50; margin-bottom: 20px; font-weight: 600; }}
            .status-box {{ background-color: #e8f4fd; border-left: 4px solid #3498db; padding: 15px; margin: 25px 0; border-radius: 4px; }}
            .status-text {{ color: #2980b9; font-weight: 600; margin: 0; }}
            .timeline {{ margin-top: 20px; }}
            .timeline-item {{ display: flex; align-items: flex-start; margin-bottom: 15px; }}
            .check {{ color: #27ae60; margin-right: 10px; font-weight: bold; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #999999; border-top: 1px solid #eaeaea; }}
            .footer a {{ color: #3498db; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{project_name}</h1>
            </div>

            <div class="content">
                <div class="greeting">Hi {name},</div>
                
                <p>Thank you for reaching out to us. We have successfully received your appointment request.</p>
                
                <div class="status-box">
                    <p class="status-text">Current Status: Pending Review</p>
                </div>

                <p>We know your time is valuable. Our administrative team is currently reviewing our schedule to find the best slot for you.</p>

                <div class="timeline">
                    <p><strong>What happens next?</strong></p>
                    <div class="timeline-item">
                        <span class="check">✓</span>
                        <span>Request Received</span>
                    </div>
                    <div class="timeline-item">
                        <span class="check" style="color: #ccc;">○</span>
                        <span>Administrative Review (5-7 Working Days)</span>
                    </div>
                    <div class="timeline-item">
                        <span class="check" style="color: #ccc;">○</span>
                        <span>Confirmation Email with Date & Time</span>
                    </div>
                </div>

                <p style="margin-top: 30px;">If you have any urgent questions in the meantime, please feel free to reply to this email.</p>
            </div>

            <div class="footer">
                <p>You received this email because you submitted a request at {project_name}.</p>
                <p>&copy; 2026 {project_name}. All rights reserved.<br>
                <a href="mailto:{contact_email}">Contact Support</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    _send_email_sync(email_to, subject, html_content)


def send_confirmation_email_sync(email_to: str, name: str, date_str: str):
    """
    Sent when admin confirms a pending request (Pending -> Upcoming).
    """
    project_name = settings.PROJECT_NAME
    contact_email = "support@neurohue.com"

    # 1. Format the date nicely (assuming ISO string input)
    # Input: "2026-01-12 10:30:00+00:00" -> Output: "Monday, 12 Jan 2026 at 10:30 AM"
    try:
        dt_obj = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        formatted_date = dt_obj.strftime("%A, %d %b %Y at %I:%M %p")
    except ValueError:
        formatted_date = str(date_str)  # Fallback if parsing fails

    subject = f"Appointment Confirmed - {project_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f6f8; color: #333; }}
            .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .header {{ background-color: #27ae60; padding: 30px; text-align: center; }} /* Green for Success */
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .details-card {{ background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 20px 0; }}
            .label {{ font-size: 12px; text-transform: uppercase; color: #888; letter-spacing: 0.5px; margin-bottom: 5px; }}
            .value {{ font-size: 18px; font-weight: 600; color: #2c3e50; margin-bottom: 15px; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Appointment Confirmed</h1>
            </div>
            <div class="content">
                <p style="font-size: 18px;">Hi {name},</p>
                <p>Great news! Your appointment request has been accepted. We look forward to seeing you.</p>
                
                <div class="details-card">
                    <div class="label">WHEN</div>
                    <div class="value">{formatted_date}</div>
                    
                    <div class="label">WHERE</div>
                    <div class="value">NeuroHue Clinic, Building A</div>
                    
                    <div class="label">DOCTOR / SPECIALIST</div>
                    <div class="value">Dr. Smith (Neuroscience Dept)</div>
                </div>

                <p>Please arrive 10 minutes early to complete any necessary paperwork.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 {project_name}.<br>Need to reschedule? <a href="mailto:{contact_email}">Contact Support</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    _send_email_sync(email_to, subject, html_content)


def send_followup_email_sync(email_to: str, name: str):
    """
    Sent when admin marks appointment as COMPLETED.
    """
    project_name = settings.PROJECT_NAME
    contact_email = "support@neurohue.com"
    feedback_link = "https://neurohue.com/feedback"  # Placeholder

    subject = f"Thank you for visiting - {project_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f6f8; color: #333; }}
            .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .header {{ background-color: #3498db; padding: 30px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; text-align: center; }}
            .message {{ font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 30px; }}
            .btn {{ display: inline-block; padding: 12px 24px; background-color: #3498db; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: bold; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Thank You!</h1>
            </div>
            <div class="content">
                <p class="message">Hi {name},</p>
                <p class="message">Thank you for visiting {project_name} today. We hope your appointment went smoothly and you received the care you needed.</p>
                
                <p class="message">Your feedback helps us improve. If you have a moment, we'd love to hear about your experience.</p>
                
                <a href="{feedback_link}" class="btn">Rate Your Experience</a>
            </div>
            <div class="footer">
                <p>&copy; 2026 {project_name}. All rights reserved.<br>
                Questions? <a href="mailto:{contact_email}">Contact Support</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    _send_email_sync(email_to, subject, html_content)


def send_booking_email_sync(email_to: str, name: str, date_str: str):
    """
    Sent when Admin manually schedules an appointment (creates as UPCOMING).
    """
    project_name = settings.PROJECT_NAME
    contact_email = "support@neurohue.com"

    # Format date
    try:
        dt_obj = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        formatted_date = dt_obj.strftime("%A, %d %b %Y at %I:%M %p")
    except ValueError:
        formatted_date = str(date_str)

    subject = f"Appointment Scheduled - {project_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f6f8; color: #333; }}
            .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .header {{ background-color: #3498db; padding: 30px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .details-card {{ background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 20px; margin: 20px 0; }}
            .value {{ font-size: 18px; font-weight: 600; color: #2c3e50; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Appointment Scheduled</h1>
            </div>
            <div class="content">
                <p>Hi {name},</p>
                <p>Our team has scheduled an appointment for you.</p>
                
                <div class="details-card">
                    <p style="margin:0; font-size:12px; color:#888;">DATE & TIME</p>
                    <p class="value" style="margin:5px 0 0 0;">{formatted_date}</p>
                </div>
                
                <p>If this time does not work for you, please contact us immediately.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 {project_name}. <a href="mailto:{contact_email}">Contact Support</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    _send_email_sync(email_to, subject, html_content)


def send_reschedule_email_sync(
    email_to: str, name: str, old_date_str: str, new_date_str: str
):
    """
    Sent when an appointment date is changed.
    """
    project_name = settings.PROJECT_NAME
    contact_email = "support@neurohue.com"

    # Format both dates
    def fmt(d):
        try:
            return datetime.fromisoformat(str(d).replace("Z", "+00:00")).strftime(
                "%d %b %Y, %I:%M %p"
            )
        except:
            return str(d)

    old_dt_fmt = fmt(old_date_str)
    new_dt_fmt = fmt(new_date_str)

    subject = f"Appointment Rescheduled - {project_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f6f8; color: #333; }}
            .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .header {{ background-color: #f39c12; padding: 30px; text-align: center; }} /* Orange for Change */
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .change-box {{ display: flex; align-items: center; justify-content: space-between; background-color: #fff8e1; padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid #ffe0b2; }}
            .date-group {{ width: 45%; }}
            .arrow {{ font-size: 24px; color: #f39c12; font-weight: bold; }}
            .label {{ font-size: 11px; text-transform: uppercase; color: #999; margin-bottom: 4px; }}
            .date-val {{ font-weight: 700; color: #444; font-size: 14px; }}
            .new-date {{ color: #d35400; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Appointment Updated</h1>
            </div>
            <div class="content">
                <p>Hi {name},</p>
                <p>Your appointment has been rescheduled to a new time.</p>
                
                <div class="change-box">
                    <div class="date-group">
                        <div class="label">PREVIOUSLY</div>
                        <div class="date-val" style="text-decoration: line-through; color: #999;">{old_dt_fmt}</div>
                    </div>
                    <div class="arrow">&rarr;</div>
                    <div class="date-group" style="text-align: right;">
                        <div class="label">NEW TIME</div>
                        <div class="date-val new-date">{new_dt_fmt}</div>
                    </div>
                </div>
                
                <p>We apologize for any inconvenience. Please mark your calendar for the new time.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 {project_name}. <a href="mailto:{contact_email}">Contact Support</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    _send_email_sync(email_to, subject, html_content)


def send_rejection_email_sync(email_to: str, name: str, reason: str):
    """
    Sent when Admin rejects a PENDING request.
    """
    project_name = settings.PROJECT_NAME
    contact_email = "support@neurohue.com"
    
    subject = f"Update on your request - {project_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f6f8; color: #333; }}
            .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .header {{ background-color: #7f8c8d; padding: 30px; text-align: center; }} /* Grey for Rejection (Neutral) */
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .reason-box {{ background-color: #f8f9fa; border-left: 4px solid #95a5a6; padding: 15px; margin: 20px 0; font-style: italic; color: #555; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Request Declined</h1>
            </div>
            <div class="content">
                <p>Hi {name},</p>
                <p>Thank you for your interest in {project_name}. After reviewing your request, we regret to inform you that we cannot schedule your appointment at this time.</p>
                
                <p><strong>Reason:</strong></p>
                <div class="reason-box">
                    "{reason}"
                </div>
                
                <p>You are welcome to submit a new request in the future or contact us for more details.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 {project_name}. <a href="mailto:{contact_email}">Contact Support</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    _send_email_sync(email_to, subject, html_content)


def send_cancellation_email_sync(email_to: str, name: str, reason: str):
    """
    Sent when an UPCOMING appointment is Cancelled.
    """
    project_name = settings.PROJECT_NAME
    contact_email = "support@neurohue.com"
    
    subject = f"Appointment Cancelled - {project_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f6f8; color: #333; }}
            .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .header {{ background-color: #e74c3c; padding: 30px; text-align: center; }} /* Red for Cancel */
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .alert-box {{ background-color: #fdedec; border: 1px solid #fadbd8; color: #c0392b; padding: 15px; border-radius: 6px; margin: 20px 0; text-align: center; font-weight: bold; }}
            .reason-label {{ font-size: 12px; text-transform: uppercase; color: #888; margin-top: 20px; }}
            .reason-text {{ font-size: 16px; color: #333; margin-top: 5px; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Appointment Cancelled</h1>
            </div>
            <div class="content">
                <p>Hi {name},</p>
                
                <div class="alert-box">
                    This appointment has been cancelled.
                </div>
                
                <p>We are writing to confirm that your upcoming appointment with {project_name} has been cancelled as per your request or administrative action.</p>
                
                <div class="reason-label">REASON FOR CANCELLATION</div>
                <div class="reason-text">{reason}</div>
                
                <p style="margin-top: 30px;">If this was a mistake, or if you would like to reschedule, please contact us immediately.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 {project_name}. <a href="mailto:{contact_email}">Contact Support</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    _send_email_sync(email_to, subject, html_content)