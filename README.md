# AuroraFIM: Advanced File Integrity Monitoring (FIM) with UBA

## 🌟 Project Overview

**AuroraFIM Pro** is a robust, cross-platform security application designed to protect critical system files and directories from unauthorized modification. Built on Python and PySide6, this system moves beyond simple file comparison by integrating **User Behavior Analytics (UBA)** and **Risk Scoring** to detect potential insider threats and anomalous user activity in real-time.

This project successfully demonstrates core FIM functions alongside advanced predictive security measures for your college showcase.

## ✨ Core Features

| Category | Feature | Description |
| :--- | :--- | :--- |
| **Integrity** | **Real-time FIM** | Uses `watchdog` to instantly detect and log file changes (MODIFIED, DELETED, CREATED) in monitored directories. |
| | **Secure Baselining** | Files are fingerprinted using SHA256 hashing. The baseline is protected by a separate HMAC signature for tamper verification. |
| **Security** | **User Behavior Profiling (UBA)** | Automatically builds a 30-day baseline of "normal" activity, tracking average logins, file changes, and file types modified. |
| | **Anomaly Detection & Risk Scoring** | Assigns a dynamic risk score (Normal, Suspicious, High Risk) based on deviations from a user's established profile (e.g., mass file changes, unusual login times). |
| | **Role-Based Access Control (RBAC)** | Enforces permissions for `admin`, `auditor`, and `viewer` roles, protected by secure `bcrypt` hashing. |
| **Operations**| **Visualization Dashboard** | Provides a dedicated dashboard for viewing risk scores, user profiles, and activity summary tables. |
| | **Reporting** | Generates detailed PDF audit reports containing all FIM events and summaries. |


## 🏗️ Architecture and Components

The application adheres to a modular architecture using SQLite for persistent data storage:

* **GUI (`gui/`):** Utilizes **PySide6** for the front-end. It runs demanding tasks (like FIM scans and risk assessment) asynchronously in separate worker threads to keep the UI responsive.
* **Core (`core/`):** Contains the engine logic:
    * `FIMEngine`: Manages monitoring, baseline comparisons, and signals real-time events.
    * `AuthHandler`: Handles user security and session management.
    * `UserProfiler` (Conceptual): Runs the UBA calculations against the activity logs.
* **Database:** A single **`aurorafim.db`** file manages three key tables: `users`, `fim_events`, and `user_profiles`.


## 🚀 Getting Started (Installation)

Follow these steps to set up the project environment and install dependencies.

### 1. Project Setup

1.  **Clone the Repository:** Download or clone the project files to your local machine.
2.  **Navigate to Project Root:** Open your terminal and change directory to the project's root folder (the folder containing `aurorafimpro/`).
    ```bash
    cd path/to/AuroraFIM-Pro
    ```

### 2. Environment and Dependencies

You must install specific libraries for security and visualization.

1.  **Create & Activate Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate.bat # Windows
    ```

2.  **Install Dependencies:** Install all required libraries using pip:
    ```bash
    pip install PySide6 py-bcrypt reportlab watchdog Pillow
    ```

### 3. Run the Application

1.  Start the application from the root directory:
    ```bash
    python3 aurorafimpro/main.py
    ```
2.  The system will automatically initialize the database (`aurorafim.db`) and create the default admin user.

---

## 💡 Running the UBA Anomaly Demonstration

Use this workflow to demonstrate the UBA system's ability to detect anomalous behavior.

### 🔑 Default Credentials

| Username | Password | Role |
| :--- | :--- | :--- |
| `admin` | `admin` | Administrator |

### Demo Steps

1.  **Establish Baseline (First Time Only):**
    * Log in as `admin`.
    * Navigate to the **UBA Dashboard** tab.
    * Click **Manual Recalculate Profiles**. This simulates a month of "normal" login/file activity for the existing users (in this case, just `admin`) and creates a profile for the simulated attacker with an initial baseline of 0.

2.  **Run the Attack Simulation:**
    * Navigate back to the **Dashboard** tab.
    * Click **UBA: Run Anomaly Simulation**.
    * Confirm the prompt.
    * The simulator instantly logs over **25 file changes** and a **restricted file access** event for the user `sim_attacker`.

3.  **View the High-Risk Alert:**
    * The simulation handler automatically triggers the periodic risk assessment.
    * You should immediately see a **"UBA High Risk Alert"** tray notification and a status bar message.

4.  **Inspect the Anomaly:**
    * Navigate to the **UBA Dashboard** tab.
    * The **Suspicious Activity Summary** table will now list **`sim_attacker`** with a score of **70+** (High Risk), detailing that the anomalous events were successfully detected.

This process demonstrates the project's real-time monitoring, security logging, and advanced behavioral analysis in a concise, high-impact manner.
