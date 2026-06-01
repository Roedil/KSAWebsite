"""KSA Metrology Pte Ltd — company website (Flask)."""
import json
import os
import urllib.error
import urllib.request

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


def send_inquiry_email(name, email, message, company=""):
    """Send a contact inquiry through the Resend API. Returns True on success."""
    if not RESEND_API_KEY:
        app.logger.warning("RESEND_API_KEY not set — inquiry logged but not emailed.")
        return False

    company_line = f"Company: {company}\n" if company else ""
    text = (f"New inquiry from the KSA Metrology website\n\n"
            f"Name:  {name}\n"
            f"Email: {email}\n"
            f"{company_line}\n"
            f"Message:\n{message}\n")
    company_html = (f"<strong>Company:</strong> {company}<br>" if company else "")
    html = (f"<h2>New website inquiry</h2>"
            f"<p><strong>Name:</strong> {name}<br>"
            f"<strong>Email:</strong> <a href='mailto:{email}'>{email}</a><br>"
            f"{company_html}</p>"
            f"<p><strong>Message:</strong></p>"
            f"<p style='white-space:pre-wrap'>{message}</p>")
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
                 "Content-Type": "application/json"},
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
]


@app.context_processor
def inject_company():
    """Make COMPANY available in every template."""
    return {"company": COMPANY}


@app.route("/")
def index():
    return render_template("index.html", services=SERVICES, stats=STATS,
                           industries=INDUSTRIES)


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
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        company = (request.form.get("company") or "").strip()
        message = (request.form.get("message") or "").strip()

        if not name or not email or not message:
            flash("Please fill in your name, email and message.", "error")
            return redirect(url_for("contact"))

        # Always log the inquiry as a backup, then email it via Resend.
        app.logger.info("Inquiry from %s <%s> [%s]: %s", name, email, company, message)
        send_inquiry_email(name, email, message, company)
        flash("Thank you! Your inquiry has been received — we'll be in touch shortly.",
              "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")


if __name__ == "__main__":
    # Local development server only. For production use a WSGI server
    # (waitress on Windows, gunicorn on Linux) — see README.md.
    port = int(os.environ.get("PORT", 5055))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
