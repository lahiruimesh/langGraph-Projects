import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from json import loads
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

def send_email_alert(fresh_jobs: List[Dict[str, Any]]):
    """
    Send the newly discovered jobs to all recipients as a formatted HTML table.
    """
    if not fresh_jobs:
        print("No fresh jobs to notify.")
        return

    print("Preparing email alert for fresh opportunities...")
    
    # 1. Read credentials from environment variables.
    sender_email = os.getenv("EMAIL_SENDER")
    # Use a Google App Password here, not your regular account password.
    sender_password = os.getenv("EMAIL_PASSWORD") 
    
    # EMAIL_RECEIVERS should be a JSON list such as ["a@example.com", "b@example.com"].
    try:
        receivers = loads(os.getenv("EMAIL_RECEIVERS", "[]"))
    except Exception:
        print("Error parsing EMAIL_RECEIVERS from .env. Make sure it is a valid JSON list.")
        return

    if not sender_email or not sender_password or not receivers:
        print("Email credentials or receivers list missing in the .env file.")
        return

    # 2. Build the HTML table dynamically.
    table_rows = ""
    for job in fresh_jobs:
        title = job.get("job_title", "N/A")
        source = job.get("company_source", "#")
        skills = ", ".join(job.get("skills", []))
        
        table_rows += f"""
        <tr>
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold; color: #1e293b;">{title}</td>
            <td style="padding: 12px; border: 1px solid #ddd; color: #475569; font-size: 14px;">{skills}</td>
            <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">
                <a href="{source}" style="background-color: #0080FF; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: bold;">Apply</a>
            </td>
        </tr>
        """

    # 3. Build the full HTML email body.
    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; padding: 24px; margin: 0;">
        <div style="max-width: 700px; background-color: #ffffff; margin: 0 auto; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="background-color: #0080FF; padding: 28px; text-align: center; color: #ffffff;">
                <h1 style="margin: 0; font-size: 24px; letter-spacing: 1px;">CareerSpy AI Alert</h1>
                <p style="margin: 5px 0 0 0; color: #ffffff; font-size: 14px;">Autonomous Job Hunter Network Found New Matches!</p>
            </div>
            <div style="padding: 24px;">
                <p style="color: #334155; font-size: 16px;">Hey Team,</p>
                <p style="color: #475569; font-size: 15px; line-height: 1.5;">Our background AI agents just crawled your target career portals and discovered <b>{len(fresh_jobs)} new vacancies</b> matching your tech stack profiles. Check them out below:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <thead>
                        <tr style="background-color: #f1f5f9;">
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: left; color: #1e293b;">Job Title</th>
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: left; color: #1e293b;">Required Skills</th>
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: center; color: #1e293b;">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                <p style="color: #94a3b8; font-size: 12px; text-align: center; margin: 0;">This is an automated production run by CareerSpy AI Framework.<br>Hosted serverless via GitHub Actions Cloud Runners.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # 4. Send the email over SMTP.
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"CareerSpy AI - {len(fresh_jobs)} New Tech Vacancies Discovered!"
        msg['From'] = sender_email
        msg['To'] = ", ".join(receivers)
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Connect to Gmail SMTP using TLS on port 587.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Send the email.
        server.sendmail(sender_email, receivers, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {len(receivers)} receivers!")
        
    except Exception as e:
        print(f"Failed to send email alerts: {e}")