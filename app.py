"""KSA Metrology Pte Ltd — company website (Flask)."""
import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from html import escape

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
# In production set SECRET_KEY via an environment variable.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ksa-metrology-dev-key-change-me")

# --- Email delivery (Resend HTTP API; works on Render where SMTP is blocked) ---
# Set these as environment variables in Render (Environment tab):
#   RESEND_API_KEY  — your Resend API key (required to actually send mail)
#   CONTACT_TO      — recipient inbox (defaults to the company inquiry address)
#   CONTACT_FROM    — verified sender (defaults to inquiry@kalibratesolutions.com).
#                     The kalibratesolutions.com domain must be verified in Resend.
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
CONTACT_TO = os.environ.get("CONTACT_TO", "inquiry@kalibratesolutions.com")
CONTACT_FROM = os.environ.get("CONTACT_FROM",
                              "KSA Metrology Website <inquiry@kalibratesolutions.com>")

# --- hCaptcha ---
# Set these in Render's Environment tab:
#   HCAPTCHA_SITE_KEY   — public site key (also used in the HTML template)
#   HCAPTCHA_SECRET_KEY — secret key for server-side verification
HCAPTCHA_SITE_KEY = os.environ.get("HCAPTCHA_SITE_KEY", "")
HCAPTCHA_SECRET_KEY = os.environ.get("HCAPTCHA_SECRET_KEY", "")


# --- Contact-form abuse protection ---
_form_submissions: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 5     # max POST submissions
_RATE_WINDOW = 3600  # per this many seconds (1 hour)

def _contact_rate_limited(ip: str) -> bool:
    now = time.time()
    cutoff = now - _RATE_WINDOW
    recent = [t for t in _form_submissions[ip] if t > cutoff]
    _form_submissions[ip] = recent
    if len(recent) >= _RATE_LIMIT:
        return True
    _form_submissions[ip].append(now)
    return False


