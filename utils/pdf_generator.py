import os
import uuid
import datetime
import qrcode
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from config import Config
from utils.logger import log_info, log_error

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'static', 'assets')

WEBINTERN_LOGO_PATH = os.path.join(ASSETS_DIR, 'webintern_unique_logo.png')
MSME_LOGO_PATH = os.path.join(ASSETS_DIR, 'msme_logo.png')
VERIFIED_BADGE_PATH = os.path.join(ASSETS_DIR, 'verified_badge.jpg')
FOUNDER_SIG_PATH = os.path.join(ASSETS_DIR, 'founder_sig_clean.png')

def generate_qr_code_file(url):
    """
    Generates a dynamic QR code PNG image file pointing to the verification URL.
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F172A", back_color="white")
        
        qr_dir = os.path.join(Config.UPLOAD_FOLDER, 'temp_qrs')
        os.makedirs(qr_dir, exist_ok=True)
        qr_path = os.path.join(qr_dir, f"qr_{uuid.uuid4().hex[:8]}.png")
        img.save(qr_path)
        return qr_path
    except Exception as e:
        log_error(f"Failed to generate QR code: {e}")
        return None

class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas drawing executive borders per document type (Royal Blue/Gold Banners for Offer Letter, Dual Gold/Navy Frame & Corner Ornaments for Certificate)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations()
            super().showPage()
        super().save()

    def draw_page_decorations(self):
        self.saveState()
        width, height = self._pagesize
        
        if width > height:
            # Full Color Executive Certificate Frame (Landscape)
            # Outer Gold Accent Border
            self.setStrokeColor(colors.HexColor('#D97706'))
            self.setLineWidth(3.5)
            self.rect(14, 14, width - 28, height - 28)
            
            # Inner Royal Navy Border
            self.setStrokeColor(colors.HexColor('#1E3A8A'))
            self.setLineWidth(1.5)
            self.rect(19, 19, width - 38, height - 38)

            # Executive Corner Ornaments (Gold Corner Lines)
            self.setStrokeColor(colors.HexColor('#D97706'))
            self.setLineWidth(2.0)
            # Top-Left
            self.line(24, height - 24, 40, height - 24)
            self.line(24, height - 24, 24, height - 40)
            # Top-Right
            self.line(width - 24, height - 24, width - 40, height - 24)
            self.line(width - 24, height - 24, width - 24, height - 40)
            # Bottom-Left
            self.line(24, 24, 40, 24)
            self.line(24, 24, 24, 40)
            # Bottom-Right
            self.line(width - 24, 24, width - 40, 24)
            self.line(width - 24, 24, width - 24, 40)
        else:
            # Executive Corporate Offer Letter Banners (Portrait)
            # Top Royal Navy Header Bar
            self.setFillColor(colors.HexColor('#1E3A8A'))
            self.rect(0, height - 8, width, 8, fill=1, stroke=0)
            # Top Gold Accent Ribbon
            self.setFillColor(colors.HexColor('#D97706'))
            self.rect(0, height - 11, width, 3, fill=1, stroke=0)
            # Bottom Dark Slate Footer Bar
            self.setFillColor(colors.HexColor('#0F172A'))
            self.rect(0, 0, width, 5, fill=1, stroke=0)
            
        self.restoreState()


def generate_offer_letter_pdf(student_name, email, internship_title, start_date, end_date, doc_number, guide_name="Dr. A. K. Sharma (Technical Director)"):
    """
    Generates an Ultra-Formal Executive Corporate Offer Letter PDF.
    Features: Royal Blue & Gold Banners, Styled Program Summary Box, Official MSME Logo, WebIntern Logo, Founder Signature, and Dynamic QR Code.
    """
    file_name = f"{doc_number}.pdf"
    file_path = os.path.join(Config.OFFER_LETTERS_DIR, file_name)
    
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitleBW',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#0F172A'),
        alignment=0
    )

    body_style = ParagraphStyle(
        'BodyBW',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor('#1E293B')
    )

    bold_body_style = ParagraphStyle(
        'BoldBodyBW',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor('#0F172A')
    )

    story = []
    
    # Dynamic student verification QR code
    verify_url = f"https://webintern.in/#/verify/{doc_number}"
    qr_file_path = generate_qr_code_file(verify_url)
    
    logo_img = RLImage(WEBINTERN_LOGO_PATH, width=135, height=40) if os.path.exists(WEBINTERN_LOGO_PATH) else Paragraph("<b>WEB INTERN</b>", title_style)
    msme_img = RLImage(MSME_LOGO_PATH, width=135, height=38) if os.path.exists(MSME_LOGO_PATH) else Paragraph("<b>MSME INDIA</b>", bold_body_style)
    
    # 1. Header Table (Perfect Logo Placement & Title "INTERNSHIP OFFER LETTER")
    header_data = [
        [
            logo_img,
            msme_img,
            Paragraph(f"<b>INTERNSHIP OFFER LETTER</b><br/><font size=8 color='#1E3A8A'><b>WEB INTERN PLATFORM</b></font><br/><font size=7.5 color='#475569'>Ref: {doc_number}<br/>Date: {datetime.date.today().strftime('%B %d, %Y')}</font>", ParagraphStyle('RHeadBW', alignment=2, fontName='Helvetica', fontSize=8.5, leading=12))
        ]
    ]
    header_table = Table(header_data, colWidths=[160, 150, 210])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph("<hr color='#1E3A8A' size=1.5/>", body_style))
    story.append(Spacer(1, 10))
    
    # 2. Recipient Details & Subject Line
    story.append(Paragraph(f"<b>To,</b><br/><b>{student_name}</b><br/><font color='#475569'>{email}</font>", bold_body_style))
    story.append(Spacer(1, 10))
    
    subject_text = f"<b>Subject: INTERNSHIP OFFER LETTER — {internship_title}</b>"
    story.append(Paragraph(subject_text, ParagraphStyle('SubjStyle', parent=bold_body_style, fontSize=10.5, textColor=colors.HexColor('#1E3A8A'))))
    story.append(Spacer(1, 10))
    
    # 3. Formal Offer Letter Paragraphs & Styled Summary Box
    p1 = (
        f"Dear <b>{student_name}</b>,<br/><br/>"
        f"We are pleased to offer you an appointment for the <b>4-Week Virtual Internship Program</b> in <b>{internship_title}</b> at <b>Web Intern Platform</b>. "
        f"Following the evaluation of your academic profile and credentials, the Selection Board is confident in your ability to contribute effectively to our enterprise projects."
    )
    story.append(Paragraph(p1, body_style))
    story.append(Spacer(1, 10))

    # Styled Program Details Summary Box
    summary_data = [
        [
            Paragraph("<b>INTERNSHIP PROGRAM SPECIFICATIONS</b>", ParagraphStyle('BoxHead', parent=bold_body_style, fontSize=9, textColor=colors.HexColor('#1E3A8A'))),
            Paragraph(f"<b>Format:</b> Virtual / Remote", ParagraphStyle('BoxMode', parent=body_style, fontSize=8.5, alignment=2))
        ],
        [
            Paragraph(f"<b>Domain Track:</b> {internship_title}<br/><b>Start Date:</b> {start_date}", body_style),
            Paragraph(f"<b>Technical Mentor:</b> {guide_name}<br/><b>End Date:</b> {end_date}", body_style)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[260, 260])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))
    
    p3 = (
        f"<b>Terms & Guidelines:</b><br/>"
        f"• <b>Weekly Submissions:</b> Deliverables must be uploaded via your Student Dashboard in PDF format for mentor review.<br/>"
        f"• <b>Evaluation & Grading:</b> Deliverables will be graded out of 10 points per module by domain experts.<br/>"
        f"• <b>Certificate Release:</b> Upon completing all 4 modules and reaching the tenure end date, your official MSME & ISO recognized Certificate of Completion will be issued.<br/>"
        f"• <b>Code of Conduct:</b> All submitted work must be original and adhere to professional integrity standards."
    )
    story.append(Paragraph(p3, body_style))
    story.append(Spacer(1, 10))

    p4 = (
        f"We welcome you to Web Intern Platform and wish you an enriching and successful internship experience."
    )
    story.append(Paragraph(p4, body_style))
    story.append(Spacer(1, 14))
    
    # 4. Signatures Footer Table (Founder Title, Verified Badge, QR Code - NO Founder Name)
    founder_sig_img = RLImage(FOUNDER_SIG_PATH, width=125, height=35) if os.path.exists(FOUNDER_SIG_PATH) else Paragraph("<b>[SIGNATURE]</b>", bold_body_style)
    badge_img = RLImage(VERIFIED_BADGE_PATH, width=54, height=54) if os.path.exists(VERIFIED_BADGE_PATH) else Paragraph("<b>[BADGE]</b>", bold_body_style)
    qr_img = RLImage(qr_file_path, width=54, height=54) if (qr_file_path and os.path.exists(qr_file_path)) else Paragraph("<b>[QR CODE]</b>", bold_body_style)
    
    sig_cell_data = [
        [Paragraph("<b>Authorized Signatory</b>", bold_body_style)],
        [Spacer(1, 2)],
        [founder_sig_img],
        [Spacer(1, 2)],
        [Paragraph("<b>Founder & Managing Director</b><br/><font size=7.5 color='#475569'>Web Intern Platform</font>", body_style)]
    ]
    sig_cell_table = Table(sig_cell_data, colWidths=[180])
    sig_cell_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))

    sig_data = [
        [
            sig_cell_table,
            badge_img,
            Paragraph(f"<b>MSME Govt Recognized</b><br/><font size=7.5 color='#15803D'><b>[VERIFIED ISSUER]</b></font><br/><font size=7.5 color='#475569'>Doc Ref: {doc_number}</font>", ParagraphStyle('MidSealBW', alignment=1, fontName='Helvetica', fontSize=8, leading=11)),
            qr_img
        ]
    ]
    sig_table = Table(sig_data, colWidths=[180, 70, 190, 80])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (3,0), (3,0), 'RIGHT'),
    ]))
    story.append(sig_table)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    log_info(f"Generated Corporate Offer Letter PDF: {file_path}")
    
    if qr_file_path and os.path.exists(qr_file_path):
        try: os.remove(qr_file_path)
        except Exception: pass
        
    return file_path


def generate_certificate_pdf(student_name, internship_title, start_date, end_date, cert_id, is_paid=True):
    """
    Generates a Full-Color Executive Professional Certificate PDF (Landscape A4) with Web Intern UI/UX design.
    Features: Deep Navy & Gold Theme, MSME Emblem, WebIntern Logo, Gold Badge, Founder Signature, and Dynamic QR Code.
    """
    file_name = f"{cert_id}.pdf"
    file_path = os.path.join(Config.CERTIFICATES_DIR, file_name)
    
    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(A4),
        rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28
    )
    
    styles = getSampleStyleSheet()
    
    cert_header_style = ParagraphStyle(
        'CertHeaderColor',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=30,
        textColor=colors.HexColor('#0F172A'),
        alignment=1
    )

    name_style = ParagraphStyle(
        'StudentNameColor',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=25,
        leading=29,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1
    )

    text_center = ParagraphStyle(
        'TextCenterColor',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=17,
        textColor=colors.HexColor('#334155'),
        alignment=1
    )

    bold_body_style = ParagraphStyle(
        'BoldBodyCert',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#0F172A')
    )

    story = []
    
    # Dynamic student QR Code
    verify_url = f"https://webintern.in/#/verify/{cert_id}"
    qr_file_path = generate_qr_code_file(verify_url)
    
    msme_img = RLImage(MSME_LOGO_PATH, width=140, height=40) if os.path.exists(MSME_LOGO_PATH) else Paragraph("<b>MSME INDIA</b>", text_center)
    logo_img = RLImage(WEBINTERN_LOGO_PATH, width=145, height=42) if os.path.exists(WEBINTERN_LOGO_PATH) else Paragraph("<b>WEB INTERN</b>", cert_header_style)
    
    # 1. Top Header Table
    top_header_data = [
        [
            msme_img,
            logo_img,
            Paragraph(f"<b>CREDENTIAL ID:</b><br/><font color='#1E3A8A'><b>{cert_id}</b></font><br/><font size=8 color='#64748B'>Date: {datetime.date.today().strftime('%B %d, %Y')}</font>", ParagraphStyle('RightRefCol', alignment=2, fontName='Helvetica', fontSize=8.5, leading=12))
        ]
    ]
    top_table = Table(top_header_data, colWidths=[200, 380, 200])
    top_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
    ]))
    story.append(top_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph("<hr width='95%' color='#D97706' size=1.5/>", text_center))
    story.append(Spacer(1, 10))
    
    # 2. Title & Recipient Name
    story.append(Paragraph("CERTIFICATE OF COMPLETION", cert_header_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("THIS CERTIFICATE IS PROUDLY PRESENTED TO", ParagraphStyle('SubTextCol', alignment=1, fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#64748B'))))
    story.append(Spacer(1, 8))
    story.append(Paragraph(student_name, name_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<hr width='45%' color='#D97706' size=1.5/>", text_center))
    story.append(Spacer(1, 10))
    
    # 3. Core Achievement Statement
    body_content = (
        f"for successfully completing the <b>4-Week Virtual Internship Program</b> in "
        f"<b><font color='#1E3A8A'>{internship_title}</font></b><br/>"
        f"conducted from <b>{start_date}</b> to <b>{end_date}</b>.<br/>"
        f"The candidate demonstrated exceptional technical performance in weekly capstone deliverables and domain project evaluations."
    )
    story.append(Paragraph(body_content, text_center))
    story.append(Spacer(1, 14))
    
    # 4. Footer (Verification Details, QR Code, Gold Badge, Founder Signature - NO Founder Name)
    status_text = "VERIFIED CREDENTIAL (MSME ISO RECOGNIZED)" if is_paid else "STUDENT DRAFT COPY"
    status_color = "#15803D" if is_paid else "#B45309"
    
    badge_img = RLImage(VERIFIED_BADGE_PATH, width=68, height=68) if os.path.exists(VERIFIED_BADGE_PATH) else Paragraph("<b>[GOLD BADGE]</b>", text_center)
    qr_img = RLImage(qr_file_path, width=58, height=58) if (qr_file_path and os.path.exists(qr_file_path)) else Paragraph("<b>[QR CODE]</b>", text_center)
    founder_sig_img = RLImage(FOUNDER_SIG_PATH, width=130, height=36) if os.path.exists(FOUNDER_SIG_PATH) else Paragraph("<b>[SIGNATURE]</b>", bold_body_style)
    
    cert_sig_cell_data = [
        [founder_sig_img],
        [Spacer(1, 3)],
        [Paragraph("<b>Founder & Managing Director</b><br/><font size=7.5 color='#64748B'>Web Intern Platform</font>", ParagraphStyle('MetaRCol', alignment=2, fontName='Helvetica-Bold', fontSize=8.5, leading=12))]
    ]
    cert_sig_cell_table = Table(cert_sig_cell_data, colWidths=[230])
    cert_sig_cell_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))

    footer_data = [
        [
            Paragraph(f"<b>Verification Authority:</b><br/>Credential ID: {cert_id}<br/><font color='{status_color}'><b>Status: {status_text}</b></font><br/>MSME Govt Recognized Entity", ParagraphStyle('MetaLCol', alignment=0, fontName='Helvetica', fontSize=8, leading=12)),
            qr_img,
            badge_img,
            cert_sig_cell_table
        ]
    ]
    footer_table = Table(footer_data, colWidths=[240, 90, 200, 250])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (1,0), (2,0), 'CENTER'),
    ]))
    story.append(footer_table)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    log_info(f"Generated Executive Certificate PDF: {file_path}")
    
    if qr_file_path and os.path.exists(qr_file_path):
        try: os.remove(qr_file_path)
        except Exception: pass

    return file_path
