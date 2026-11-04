# TaskFlow — Modern Task Management Web Application

TaskFlow is a responsive, feature-rich task management web application built with **Python**, **Django MVT**, **Neon PostgreSQL / SQLite**, and vanilla **JavaScript**, styled with a custom design system inspired by modern SaaS productivity platforms.

It includes an integrated **Groq-powered AI productivity assistant** and **AI task description generator**, real-time **Chart.js** analytics, complete database-backed task CRUD with modals, and strict user data isolation.

---

## Features

- **Authentication & Security**
  - Custom branded Sign In and Sign Up screens with password visibility toggles.
  - Server-side validation (unique email/username, password strength checks).
  - Strict user data isolation: each user can only view, edit, toggle, or delete their own tasks.
  - Secure CSRF protection on all state-changing operations and AJAX requests.
  - Profile management (name, email, member stats, secure password changes).

- **Task Management (CRUD & Modals)**
  - Fast task creation & editing via responsive modal dialogs without leaving the page.
  - Priority levels: `Low` (🟢 green), `Medium` (🟡 orange), `High` (🔴 red).
  - Due dates with automatic overdue detection.
  - Task completion checkbox and instant status toggle.
  - Search by title or description, filter by status (All, Pending, Completed, Overdue), and filter by priority.
  - Clean pagination.
  - Explicit confirmation modal for task deletion.

- **Dashboard & Analytics**
  - **4 Stat Summary Cards**: Total Tasks, Completed, Pending, Overdue.
  - **Interactive Charts (Chart.js)**:
    - Donut chart: Task completion & status breakdown.
    - Weekly Activity line chart: Tasks created across the last 7 days.
    - Bar chart: Tasks distribution by priority.
  - Recent Tasks table with inline action buttons.

- **Groq-Powered AI Integration**
  - **Floating AI Assistant**: Chat with `TaskFlow AI` anytime to get productivity tips, break down complex goals, and prioritize your workload.
  - **AI Task Description Generator**: In the Create/Edit task modals, enter a task title and click **"✨ Suggest with AI"** to generate concise, actionable descriptions.
  - **Safe Server-Side Integration**: Your Groq API key is never exposed to browser JavaScript. Gracefully handles network timeouts and missing API key configurations.

---

## Technology Stack

- **Backend**: Python 3.10+, Django 5.x / 6.x (MVT, Function-Based Views, Django ORM)
- **Database**: Neon Serverless PostgreSQL (via `psycopg` v3 & `dj-database-url`) / SQLite (local fallback)
- **Static Assets & Server**: WhiteNoise 6.x (`CompressedStaticFilesStorage`), Gunicorn WSGI HTTP Server
- **Frontend**: HTML5, CSS3 (Custom Design System), Vanilla JavaScript (ES6+)
- **Icons & Visuals**: Bootstrap Icons (`bi`), SVG Logos
- **Charts**: Chart.js 4.4
- **AI Service**: Groq API (`llama3-8b-8192` or other supported models) via server-side Python requests

---

## Windows Installation & Setup Guide

### 1. Clone or Open Project
```powershell
cd e:\BlackBox\TaskFlow
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` in any text editor and configure your environment variables:
```env
SECRET_KEY=django-insecure-taskflow-secret-key-12345
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database (Neon PostgreSQL connection string, or omit to use local SQLite)
DATABASE_URL=postgresql://<user>:<password>@<ep-sample-pooler>.<region>.aws.neon.tech/<dbname>?sslmode=require

# Groq Cloud AI
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama3-8b-8192
```
*(Note: TaskFlow runs normally even without a Groq API key or external database; omitting `DATABASE_URL` defaults automatically to local SQLite `db.sqlite3`).*

### 5. Apply Database Migrations
Run database migrations to initialize tables (automatically applies to Neon PostgreSQL when `DATABASE_URL` is set, or local SQLite otherwise):
```powershell
python manage.py migrate
python manage.py seed_demo_data
```

### 6. Create an Admin Superuser (Optional)
```powershell
python manage.py createsuperuser
```

### 7. Run the Development Server
```powershell
python manage.py runserver
```
Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your web browser.

---

## Running Automated Tests

Run the test suite covering authentication, authorization, CRUD operations, data isolation, calculations, and AI endpoints:
```powershell
python manage.py test
```

---

## Production Deployment (Render)

TaskFlow is pre-configured for seamless cloud deployment on platforms like [Render](https://render.com/):

### 1. Build & Start Commands
- **Build Command:** `./build.sh` (or `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`)
- **Start Command:** `gunicorn config.wsgi:application`

### 2. Environment Variables on Render
Configure the following in the Render Dashboard Environment settings:
- `SECRET_KEY`: Long, random secret key.
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: `<your-app-name>.onrender.com,127.0.0.1,localhost`
- `DATABASE_URL`: Your Neon PostgreSQL connection string (`postgresql://...`).
- `GROQ_API_KEY`: Groq Cloud API key.
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD`: Transactional Gmail SMTP credentials.

### 3. Static Files & WhiteNoise
Static assets (CSS, JS, SVGs) are automatically collected into `staticfiles/` during the build step and served directly through `WhiteNoiseMiddleware` using `CompressedStaticFilesStorage` with Gzip and Brotli compression, ensuring fast load times and reliable asset delivery without external CDN dependencies.

---

## Project Structure

```
TaskFlow/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── config/                  # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── accounts/                # Authentication & User Profiles
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── tasks/                   # Tasks CRUD & Dashboard
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── reports/                 # Analytics & Chart.js Visualizations
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── assistant/               # Groq AI Service & Chatbot API
│   ├── services.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── templates/               # Django MVT HTML Templates
│   ├── base.html
│   ├── base_app.html
│   ├── includes/
│   │   ├── sidebar.html
│   │   ├── topbar.html
│   │   └── ai_assistant.html
│   ├── accounts/
│   │   ├── login.html
│   │   ├── signup.html
│   │   └── profile.html
│   ├── tasks/
│   │   ├── dashboard.html
│   │   ├── task_list.html
│   │   └── includes/
│   │       ├── create_task_modal.html
│   │       ├── edit_task_modal.html
│   │       └── delete_task_modal.html
│   └── reports/
│       └── report_dashboard.html
│
└── static/
    ├── css/
    │   ├── main.css
    │   ├── auth.css
    │   ├── dashboard.css
    │   ├── tasks.css
    │   └── reports.css
    ├── js/
    │   ├── main.js
    │   ├── tasks.js
    │   ├── assistant.js
    │   └── reports.js
    └── images/
        └── logo.svg
```

