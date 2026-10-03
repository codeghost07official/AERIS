# AERIS

AERIS (Aerospace Equipment & Reliability Intelligence System) is a Flask-based web application designed to support spacecraft-related monitoring and review using uploaded telemetry data and spacecraft images. The project focuses on two major tasks: detecting unusual numerical patterns in telemetry CSV files and examining image characteristics such as brightness, contrast, sharpness, and edge density to support visual inspection of aerospace imagery.

The application is built as a Class XII CBSE AI Capstone Project and is intended to demonstrate how artificial intelligence and data analysis can be used in a practical engineering context. It combines web application development, database design, authentication, machine learning, and image processing in a single, user-friendly system.

---

## 1. Project Introduction and Purpose

Modern aerospace systems generate large amounts of telemetry and high-resolution images. These data sources are often too large and detailed to inspect manually in real time. AERIS is designed to help users quickly review key indicators and identify patterns that may require a closer look.

The application does not claim to replace engineering judgment or certification. Instead, it acts as a supportive decision aid. It helps users:

- upload telemetry data in CSV format,
- detect unusual readings using an unsupervised anomaly-detection model,
- upload spacecraft or equipment-related images,
- compute image quality and visual characteristics,
- store results in a database for later review,
- present a simple plain-language explanation for each analysis,
- allow users to manage their own analysis history securely.

This makes the project suitable for educational demonstration, technical explanation, and prototype-level analysis system design.

---

## 2. Problem Statement and Motivation

Spacecraft systems depend on reliable equipment monitoring. Small changes in temperature, voltage, pressure, current, vibration, or other monitored variables may indicate a possible issue. Similarly, images captured by spacecraft or related inspection systems can be affected by poor lighting, low contrast, low sharpness, or unclear edges, which may make equipment details difficult to inspect.

In real-world engineering scenarios, manual inspection of huge datasets and images can be slow, error-prone, and difficult to scale. A system that can quickly summarize telemetry outliers and image characteristics helps reduce the burden on engineers and supports better decision-making.

AERIS was created to demonstrate how this challenge can be addressed using a web application built with Python, machine learning, and computer vision techniques. The project focuses on educational and prototype-level analysis rather than operational spacecraft control.

---

## 3. Project Objectives

The main objectives of AERIS are to:

1. Build a secure and user-friendly web application for spacecraft-related data analysis.
2. Detect unusual patterns in uploaded telemetry CSV files using an unsupervised machine learning model.
3. Analyze image quality indicators such as brightness, contrast, sharpness, and edge density.
4. Convert technical output into simple, understandable explanations for users.
5. Store and display user analysis history in a database.
6. Demonstrate the complete flow from data upload to result generation and reporting.
7. Provide a realistic AI-capstone project that combines software engineering, data analysis, and AI concepts.

---

## 4. How AERIS Works

AERIS follows a straightforward workflow:

1. User registers an account or signs in with email/password.
2. User may also continue with Google OAuth.
3. The user chooses either telemetry analysis or image analysis from the dashboard.
4. The system validates the uploaded file type and size.
5. The selected analysis method runs on the file.
6. Results are displayed in a readable dashboard page.
7. The system saves important metadata and summaries to the database.
8. The user can review all their previous analyses in the history section.
9. Analysis records can be deleted through the history page.

This flow is handled by the Flask application and various backend modules working together.

---

## 5. Telemetry CSV Analysis and Anomaly Detection

### 5.1 Why telemetry analysis is important

Telemetry data usually contains time-based or observation-based records of sensors and operating parameters. In spacecraft-related systems, unusual values may be associated with transient faults, degraded equipment, sensor issues, or abnormal operating conditions. However, anomaly detection does not prove a specific defect by itself; it only highlights readings that appear different from the pattern.

### 5.2 What the code does

The telemetry analysis logic is implemented in `app/telemetry.py`.

It performs the following steps:

- reads the uploaded CSV using pandas,
- checks that the file is not empty,
- selects only numerical columns,
- removes infinite and missing values,
- drops all-empty columns,
- fills missing values with the median of each column,
- removes constant columns because they contain no variation,
- confirms that at least five usable observations remain,
- applies an Isolation Forest model from scikit-learn,
- flags anomalies as observations with prediction value `-1`,
- calculates the anomaly count and percentage,
- prepares summary statistics such as mean, minimum, maximum, and standard deviation for each numeric parameter,
- generates a simple chart and plain-language explanation.

### 5.3 Isolation Forest model

AERIS uses `sklearn.ensemble.IsolationForest` with:

