# 🚀 AuroraFIM

AuroraFIM is a real-time File Integrity Monitoring (FIM) and User Behavior Analytics (UBA) system designed to detect unauthorized file changes and potential insider threats through behavioral analysis and system monitoring.

---

## 🔍 Overview

AuroraFIM continuously monitors file system activity and user behavior to identify suspicious patterns. It combines integrity checking, behavioral profiling, and performance monitoring into a unified system with a modern GUI dashboard.

---

## ✨ Key Features

### 🔐 File Integrity Monitoring (FIM)
- Detects unauthorized file modifications
- Tracks file creation, deletion, and updates
- Hash-based integrity verification

### 👤 User Behavior Analytics (UBA)
- Profiles user activity patterns
- Detects anomalies in behavior
- Logs user actions for analysis

### 📊 Analytics & Metrics
- Real-time metrics collection
- Behavioral insights and trends
- Performance monitoring (CPU, memory, system activity)

### 🖥️ GUI Dashboard (PySide6)
- Interactive and modern interface
- Visual analytics and charts
- User activity logs and alerts

### 🗄️ Database Integration
- Efficient data storage using structured DB layer
- Connection pooling via db_pool
- Persistent logging and reporting

---
## 🏗️ Project Structure
FIM/
├── aurorafimpro/
│   ├── core/          # Authentication, hashing, monitoring, reporting, logging
│   ├── database/      # SQLite setup and initialization
│   ├── gui/           # Main window, dialogs, widgets, styles
│   ├── main.py        # Application entry point
│   └── config.py      # App configuration and theme settings
├── audit_reports/     # Generated PDF reports
├── baseline.json      # Baseline integrity data
├── baseline.sig       # Baseline signature
├── file_snapshots/    # Snapshot data used by the monitor
├── logs/              # Runtime logs
└── requirements.txt   # Python dependencies

---

## ⚙️ How It Works

1. File Monitoring
   - Watches directories for changes
   - Computes file hashes to detect tampering

2. Behavior Tracking
   - Records user actions and system interactions
   - Builds behavioral profiles

3. Anomaly Detection
   - Compares real-time activity with baseline patterns
   - Flags suspicious behavior

4. Visualization
   - Displays metrics, logs, and alerts in GUI dashboard

---

## 🛠️ Tech Stack

- Language: Python  
- GUI: PySide6 (Qt Framework)  
- Database: SQLite (via custom DB layer)  
- Architecture: Modular (Core + GUI + Database)

---

## 🚀 Getting Started

### 1. Clone the repository
bash git clone https://github.com/tejassambhus17/AuroraFIM.git cd AuroraFIM 

### 2. Install dependencies
bash pip install -r requirements.txt 

### 3. Run the application
bash python main.py 

---

## 📊 Example Use Cases

- Detect unauthorized file changes in sensitive directories  
- Monitor insider threats in enterprise environments  
- Analyze user activity patterns for anomalies  
- Build security dashboards for system monitoring  

---

## 📌 Future Improvements

- Machine learning-based anomaly detection  
- Real-time alerts/notifications  
- Distributed monitoring support  
- Web-based dashboard  

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork the repo and submit pull requests.

---

## 📜 License

This project is for educational and research purposes.

---

## 👤 Author

**Tejas Sambhus**
