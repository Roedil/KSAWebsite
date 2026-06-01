# KSA Metrology Pte Ltd — Website

A Flask website for **KSA Metrology Pte Ltd** (Kalibrate Solutions Asia):
calibration, validation and technical support for regulated industries.

## Project structure

```
Website_KSA/
├─ app.py              # Flask app + company data, routes
├─ wsgi.py             # production WSGI entry point (waitress/gunicorn)
├─ Procfile            # gunicorn config for Render/Heroku
├─ serve.ps1           # one-line waitress launcher for Windows
├─ requirements.txt    # dependencies
├─ runtime.txt         # Python version (for hosts that read it)
├─ templates/          # base, index, about, services, contact
└─ static/css/         # style.css
```

## Local development

```powershell
cd D:\Claude_Projects\Website_KSA
pip install -r requirements.txt
python app.py
```
Opens on **http://0.0.0.0:5055** (reachable locally at http://127.0.0.1:5055).

> Port defaults to **5055** and is configurable via the `PORT` env var.
> Port 5000 is intentionally avoided.

## Production / hosting

Do **not** use `python app.py` in production (it runs Flask's debug server).
Use a real WSGI server instead.

### Windows (waitress)
```powershell
pip install -r requirements.txt
.\serve.ps1
# or:  waitress-serve --host=0.0.0.0 --port=5055 wsgi:app
```

### Linux (gunicorn)
```bash
pip install -r requirements.txt
gunicorn wsgi:app --bind 0.0.0.0:5055 --workers 3
```

### Render / Heroku
The included `Procfile` runs gunicorn and binds to the platform-provided
`$PORT` automatically:
```
web: gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 3
```

## Environment variables

| Variable      | Purpose                                   | Default                |
|---------------|-------------------------------------------|------------------------|
| `PORT`        | Port for the dev/waitress server          | `5055`                 |
| `SECRET_KEY`  | Flask session/flash signing key           | dev placeholder        |
| `FLASK_DEBUG` | `1` = debug on (dev only), `0` = off       | `1`                    |

**Before hosting publicly:** set a strong `SECRET_KEY` and `FLASK_DEBUG=0`.

## Contact form note

The enquiry form logs submissions rather than sending email over SMTP
(many hosts block outbound SMTP). To enable real delivery, integrate an
email API such as SendGrid or Mailgun in the `contact()` route in `app.py`.