- `n_estimators=100`
- `contamination="auto"`
- `random_state=42`

This is an unsupervised anomaly-detection algorithm. It does not learn from labelled fault data in the project; instead, it identifies data points that stand out from the majority pattern.

### 5.4 Important validation rules

The current implementation enforces a few practical rules:

- the CSV must contain at least one numeric column,
- the file cannot be empty,
- all numeric measurements must not be constant,
- at least five usable observations are required,
- non-numeric columns are ignored,
- rows with invalid or non-numeric values are not treated as valid measurement inputs.

### 5.5 Result output

The telemetry result includes:

- total observations,
- selected parameter names,
- anomaly count,
- anomaly percentage,
- anomaly row numbers,
- interpretation text,
- summary text,
- plain-language explanation,
- descriptive statistics for each numeric column,
- a chart showing anomaly positions.

The UI presents these values in cards and tables. The anomaly chart uses Chart.js to visualize each observation as either normal or anomalous.

### 5.6 Plain-language explanation

The function `create_plain_language_explanation()` formats the output for non-technical users. It converts technical results into sentences like:

- “AERIS found 3 unusual lines (15%).”
- “These differences could be a warning that some equipment needs a closer look.”
- “They are not proof that anything is broken.”

This is intentional: the app is designed to explain findings in everyday language without overstating certainty.

---

## 6. Spacecraft Image Analysis and Measurements

### 6.1 What the image module does

The image analysis logic is implemented in `app/image_analysis.py`.

The system accepts image files with extensions `.jpg`, `.jpeg`, and `.png`. Each file is loaded using OpenCV. It then extracts basic visual quality metrics from the grayscale version of the image:

- brightness: average pixel intensity,
- contrast: standard deviation of image intensity,
- sharpness: variance of the Laplacian transform,
- edge density: proportion of edge pixels detected by the Canny edge detector.

### 6.2 Image measurements in detail

The app computes the following:

- Image width and height from the loaded image dimensions.
- Brightness by measuring the mean intensity across the grayscale image.
- Contrast by calculating the standard deviation of grayscale values.
- Sharpness using `cv2.Laplacian(gray, cv2.CV_64F).var()`.
- Edge density as the percentage of pixels marked as edges by `cv2.Canny()`.

### 6.3 Interpretation logic

The code converts these values into interpretation notes:

- if brightness is low, the image is described as relatively dark,
- if brightness is very high, the image is described as bright,
- low contrast suggests that some regions may blend together,
- low sharpness suggests that fine details may be difficult to see,
- low edge density indicates relatively few prominent outlines,
- higher edge density indicates more visible structural outlines.

These metrics help answer a practical question: “Is this image easy to inspect?”

### 6.4 Important fact about the image analysis

The current system does not identify cracks, dents, broken parts, or specific fault types. It does not use a trained model for defect classification. Instead, it provides descriptive image characteristics and tells the user that these features do not independently establish equipment damage.

This is an important design choice and matches the project’s educational and prototype nature.

---

## 7. How the System Interprets Results and Produces Insights

AERIS is deliberately designed to present results in a way that is technically meaningful but easy to understand.

### 7.1 Technical summary

Each analysis returns a `summary` string that captures the most relevant numbers clearly.

For example:

- telemetry: “Analyzed 20 observations across 2 numerical parameters. Detected 3 anomalies (15%).”
- image: “Analyzed a 1200 × 800 image. Brightness: 132.5, contrast: 42.1, sharpness: 89.3, and edge density: 8.7%.”

### 7.2 Plain-language explanation

The project uses a second explanation format to make results accessible to non-technical readers.

This is especially important for CBSE evaluators, teachers, and external reviewers, because the app is not only checking technical metrics but also translating them into everyday language.

Examples from the project include:

- warning about unusual readings requiring a closer look,
- confirmation that anomalies are not proof of failure,
- note that image quality may make equipment difficult to inspect,
- reminder that analysis supports review and does not replace a human inspection.

### 7.3 Decision-support mindset

The application intentionally avoids definitive diagnosis claims. It says:

- unusual readings may warrant review,
- some image attributes may reduce visibility,
- human expertise is still important,
- additional inspection is recommended when the output suggests uncertainty.

This careful wording is a strength of the project because it reflects realistic engineering practice.

---

## 8. User Registration, Login, Google Authentication, and Session Management

AERIS includes a complete authentication flow.

### 8.1 User registration

The registration route in `app/auth.py` accepts:

- name,
- email,
- password.

The application validates:

- all fields are filled,
- password length is at least 8 characters,
- email is unique in the database.

