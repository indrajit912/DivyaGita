# DivyaGita – A Modern Portal for Bhagavad Gita

DivyaGita is a production-quality, modern, and modular Flask web application dedicated to the study, preservation, and collaborative commentary of the **Bhagavad Gita**. 

Unlike other traditional scripture portals, DivyaGita offers a sleek, premium, mobile-first design, interactive user contributions, secure profile features for contributors, and robust administrative moderation tools.

Repository: [https://github.com/indrajit912/DivyaGita.git](https://github.com/indrajit912/DivyaGita.git)  
Production URL: [https://divyagita.pythonanywhere.com](https://divyagita.pythonanywhere.com)

---

## Features

- **Gita Content Browse Engine:** Clean, mobile-friendly interface for browsing all 18 Chapters and 700 Verses, formatted with Noto Serif Devanagari Sanskrit rendering.
- **English Transliterations & Default Translations:** Fast lookup of pronunciation guides and classical English translations.
- **Collaborative Explanation System:** Registered users (contributors) can submit and update their own explanations for any verse.
- **Hermes Email Integration:** Real-time OTP (One-Time Password) email dispatch for registration verification and password reset workflows.
- **Admin Moderation Panel:** Administrators can view contributor profiles (including secure fields hidden from standard users), toggle account activation states, search contributors, and remove inappropriate content.
- **Automated Database Setup:** Local JSON-driven database population script to build the entire content index in a single command.

---

## Technical Stack

- **Backend:** Python 3.14+, Flask (Application Factory Pattern), SQLAlchemy, Flask-Login, Flask-Migrate, WTForms, Requests.
- **Frontend:** Bootstrap 5, Bootstrap Icons, Google Fonts (Playfair Display, Inter, Noto Serif Devanagari), Custom Premium CSS.
- **Database:** SQLite (Development) / PostgreSQL or MySQL (Production ready via environment variables).

---

## Project Structure

```text
divyagita/
│
├── app/
│   ├── auth/          # Contributor register/login/verification routes & forms
│   ├── admin/         # Moderator dashboards, user list, search & moderation
│   ├── main/          # Landing pages and About details
│   ├── gita/          # Chapter/Verse indexing, explanations, WTForms
│   ├── services/      # Reusable EmailService (Hermes integration)
│   ├── models/        # User, Role, Chapter, Verse, Translation, Explanation
│   ├── templates/     # Jinja2 HTML templates
│   ├── static/        # Custom styles and scripts
│   ├── commands.py    # Flask CLI commands (setup-db, create-admin)
│   └── extensions.py  # Extensions instantiation (db, migrate, login_manager)
│
├── data/              # Source Bhagavad Gita JSON data (chapters, verses)
├── migrations/        # Database migration files (Flask-Migrate)
├── config.py          # Production & Development environment configs
├── wsgi.py            # WSGI and App Entrypoint
├── requirements.txt   # Dependencies manifest
└── README.md          # Documentation
```

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/indrajit912/DivyaGita.git
cd DivyaGita
```

### 2. Configure Virtual Environment
Create and activate a virtual environment:

**On Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` (the application will do this automatically on first boot if omitted). Set the following keys:
```text
SECRET_KEY=your-random-secret-key
SECURITY_PASSWORD_SALT=your-password-salt
HERMES_BASE_URL=https://hermesbot.pythonanywhere.com
HERMES_API_KEY=your-hermes-api-key
HERMES_EMAILBOT_ID=your-hermes-bot-id
```

---

## Database Setup & Administration Commands

Ensure your virtual environment is active, then initialize the database and create the first administrator account using the following workflow:

```bash
# 1. Run migrations to create the database schema and tables
flask db upgrade

# 2. Populate the database with the complete Bhagavad Gita dataset
flask setup-db

# 3. Create the administrator account interactively
flask create-admin
```
Follow the prompts to supply your Username, Email, Name, and Password.

---

## Development Workflow

To run the Flask development server locally, use the standard Flask utility CLI:
```bash
flask run
```
The application will be accessible at: `http://127.0.0.1:5000`

---

## Deployment Notes

To deploy DivyaGita in a production environment (such as PythonAnywhere or Render):
1. Configure environment variables in the host server panel (`FLASK_ENV=production`, `DATABASE_URL` for Postgres/MySQL if applicable, and Hermes credentials).
2. Set the `SESSION_COOKIE_SECURE=True` parameter (enabled automatically under `ProductionConfig`).
3. Set up a WSGI server (such as Gunicorn or uWSGI) pointing to the `app` instance in `wsgi.py`.
4. Ensure files under `data/` are readable by the server process.

---

## License & Attribution

- **Developer:** Indrajit Ghosh
- **Developer Website:** [https://indrajitghosh.onrender.com](https://indrajitghosh.onrender.com)
- **Inspiration:** Sri Avimunya (devotee of Lord Krishna)
- **License:** MIT License