def _verify_hcaptcha(token: str) -> bool:
    """Return True if the hCaptcha token is valid. Skip check when no secret is configured."""
    if not HCAPTCHA_SECRET_KEY:
        return True  # dev/test: skip verification
    if not token:
        return False
    payload = f"secret={HCAPTCHA_SECRET_KEY}&response={token}".encode()
    req = urllib.request.Request(
        "https://hcaptcha.com/siteverify",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return bool(result.get("success"))
    except Exception as exc:  # noqa: BLE001
        app.logger.error("hCaptcha verification failed: %s", exc)
        return False


def send_inquiry_email(name, email, message, company=""):
    """Send a contact inquiry through the Resend API. Returns True on success."""
    if not RESEND_API_KEY:
        app.logger.warning("RESEND_API_KEY not set — inquiry logged but not emailed.")
        return False

    # --- Plain-text version (fallback) ---
    company_line = f"Company: {company}\n" if company else ""
    text = ("KSA METROLOGY PTE LTD — New website inquiry\n"
            "----------------------------------------\n\n"
            f"Name:    {name}\n"
            f"Email:   {email}\n"
            f"{company_line}"
            "\nMessage:\n"
            f"{message}\n\n"
            "----------------------------------------\n"
            f"Reply directly to this email to respond to {name}.\n")

    # --- HTML version (formal, Arial, table-based for email-client safety) ---
    e_name, e_email, e_company = escape(name), escape(email), escape(company)
    e_message = escape(message)
    label = ("padding:11px 0;color:#5b6b82;font-size:14px;width:110px;"
             "border-bottom:1px solid #eef2f7;vertical-align:top;")
    value = ("padding:11px 0;color:#0b2545;font-size:14px;"
             "border-bottom:1px solid #eef2f7;vertical-align:top;")
    company_row = (
        f'<tr><td style="{label}">Company</td>'
        f'<td style="{value}">{e_company}</td></tr>') if company else ""

    html = f"""\
<div style="margin:0;padding:24px 0;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7fb;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="max-width:600px;width:100%;background:#ffffff;border:1px solid #e6ebf2;border-radius:10px;overflow:hidden;">
        <tr><td style="background:#0b2545;padding:22px 28px;font-family:Arial,Helvetica,sans-serif;">
          <div style="color:#ffffff;font-size:18px;font-weight:bold;letter-spacing:.2px;">KSA Metrology Pte Ltd</div>
          <div style="color:#9fc0e8;font-size:13px;margin-top:3px;">New website inquiry</div>
        </td></tr>
        <tr><td style="padding:26px 28px 6px;font-family:Arial,Helvetica,sans-serif;color:#13315c;font-size:15px;line-height:1.5;">
          You have received a new inquiry from the website contact form:
        </td></tr>
        <tr><td style="padding:10px 28px 4px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                 style="font-family:Arial,Helvetica,sans-serif;border-collapse:collapse;">
            <tr><td style="{label}">Name</td><td style="{value}font-weight:bold;">{e_name}</td></tr>
            <tr><td style="{label}">Email</td>
                <td style="{value}"><a href="mailto:{e_email}" style="color:#1f6feb;text-decoration:none;">{e_email}</a></td></tr>
            {company_row}
          </table>
        </td></tr>
        <tr><td style="padding:20px 28px 8px;font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#5b6b82;text-transform:uppercase;letter-spacing:.6px;">Message</td></tr>
        <tr><td style="padding:0 28px 26px;">
          <div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#13315c;line-height:1.65;background:#f4f7fb;border-left:3px solid #1f6feb;border-radius:6px;padding:14px 16px;white-space:pre-wrap;">{e_message}</div>
        </td></tr>
        <tr><td style="background:#f7f9fc;padding:16px 28px;border-top:1px solid #e6ebf2;font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#8a98a8;line-height:1.5;">
          Reply directly to this email to respond to {e_name}.<br>Sent from kalibratesolutions.com
        </td></tr>
      </table>
    </td></tr>
  </table>
</div>"""
    payload = {
        "from": CONTACT_FROM,
        "to": [CONTACT_TO],
        "reply_to": email,
        "subject": f"New website inquiry from {name}",
        "text": text,
        "html": html,
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {RESEND_API_KEY}",
                 "Content-Type": "application/json",
                 # Cloudflare (in front of api.resend.com) blocks the default
                 # "Python-urllib" UA with error 1010 — send a real UA.
                 "User-Agent": "KSA-Website/1.0",
                 "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "ignore")
        app.logger.error("Resend API error %s: %s", exc.code, body)
    except Exception as exc:  # noqa: BLE001 — never let email failure 500 the form
        app.logger.error("Resend send failed: %s", exc)
    return False

# --- Company data (single source of truth, shared with all templates) -------
COMPANY = {
    "name": "KSA Metrology Pte Ltd",
    "tagline": "Precision Calibration & Validation You Can Trust",
    "phone": "(+65) 6231 9667",
    "phone_href": "+6562319667",
    "whatsapp": "(+65) 6254 5466",
    "whatsapp_href": "6562545466",
    "email": "inquiry@kalibratesolutions.com",
    "website": "www.kalibratesolutions.com",
    "address": "60 Kaki Bukit Place, #06-16 (Lobby A – Exit B), Eunos Techpark, Singapore 415979",
    "ph_address": "Unit 2, Solid Manila Building, Corner Lacson and San Sebastian Streets, Barangay 32, Bacolod City, Negros Occidental 6100, Philippines",
    "ph_company": "KSA Supplies & Services Inc.",
    "facebook": "https://www.facebook.com/KSAMetrologyPteLtd",
    "linkedin": "https://www.linkedin.com/company/ksa-metrology-pte-ltd",
    "founded": 2014,
    "clients": "1,000+",
    # Authorised Verifier designation under the Weights & Measures programme.
    "av_no": "AV37",
    "av_scheme": "Authorised Verifier",
    "av_authority": "Weights & Measures Office, Enterprise Singapore",
    "av_registry": "https://www.cpsaplus.gov.sg/Homepage/RegistryOfRegisteredSuppliersAndPatternApproval",
    # SAC-SINGLAS laboratory accreditation (Singapore Accreditation Council).
    "sac_scheme": "SAC-SINGLAS",
    "sac_no": "LA-2009-0444-C",
    "sac_field": "Calibration & Measurement",
    # Channel NewsAsia feature on Weights & Measures verification.
    "cna_url": "https://www.channelnewsasia.com/singapore/chinese-new-year-items-sea-cucumber-ginseng-weight-enterprise-singapore-4898681",
}

SERVICES = [
    {
        "icon": "scale",
        "title": "Weights & Measures Verification (AV37)",
        "desc": "As a designated Authorised Verifier (AV37) under Enterprise "
                "Singapore's Weights & Measures programme, we verify and seal "
                "weighing and measuring instruments for trade use, with ACCURACY "
                "labels registered in the CPSA+ system.",
        "featured": True,
        "tags": ["Trade-use approval", "ACCURACY labels", "CPSA+ registered"],
    },
    {
        "icon": "thermometer",
        "title": "Temperature Calibration",
        "desc": "Calibration of temperature sensors, data loggers, dry blocks and "
                "precision thermometers — critical for cold-chain and regulated storage.",
        "tags": ["Data loggers", "Dry blocks", "Thermometers"],
    },
    {
        "icon": "gauge",
        "title": "Mechanical Calibration",
        "desc": "Calibration of weighing machines, mass / weights and pressure "
                "gauges to traceable national standards.",
        "tags": ["Weighing machines", "Mass / weights", "Pressure gauges"],
    },
    {
        "icon": "clipboard",
        "title": "Equipment Validation (IQ/OQ/PQ)",
        "desc": "Installation, operational and performance qualification for "
                "pharmaceutical and life-science equipment and facilities.",
        "tags": ["IQ", "OQ", "PQ"],
    },
    {
        "icon": "shield",
        "title": "Compliance & Technical Support",
        "desc": "ISO/IEC 17025-aligned documentation and on-site technical support "
                "to keep your audits and regulatory submissions on track.",
        "tags": ["ISO/IEC 17025", "Audit-ready docs", "On-site support"],
    },
    {
        "icon": "droplet",
        "title": "Humidity & Environmental",
        "desc": "Calibration and mapping of humidity, pressure and environmental "
                "chambers, stability rooms and warehouses.",
        "tags": ["Chamber mapping", "Stability rooms", "Warehouses"],
    },
    {
        "icon": "truck",
        "title": "Logistics & Cold-Chain",
        "desc": "Validation and monitoring solutions for cold-chain transport, "
                "warehousing and distribution across the region.",
        "tags": ["Cold-chain", "Transport", "Monitoring"],
    },
]

# Accredited scope of calibration, summarised from the SAC-SINGLAS Schedule
# (Certificate LA-2009-0444-C, Issue 20). CMC = Calibration & Measurement
# Capability, expressed as expanded uncertainty at ~95% confidence.
CAPABILITIES = [
    {
        "group": "Temperature",
        "rows": [
            ("Temperature sensors (RTD)", "−80 °C to 200 °C", "from 0.30 °C"),
            ("RTD electrical simulation", "−200 °C to 800 °C", "from 0.41 °C"),
            ("Thermometers (digital display)", "−80 °C to 200 °C", "from 0.30 °C"),
            ("Thermometers (analog display)", "−30 °C to 200 °C", "from 1.1 °C"),
            ("Loop calibration (sensor & readout)", "−80 °C to 200 °C", "from 0.30 °C"),
            ("Dry block heaters", "25 °C to 140 °C", "from 0.30 °C"),
            ("Temperature mapping — autoclaves, chambers, "
             "fridges/freezers, ovens, incubators, storage areas",
             "−80 °C to 200 °C", "from 0.44 °C"),
            ("Humidity instruments (sensors, loggers, thermo-hygrometers)",
             "30–90 %RH @ 20–40 °C", "from 2.5 %RH"),
            ("Humidity mapping", "20–90 %RH", "from 2.2 %RH"),
            ("Liquid-in-glass thermometers", "0 °C to 200 °C", "from 0.21 °C"),
        ],
    },
    {
        "group": "Mechanical",
        "rows": [
            ("Pressure gauges (digital display)", "−900 to 20 000 mbar", "from 3.0 mbar"),
            ("Pressure gauges (analog display)", "−900 to 4 000 mbar", "from 13 mbar"),
            ("Absolute pressure instruments", "100 to 21 000 mbar abs", "from 4.7 mbar"),
            ("Differential pressure gauges", "0 to 2 500 Pa", "from 5 Pa"),
            ("Balances & weighing scales", "up to 1 000 kg", "from 0.0006 g"),
            ("Standard weights (OIML Class M1)", "1 kg to 10 kg", "from 17 mg"),
        ],
    },
    {
        "group": "Time",
        "rows": [
            ("Stopwatches, bench & equipment timers", "5 to 3 600 s", "from 0.25 s"),
        ],
    },
]

INDUSTRIES = [
    "Pharmaceuticals", "Logistics & Cold-Chain", "Food & Beverage",
    "Manufacturing", "Healthcare", "Laboratories",
]

STATS = [
    {"value": "1,000+", "label": "Clients served"},
    {"value": "10+", "label": "Years of expertise"},
    {"value": "SAC-SINGLAS", "label": "Accredited laboratory"},
    {"value": "AV37", "label": "Authorised Verifier"},
    {"value": "bizSAFE 3", "label": "Committed to Workplace Safety Excellence"},
]

WHATSNEWS = [
    {
        "date": "June 2026",
        "title": "New Office in the Philippines",
        "desc": "KSA Metrology is expanding! KSA Supplies & Services Inc., "
                "a company of KSA Metrology Pte Ltd, brings accredited "
                "calibration and verification services closer to our clients "
                "across Southeast Asia. Located in Bacolod City, "
                "Negros Occidental.",
        "img": "img/photos/NewOffice.jpg",
        "img_alt": "KSA Supplies & Services Inc. — new office in Bacolod City, Philippines",
    },
]


@app.context_processor
def inject_company():
    """Make COMPANY available in every template."""
    return {"company": COMPANY}


@app.route("/")
def index():
    return render_template("index.html", services=SERVICES, stats=STATS,
                           industries=INDUSTRIES, whatsnews=WHATSNEWS)


@app.route("/about")
def about():
    return render_template("about.html", stats=STATS, industries=INDUSTRIES)


@app.route("/services")
def services():
    return render_template("services.html", services=SERVICES,
                           capabilities=CAPABILITIES)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # Honeypot — invisible to humans; bots tend to fill it
        if (request.form.get("url") or "").strip():
            flash("Thank you! Your inquiry has been received — we'll be in touch shortly.",
                  "success")
            return redirect(url_for("contact"))

        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        company = (request.form.get("company") or "").strip()
        message = (request.form.get("message") or "").strip()

        if not name or not email or not message:
            flash("Please fill in your name, email and message.", "error")
            return redirect(url_for("contact"))

        # Field length caps
        if len(name) > 100 or len(email) > 254 or len(company) > 200 or len(message) > 5000:
            flash("One or more fields exceeds the allowed length.", "error")
            return redirect(url_for("contact"))

        # hCaptcha verification
        captcha_token = request.form.get("h-captcha-response", "")
        if not _verify_hcaptcha(captcha_token):
            flash("CAPTCHA verification failed. Please try again.", "error")
            return redirect(url_for("contact"))

        # Rate limit: 5 submissions per IP per hour
        ip = request.remote_addr or "unknown"
        if _contact_rate_limited(ip):
            flash("Too many submissions. Please wait a while before trying again.", "error")
            return redirect(url_for("contact"))

        app.logger.info("Inquiry from %s <%s> [%s]: %s", name, email, company, message)
        send_inquiry_email(name, email, message, company)
        flash("Thank you! Your inquiry has been received — we'll be in touch shortly.",
              "success")
        return redirect(url_for("contact"))

    return render_template("contact.html", hcaptcha_site_key=HCAPTCHA_SITE_KEY)


if __name__ == "__main__":
    # Local development server only. For production use a WSGI server
    # (waitress on Windows, gunicorn on Linux) — see README.md.
    port = int(os.environ.get("PORT", 5055))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