Passwords are hashed using Werkzeug’s password hashing utilities before storage.

### 8.2 Login

The login route checks the submitted email and password against the stored values. If correct, it stores session data including:

- `user_id`
- `user_name`
- `user_email`

This allows the user to move through the protected application pages without repeated sign-in.

### 8.3 Google authentication

The project also integrates Google OAuth using `Authlib`.

The application configures the OAuth client with:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- Google OpenID discovery endpoint

During sign-in:

- the app initiates the Google authorization flow,
- receives the token and user profile,
- checks email and verification status,
- links the Google account to a local user record if needed,
- signs the user into the current session.

This is implemented with the `google_login()`, `google_callback()`, and related logic in `app/auth.py`.

### 8.4 Session lifecycle and logout

The app uses Flask sessions and clears session data on logout. The login-required decorator ensures that protected routes redirect unauthenticated users back to the login page.

---

## 9. Database Design and Stored Information

AERIS uses PostgreSQL via `psycopg`, with configuration defined by `DATABASE_URL`.

### 9.1 Database initialization

During app startup, `create_app()` calls `init_db()`. The database initialization function performs a schema setup that includes:

- a `public.users` table,
- an `analysis_history` table for UUID-based user IDs,
- a fallback `public.analyses` table for integer-based user IDs.

The project detects the database user ID type at runtime, which makes it compatible with different PostgreSQL schema patterns.

### 9.2 Users table

The `public.users` table stores:

- `id`
- `name`
- `email` (unique)
- `password_hash`
- `google_id` (optional, unique)
- `created_at`

This supports both traditional local accounts and Google-authenticated accounts.

### 9.3 Analysis history table

For UUID-based storage, the project uses `public.analysis_history`, which stores:

- `id`
- `user_id`
- `analysis_type` (`telemetry` or `image`)
- `filename`
- `status`
- `total_observations`
- `anomalies_detected`
- `anomaly_rate`
- `features_used`
- `method`
- `method_description`
- `file_path`
- `result_data` (JSONB)
- `plain_language_explanation`
- `created_at`

This is a flexible structure for storing machine-readable and human-readable result data.

### 9.4 History retrieval and deletion

The application provides:

- `save_analysis()` to store results after each analysis,
- `get_user_history()` to retrieve a user’s analysis records,
- `delete_analysis()` to delete a specific record if it belongs to the correct user.

The history page displays the records, and each entry can be deleted through a confirmation prompt. This ensures that users only remove their own records.

---

## 10. Technologies, Libraries, and Tools Used

The project is implemented in Python and uses a small set of carefully chosen libraries.

### Programming languages

- Python 3
- HTML
- CSS
- JavaScript

### Backend and application framework

- Flask
- Werkzeug
- python-dotenv

### Database and authentication

- PostgreSQL
- psycopg
- Authlib

### Data analysis and machine learning

- pandas
- numpy
- scikit-learn

### Image processing

- OpenCV (`opencv-python-headless`)
- Pillow

### Front-end UI and visualization

- Chart.js (loaded from CDN)
- custom CSS and JavaScript in `app/static/`

### Deployment / runtime support

- Gunicorn

---

## 11. Complete Project Folder Structure

The project layout is as follows:

```text
AERIS/
├── .env
├── .git/
├── .gitignore
├── .kilo/
├── .venv/
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── database.py
│   ├── image_analysis.py
│   ├── routes.py
│   ├── telemetry.py
│   ├── static/
│   │   ├── script.js
│   │   ├── style.css
│   │   └── uploads/
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── history.html
│       ├── login.html
│       ├── register.html
│       └── results.html
├── tests/
│   ├── test_database.py
│   ├── test_image_analysis.py
│   ├── test_report_explanation.py
│   └── test_telemetry.py
├── uploads/
├── LICENSE
├── README.md
├── requirements.txt
├── run.py
└── venv/
```

### Key files explained

- `run.py`: starts the Flask application.
- `app/__init__.py`: creates the app, loads environment variables, configures OAuth, and initializes the database.
- `app/auth.py`: handles registration, login, Google OAuth, and session management.
- `app/database.py`: handles database connections, schema creation, save/load/delete logic, and user history queries.
- `app/telemetry.py`: performs CSV telemetry analysis and anomaly detection.
- `app/image_analysis.py`: analyzes image brightness, contrast, sharpness, and edge density.
- `app/routes.py`: defines the application endpoints, file upload routes, and protected pages.
- `app/templates/`: stores the HTML pages for login, registration, dashboard, results, and history.
- `app/static/script.js`: draws the telemetry anomaly chart and handles simple front-end behavior.
- `tests/`: contains unit tests for database behavior, report explanations, and analysis functions.

