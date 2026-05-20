import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
from icalendar import Calendar, Event
import uuid
from app.core.config import settings


def _get_smtp_connection():
    """
    Creates and returns an authenticated Gmail SMTP connection.
    Caller is responsible for closing it.
    """
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(settings.GMAIL_SENDER, settings.GMAIL_APP_PASSWORD)
    return server

def _build_ics_attachment(
    candidate_name: str,
    job_title: str,
    interview_slot_start: datetime,
    interview_slot_end: datetime,
    meet_url: str
) -> bytes:
    """
    Builds an ICS calendar file as bytes.
    When candidate opens this attachment, their calendar app
    (Google Calendar / Outlook / Apple Calendar) adds the event automatically.
    No API required — pure icalendar library.
    """
    cal = Calendar()
    cal.add("prodid", "-//TalentWeave//Recruitment//EN")
    cal.add("version", "2.0")
    cal.add("method", "REQUEST")
 
    event = Event()
    event.add("summary", f"Interview — {job_title} | TalentWeave")
    event.add("dtstart", interview_slot_start)
    event.add("dtend", interview_slot_end)
    event.add(
        "description",
        f"Dear {candidate_name},\n\nYour interview for {job_title} is confirmed.\n\nJoin here: {meet_url}"
    )
    event.add("location", meet_url)
    event.add("uid", str(uuid.uuid4()))
    event.add("status", "CONFIRMED")
 
    cal.add_component(event)
    return cal.to_ical()


def send_interview_email(
    candidate_name: str,
    candidate_email: str,
    job_title: str,
    interview_slot_start: str,
    interview_slot_end: str,
    meet_url: str
):
    """
    Sends interview invitation email to a passing candidate.
    Called by scheduler after screening deadline fires (no-assignment path).
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Interview Invitation — {job_title} | TalentWeave"
        msg["From"] = settings.GMAIL_SENDER
        msg["To"] = candidate_email
        
        # Format times for human-readable body
        start_str = interview_slot_start.strftime("%A, %B %d %Y at %I:%M %p")
        end_str = interview_slot_end.strftime("%I:%M %p")

        body = f"""
Dear {candidate_name},

Congratulations! You have successfully passed the screening exam for the position of {job_title}.

We would like to invite you for an interview. Here are your details:

Date & Time : {start_str} to {end_str}
Google Meet : {meet_url}

A calendar invite is attached - open it to add this event directly to your calendar.
Please join the meeting on time. If you have any questions, reply to this email.

Best regards,
TalentWeave Recruitment Team
        """.strip()

        msg.attach(MIMEText(body, "plain"))


        # Attach ICS calendar file
        ics_bytes = _build_ics_attachment(
            candidate_name=candidate_name,
            job_title=job_title,
            interview_slot_start=interview_slot_start,
            interview_slot_end=interview_slot_end,
            meet_url=meet_url
        )
 
        ics_attachment = MIMEBase("text", "calendar", method="REQUEST", name="interview.ics")
        ics_attachment.set_payload(ics_bytes)
        encoders.encode_base64(ics_attachment)
        ics_attachment.add_header("Content-Disposition", "attachment; filename=interview.ics")
        msg.attach(ics_attachment)

        
        server = _get_smtp_connection()
        server.sendmail(settings.GMAIL_SENDER, candidate_email, msg.as_string())
        server.quit()

        print(f"✅ Interview email sent to {candidate_email}")

    except Exception as e:
        print(f"❌ Failed to send interview email to {candidate_email}: {e}")


def send_assignment_email(
    candidate_name: str,
    candidate_email: str,
    job_title: str,
    job_id: int,
    assignment_pdf_path: str
):
    """
    Sends assignment email with PDF attached.
    Called by scheduler after screening deadline fires (assignment path).
    PDF is read from disk using the path stored in jobs.assignment_pdf_path.
    """
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"Assignment — {job_title} | TalentWeave"
        msg["From"] = settings.GMAIL_SENDER
        msg["To"] = candidate_email

        submission_url = f"http://localhost:8000/static/assignment_submit.html?job_id={job_id}"

        body = f"""
Dear {candidate_name},

Congratulations on passing the screening exam for {job_title}!

Please find your assignment attached to this email.

Complete the assignment and submit your work here:
{submission_url}

You will need to provide:
- Your GitHub repository link
- Your LinkedIn profile
- Deployment URL (if applicable)
- Any additional notes

Please submit before the assignment deadline.

Best regards,
TalentWeave Recruitment Team
        """.strip()

        msg.attach(MIMEText(body, "plain"))

        # Attach PDF from disk
        pdf_path = Path(assignment_pdf_path)
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(pdf_bytes)
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                f"attachment; filename=assignment_{job_id}.pdf"
            )
            msg.attach(attachment)
        else:
            print(f"⚠️ Assignment PDF not found at {assignment_pdf_path} — sending email without attachment.")

        server = _get_smtp_connection()
        server.sendmail(settings.GMAIL_SENDER, candidate_email, msg.as_string())
        server.quit()

        print(f"✅ Assignment email sent to {candidate_email}")

    except Exception as e:
        print(f"❌ Failed to send assignment email to {candidate_email}: {e}")


def send_meet_link_email(
    candidate_name: str,
    candidate_email: str,
    job_title: str,
    meet_url: str
):
    """
    Sends a simple Meet link email.
    Used for manual trigger from Streamlit ops dashboard (Step 7).
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your Interview Link — {job_title} | TalentWeave"
        msg["From"] = settings.GMAIL_SENDER
        msg["To"] = candidate_email

        body = f"""
Dear {candidate_name},

Your interview for {job_title} has been scheduled.

Join here: {meet_url}

Please be ready 5 minutes before your scheduled time.

Best regards,
TalentWeave Recruitment Team
        """.strip()

        msg.attach(MIMEText(body, "plain"))

        server = _get_smtp_connection()
        server.sendmail(settings.GMAIL_SENDER, candidate_email, msg.as_string())
        server.quit()

        print(f"✅ Meet link email sent to {candidate_email}")

    except Exception as e:
        print(f"❌ Failed to send meet link email to {candidate_email}: {e}")


def test_email_connection():
    """
    Sends a test email to the sender themselves.
    Call this once manually to verify Gmail SMTP is working.
    Run: python -c "from app.services.email_service import test_email_connection; test_email_connection()"
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "TalentWeave — Email Service Test"
        msg["From"] = settings.GMAIL_SENDER
        msg["To"] = settings.GMAIL_SENDER

        body = """
This is a test email from TalentWeave.
If you received this, Gmail SMTP is working correctly.
        """.strip()

        msg.attach(MIMEText(body, "plain"))

        server = _get_smtp_connection()
        server.sendmail(settings.GMAIL_SENDER, settings.GMAIL_SENDER, msg.as_string())
        server.quit()

        print("✅ Test email sent successfully. Check your inbox.")

    except Exception as e:
        print(f"❌ Test email failed: {e}")