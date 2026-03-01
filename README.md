# Digit Project

A Django web app where users draw digits (0-9) in a browser canvas and a TensorFlow model predicts the digit.

## Overview

- Users open the game, get a random target digit, draw it, and submit.
- The backend preprocesses the image and runs inference with a saved Keras model (`model/digit_model.h5`).
- Score (`correct` / `total`) is tracked per session in SQLite.

## Features

- Random target digit game loop
- Canvas-based digit input
- Image preprocessing (crop, resize, normalize)
- TensorFlow digit prediction
- Result page with prediction + running score

## Tech Stack

- **Backend:** Django 5, Python
- **ML Inference:** TensorFlow / Keras, NumPy, Pillow
- **Frontend:** Django templates + Tailwind CSS (`django-tailwind`)
- **Database:** SQLite (default)
- **Static serving (prod):** WhiteNoise
- **WSGI server (prod):** Gunicorn

## Project Structure (key parts)

- `digit/` — app logic (`views.py`, `utils.py`, `models.py`, templates)
- `digit_project/` — project settings and root URLs
- `model/digit_model.h5` — trained model file used for inference
- `theme/` — Tailwind integration

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables (minimum for local dev):

   ```bash
   # PowerShell example
   $env:DEBUG="True"
   $env:SECRET_KEY="dev-only-change-me"
   ```

4. Apply migrations:

   ```bash
   python manage.py migrate
   ```

5. Run development server:

   ```bash
   python manage.py runserver
   ```

6. Open: `http://127.0.0.1:8000/digit/`

## Important Environment Variables

- `SECRET_KEY` (required when `DEBUG=False`)
- `DEBUG` (`True` for local development)
- `CSRF_TRUSTED_ORIGINS` (comma-separated domains in production)
- `SECURE_SSL_REDIRECT` (defaults to `True`)
- `SECURE_HSTS_SECONDS` (defaults to `31536000`)

## URL Endpoints

- `GET /digit/` — Home page
- `GET /digit/scribble/` — Draw page with random target
- `POST /digit/predict/` — Submit image for prediction
- `GET /digit/result/` — Shows result and score

## Production Readiness

Current status: **partially production-ready**.

Already in place:

- Environment-based `SECRET_KEY` and `DEBUG`
- Security middleware and secure cookie flags
- WhiteNoise static file configuration
- Gunicorn dependency

Still required before real production use:

- Restrict `ALLOWED_HOSTS` (currently `['*']`)
- Ensure HTTPS termination and correct proxy headers in hosting
- Set `CSRF_TRUSTED_ORIGINS` to real domain(s)
- Run `collectstatic` during deployment
- Add monitoring/logging, backup strategy, and CI tests

## Notes

- The model file must exist at `model/digit_model.h5`.
- Database is SQLite by default; consider PostgreSQL for higher scale/concurrency.