---

## 12. Application Architecture

AERIS follows a simple Flask architecture:

1. The user interacts with the browser interface.
2. Flask routes receive requests from the login, dashboard, upload, results, and history pages.
3. The application validates user data and uploaded file types.
4. Analysis functions process the file and compute metrics.
5. The database layer saves the result and history metadata.
6. The result page renders the summary, charts, and explanations.
7. The history page queries user-specific records and supports deletion.

At a high level, the architecture is:

- Front end: HTML templates + CSS + JavaScript
- Application layer: Flask routes and business logic
- Analysis layer: telemetry and image analysis modules
- Data layer: PostgreSQL database
- Security layer: password hashing, sessions, and OAuth

This structure is simple, educational, and easy to understand, which is appropriate for a school capstone project.

---

## 13. Installation and Setup

Follow these general steps to set up the project on a local machine or other compatible environment.

### 13.1 Prerequisites

- Python 3.12
- PostgreSQL database access
- A configured environment for environment variables
- Internet access if Google OAuth is enabled

### 13.2 Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 13.3 Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 13.4 Configure environment variables

Create a `.env` file in the project root and define the required settings:

- `SECRET_KEY`
- `DATABASE_URL`

Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` if Google sign-in is enabled.
Use a strong, randomly generated `SECRET_KEY`; there is no built-in default.

Do not commit real secrets to version control. Use secure values in local or hosted environments.

### 13.5 Initialize the database

The application calls `init_db()` when the app starts. This creates the required tables if they are not present.

### 13.6 Run the application

```powershell
python run.py
```

Then open the app in a browser, usually at:

- `http://127.0.0.1:5000`

The development server uses `PORT` when it is set and otherwise listens on port
5000. The `PORT` setting is supplied automatically by Railway.

---

## 14. Environment Variables and Configuration Requirements

The project relies on environment variables from `.env`.

### Required variables

- `DATABASE_URL`: PostgreSQL connection string for the application database.
- `SECRET_KEY`: used by Flask for sessions and secure application behavior.

### Optional or supporting variables

- `FLASK_APP`: used by Flask conventions.
- `FLASK_ENV`: used to indicate development or deployment context.
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`: required only when Google sign-in is used.
- `GOOGLE_REDIRECT_URI`: optional explicit Google OAuth callback URL; if omitted, it is generated from the incoming request.
- `SESSION_COOKIE_SECURE`: set to `true` when serving the site over HTTPS.
- `UPLOAD_FOLDER`: optional temporary upload directory; defaults to the operating system's temporary directory.
- `MAX_CONTENT_LENGTH`: set to 16 MB in the app config.

The application reads these variables using `python-dotenv` and the project is designed to work with a standard environment file rather than hard-coded secrets.

> Important: Never add actual credentials to the repository. Store sensitive values in a local environment, deployment secret manager, or host-managed config system.

---

## 15. How to Run the Application

From the project root:

```powershell
python run.py
```

This starts the Flask development server on `0.0.0.0` using `PORT` (5000 when
the variable is not set).

### Railway deployment

Railway uses the included `Procfile` to start the application with Gunicorn.
The service listens on Railway's assigned `$PORT`; it does not use Flask's
development server. Python is pinned to 3.12 by `.python-version`.

Configure these Railway variables:

- `SECRET_KEY`: a strong, randomly generated value.
- `DATABASE_URL`: the existing Neon PostgreSQL connection string (including its SSL setting, such as `sslmode=require`).
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`: if Google sign-in is enabled.
- `SESSION_COOKIE_SECURE`: `true` to restrict session cookies to HTTPS.
- `GOOGLE_REDIRECT_URI`: optional; set it to `https://<your-railway-domain>/google/callback` to explicitly pin the callback URL.

After Railway provides a domain, add
`https://<your-railway-domain>/google/callback` to the authorized redirect URIs
for the Google OAuth client. Uploads are stored temporarily and removed after
analysis; the application does not depend on deployment storage persisting
uploaded files.

---

## 16. How to Use Each Major Feature

### 16.1 Registration

- Open the app.
- Click “Register”.
- Enter a name, email, and password with at least 8 characters.
- Submit the form.
- If the email is unique, the account is created.

### 16.2 Login

- Use the registered email and password.
- Or click “Continue with Google” to use OAuth.
- After login, the dashboard is displayed.

### 16.3 Dashboard

