import threading
import requests
import json
import os
import base64
from config import Config
from utils.logger import log_info, log_error, log_success

def send_offer_letter_email_async(to_email, student_name, internship_title, pdf_path):
    """
    Asynchronously sends offer letter email with PDF attachment via Resend API.
    """
    def _send():
        try:
            if not Config.RESEND_API_KEY:
                log_info(f"[EMAIL MOCK] Offer Letter email queued for {to_email} ({internship_title}). Resend API key not set.")
                return

            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {Config.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            
            attachments = []
            if pdf_path and os.path.exists(pdf_path):
                try:
                    with open(pdf_path, 'rb') as f:
                        b64_content = base64.b64encode(f.read()).decode('utf-8')
                    filename = os.path.basename(pdf_path)
                    attachments.append({
                        "filename": filename,
                        "content": b64_content
                    })
                except Exception as ex:
                    log_error(f"Failed to encode offer letter PDF attachment: {ex}")
            
            payload = {
                "from": Config.FROM_EMAIL,
                "to": [to_email],
                "subject": f"🎉 Official Offer Letter: {internship_title} - Web Intern",
                "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                        <h2 style="color: #1e3a8a;">Welcome to Web Intern Platform!</h2>
                        <p>Dear <b>{student_name}</b>,</p>
                        <p>We are delighted to accept your application for the <b>{internship_title}</b> 4-Week Virtual Internship Program.</p>
                        <p>Your official <b>Offer Letter (PDF)</b> has been attached to this email and is also available for direct download in your student dashboard.</p>
                        <div style="background-color: #f8fafc; padding: 15px; border-left: 4px solid #2563eb; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold;">Next Steps:</p>
                            <ol style="margin-top: 5px; padding-left: 20px;">
                                <li>Log into your Web Intern Dashboard.</li>
                                <li>Access your weekly 4-module task workspace.</li>
                                <li>Submit your weekly project deliverables (PDF format).</li>
                            </ol>
                        </div>
                        <p>If you have any questions, feel free to reply to this email at <a href="mailto:{Config.SUPPORT_EMAIL}">{Config.SUPPORT_EMAIL}</a>.</p>
                        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;"/>
                        <p style="font-size: 12px; color: #64748b;">Web Intern Academic Board & Technical Directorate | ISO Certified MSME Entity</p>
                    </div>
                """,
                "attachments": attachments if attachments else None
            }
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

            response = requests.post(url, headers=headers, json=payload, timeout=12)
            if response.status_code in (200, 201):
                log_success(f"Offer Letter email sent successfully via Resend API to {to_email}")
            elif response.status_code == 403 and "onboarding@resend.dev" not in payload.get("from", ""):
                # Retry with default Resend verified sender
                payload["from"] = "onboarding@resend.dev"
                res_retry = requests.post(url, headers=headers, json=payload, timeout=12)
                if res_retry.status_code in (200, 201):
                    log_success(f"Offer Letter email sent successfully (via onboarding@resend.dev fallback) to {to_email}")
                else:
                    log_error(f"Resend API error (retry): {res_retry.text}")
            else:
                log_error(f"Resend API error sending Offer Letter: {response.text}")

        except Exception as e:
            log_error(f"Failed to send Offer Letter email to {to_email}: {e}")

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()


def send_certificate_email_async(to_email, student_name, internship_title, cert_id, pdf_path):
    """
    Asynchronously sends official Verified Certificate email with PDF attachment via Resend API.
    """
    def _send():
        try:
            if not Config.RESEND_API_KEY:
                log_info(f"[EMAIL MOCK] Certificate email queued for {to_email} ({internship_title}). Resend API key not set.")
                return

            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {Config.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            
            attachments = []
            if pdf_path and os.path.exists(pdf_path):
                try:
                    with open(pdf_path, 'rb') as f:
                        b64_content = base64.b64encode(f.read()).decode('utf-8')
                    attachments.append({
                        "filename": f"Certificate_{cert_id}.pdf",
                        "content": b64_content
                    })
                except Exception as ex:
                    log_error(f"Failed to encode certificate PDF attachment: {ex}")
            
            payload = {
                "from": Config.FROM_EMAIL,
                "to": [to_email],
                "subject": f"🎓 Official Verified Certificate: {internship_title} - Web Intern",
                "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                        <h2 style="color: #d97706;">Congratulations on Your Graduation!</h2>
                        <p>Dear <b>{student_name}</b>,</p>
                        <p>We are thrilled to inform you that you have successfully completed your <b>{internship_title}</b> Virtual Internship Program!</p>
                        <p>Your official <b>MSME & ISO Certified Certificate of Completion</b> (Credential ID: <code>{cert_id}</code>) is attached to this email.</p>
                        <div style="background-color: #fffbe6; padding: 15px; border-left: 4px solid #d97706; margin: 20px 0;">
                            <p style="margin: 0; font-weight: bold; color: #b45309;">Verified Digital Credential</p>
                            <p style="margin: 5px 0 0 0; font-size: 14px;">Your certificate features a unique QR verification code. Employers & institutions can instantly verify your credentials at <a href="{Config.APP_URL}/#/verify/{cert_id}">{Config.APP_URL}/#/verify/{cert_id}</a>.</p>
                        </div>
                        <p>Best regards,<br/><b>Web Intern Academic Board & Certification Directorate</b></p>
                        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;"/>
                        <p style="font-size: 12px; color: #64748b;">Web Intern Platform | Support: {Config.SUPPORT_EMAIL}</p>
                    </div>
                """,
                "attachments": attachments if attachments else None
            }
            payload = {k: v for k, v in payload.items() if v is not None}

            response = requests.post(url, headers=headers, json=payload, timeout=12)
            if response.status_code in (200, 201):
                log_success(f"Certificate email sent successfully via Resend API to {to_email}")
            elif response.status_code == 403 and "onboarding@resend.dev" not in payload.get("from", ""):
                payload["from"] = "onboarding@resend.dev"
                res_retry = requests.post(url, headers=headers, json=payload, timeout=12)
                if res_retry.status_code in (200, 201):
                    log_success(f"Certificate email sent successfully (via onboarding@resend.dev fallback) to {to_email}")
                else:
                    log_error(f"Resend API error (retry): {res_retry.text}")
            else:
                log_error(f"Resend API error sending Certificate: {response.text}")

        except Exception as e:
            log_error(f"Failed to send Certificate email to {to_email}: {e}")

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()


