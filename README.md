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

```
AuroraFIM/
│
├── core/                  # Core logic and processing
│   ├── auth.py
│   ├── db_pool.py
│   ├── fim.py
│   ├── hashing.py
│   ├── logger.py
│   ├── metrics_api.py
│   ├── performance_monitor.py
│   ├── reporting.py
│   ├── simulator.py
│   ├── user_profiler.py
│   └── validators.py
│
├── gui/                   # GUI components (PySide6)
│   ├── main_window.py
│   ├── modern_components.py
│   ├── modern_style.py
│   └── widgets/
│       ├── dashboard_widget.py
│       ├── login_dialog.py
│       ├── uba_dashboard_widget.py
│       ├── behavior_chart_widget.py
│       └── ...
│
├── database/              # Database setup and management
│   └── db_setup.py
│
├── config.py
├── main.py
├── tests.py
├── .gitignore
└── README.md
```

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
