# 📮 PostBot — India Post Infrastructure AI

**Great Lakes PGP Data Science & GenAI | Batch Sep 2025–Apr 2026**

An AI-powered decision support system for India Post officers to analyse district postal infrastructure, understand delivery performance, and get targeted recommendations.

---

## 🚀 Live Demo

> Deployed on Streamlit Cloud → *https://postbot-5gnefgmmr9pq4p36fmd4jz.streamlit.app/*

---

## 📌 What PostBot Does

| Feature | Description |
|---------|-------------|
| 📦 Real Data | Actual BO / PO / HO counts for 754 districts across 36 states |
| 📊 Delivery Analysis | Current delivery rate + performance tier (Low / Moderate / Good / High) |
| 💡 Smart Suggestions | Exact number of Branch Offices to add to reach next tier |
| 🤖 AI Chatbot | Ask anything — powered by Groq Llama 3.3 70B (free) |
| 🔐 Secure Login | Officer ID + password authentication |

---

## 🗂️ Folder Structure

```
PostBot/
├── app.py                      ← Main Streamlit application
├── auth.py                     ← Officer login & authentication
├── chatbot.py                  ← Groq AI chatbot brain
├── model_utils.py              ← ML prediction & suggestion logic
├── district_aggregated.csv     ← Real India Post dataset (754 districts)
├── requirements.txt            ← Python dependencies
├── .gitignore                  ← Protects .env from being uploaded
├── README.md                   ← This file
└── .streamlit/
    ├── config.toml             ← Streamlit theme & server settings
    └── secrets.toml.example    ← Template (copy → secrets.toml locally)
```

---

## 🔐 Login Credentials

| Officer ID | Password | Name | Circle |
|-----------|----------|------|--------|
| IP2024KA001 | post@Karnataka | Ravi Kumar | Karnataka |
| IP2024MH001 | post@Maharashtra | Priya Desai | Maharashtra |
| IP2024TN001 | post@TamilNadu | Arjun Raj | Tamil Nadu |
| IP2024GJ001 | post@Gujarat | Neha Shah | Gujarat |
| DEMO | demo123 | Demo Officer | All India |

---

## ⚙️ Run Locally

### Step 1 — Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/PostBot.git
cd PostBot
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Add your Groq API key
Create a file called `.env` in the project folder:
```
GROQ_API_KEY=gsk_your_key_here
```
Get a **free** Groq key at → [console.groq.com](https://console.groq.com)

### Step 4 — Run the app
```bash
streamlit run app.py
```
Opens at → `http://localhost:8501`

---

## ☁️ Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo → branch: `main` → Main file: `app.py`
4. Click **Deploy**
5. Go to **Settings → Secrets** and add:
```
GROQ_API_KEY = "gsk_your_actual_key_here"
```

---

## 🤖 AI & ML Details

| Component | Details |
|-----------|---------|
| Prediction Model | CatBoost Regressor (R² = 0.9243) |
| Target Variable | `district_delivery_rate` (0–1) |
| Key Predictor | BO Ratio (Pearson r = +0.87) |
| AI Chatbot | Groq Llama 3.3 70B Versatile (Free — 14,400 req/day) |
| Dataset | 165,627 India Post offices → aggregated to 754 districts |

### Performance Tiers
| Tier | Delivery Rate | BO Ratio |
|------|--------------|---------|
| 🟢 High Performance | > 95% | ~90.5% |
| 🔵 Good Performance | 85–95% | ~86.1% |
| 🟡 Moderate Performance | 70–85% | ~83.0% |
| 🔴 Low Performance | < 70% | ~15.9% |

---
**Author:** Murali Manohara

**Mentor:** Mr. Aishwarya Sarda  
**Program:** PGP in Data Science & GenAI, Great Lakes Institute of Management

---

## 📄 License

This project is built for academic purposes as part of the Great Lakes PGP Capstone.