The dashboard shows:

- welcome message,
- status cards,
- upload forms for telemetry and image analysis,
- recent analysis activity.

### 16.4 Telemetry upload

- Choose a CSV file containing numeric readings.
- Click “Analyze Telemetry”.
- The system validates the file and runs the anomaly-detection analysis.
- Results include counts, chart data, and statistical summaries.

### 16.5 Image upload

- Choose a `.jpg`, `.jpeg`, or `.png` image.
- Click “Analyze Image”.
- The system calculates image brightness, contrast, sharpness, and edge density.
- A summary and interpretation appear on the result page.

### 16.6 History page

- Visit “History” from the dashboard or navigation bar.
- Review previous analyses.
- Delete any record associated with the signed-in user.

---

## 17. Testing and Verification

The project includes automated tests for the key logic.

Run the verification suite with:

```powershell
python -m unittest discover -s tests -v
```

The current tests cover:

- database schema setup,
- UUID and integer ID handling,
- analysis save/delete logic,
- telemetry plain-language explanation generation,
- image explanation generation,
- route-level behavior for report output and deletion logic.

These checks confirm that the application’s core functions behave as expected in the project’s current state.

---

## 18. Important Limitations of the Current Analysis Methods

This project is a useful educational prototype, but it has several limitations that should be recognized.

1. Telemetry analysis is based on statistical outlier detection, not a trained spacecraft fault model.
2. The model does not identify the exact cause of a fault; it only highlights unusual patterns.
3. The image analysis computes visual characteristics, not actual defect detection or component recognition.
4. The system does not classify damage types such as cracks, leaks, overheating, or structural failures.
5. It depends on the quality and structure of uploaded data.
6. It requires at least five usable observations for telemetry analysis.
7. Non-numeric data is ignored in the telemetry workflow.
8. The project is designed for educational and prototype demonstration rather than operational deployment.

This honesty is important for responsible AI use and technical evaluation.

---

## 19. Security Considerations

The application includes some essential security practices, but it should not be treated as a fully hardened production system without further review.

Current security-related features include:

- password hashing with Werkzeug,
- unique email validation,
- user-specific history access and deletion checks,
- secure filename handling via `secure_filename`,
- session-based user authentication,
- restriction of uploads to allowed file extensions,
- maximum upload file size limit.

Recommended further considerations for deployment:

- keep secrets in environment variables or a secret manager,
- enforce HTTPS in production,
- restrict database access to trusted environments,
- add rate limiting and stronger authentication controls if used beyond a classroom demo,
- validate user input more thoroughly in larger deployments,
- use a production-grade WSGI server and secure reverse-proxy configuration.

---

## 20. Future Improvements

The current project leaves room for several enhancements:

- integrate a real spacecraft telemetry dataset for richer testing,
- add support for time-series visualization and trend analysis,
- include more advanced anomaly detection or forecasting methods,
- classify different types of equipment health issues,
- improve image analysis with object detection or segmentation,
- add report export in PDF or CSV format,
- provide admin features and audit logs,
- improve multi-user role management,
- add better form validation and error handling,
- create a more advanced dashboard with editable settings and summaries.

These improvements would move the project from a prototype toward a more complete engineering support system.

---

## 21. Project Conclusion

AERIS demonstrates how a real-world engineering problem can be addressed through an AI-powered web application. It combines user authentication, data analysis, visual interpretation, and database-driven history tracking into a single educational project.

The application is useful for understanding how:

- unsupervised learning can identify unusual telemetry patterns,
- computer vision can compute meaningful image indicators,
- software can translate raw technical output into simple explanations,
- a full workflow can be designed around user interaction and data review.

Although the current analysis is intentionally limited and designed for educational use, the project successfully shows the practical value of combining AI, software engineering, and aerospace-inspired problem solving.

---

## 22. Acknowledgements

This project is developed as a Class XII CBSE AI Capstone Project. It uses open-source Python libraries and demonstrates a realistic approach to building a small intelligent application for engineering analysis.

Special appreciation is due to the open-source developer communities behind Flask, pandas, NumPy, scikit-learn, OpenCV, and Authlib for making accessible, practical tools available for learning and prototyping.

---

## 23. Summary

AERIS is a practical educational web application for analyzing spacecraft-related telemetry and image data. It supports user registration, Google login, secure session management, CSV anomaly detection, image metric analysis, result explanation, and history tracking in a PostgreSQL database. The project is intentionally designed to be understandable, adaptable, and suitable for technical evaluation while remaining honest about the bounds of its current analysis methods.
