# AlgoDash [WORK IN PROGRESS, GITHUB MIGHT NOT ALWAYS BE UPDATED]

A personalized DSA & competitive programming dashboard that guides without giving shortcuts.

## Overview

AlgoDash is a web-based dashboard that aggregates competitive programming data from multiple platforms and provides personalized insights, problem recommendations, and AI-guided feedback—without ever revealing solutions or code.

Unlike traditional DSA tools that optimize for speed or output, AlgoDash is designed to preserve real problem-solving ability while still offering structured guidance.

## Key Features

### Unified Performance Dashboard
- Visualizes stats from LeetCode, Codeforces, and CodeChef (at least one required)

### Weakness-Driven Recommendations
- Suggests problems and contests based on topic/tag gaps instead of random practice

### AI-Powered Daily Feedback (No Solutions)
- Reflect on failed submissions  
- Makes you rethink approaches  
- Get concept-level guidance  
- Helps set concrete, time-bound goals  

### Learning-First Chatbot
- The chatbot never reveals solutions or code—only reasoning help and conceptual nudges

## Tech Stack

### Backend
- Flask  
- Groq API (AI inference)  
- Supabase (Auth + Database)  

### Frontend
- Jinja templates  
- HTML / CSS  

### Data Sources
- Codeforces (official)  
- LeetCode, CodeChef, GFG (via third-party APIs)  

> ⚠️ The `api/` directory is not included by default and must be set up manually (see below).

## Setup Guide

### 1. Clone the AlgoDash repository
```bash
git clone https://github.com/Aruniaaa/AlgoDash
cd AlgoDash
````

### 2. Clone the required API repository inside the project

AlgoDash depends on an external API wrapper for fetching LeetCode, CodeChef, and GFG data.

Clone it inside the AlgoDash root directory:

```bash
git clone https://github.com/coder-writes/leetcode-gfg-codechef-api api
```

Your folder structure should now include:

```
AlgoDash/
└── api/
```

If this repo is missing or placed elsewhere, platform data fetching will fail.

### 3. Create a virtual environment & install dependencies

```bash
python -m venv venv
source venv/bin/activate
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the root directory and add:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

GROQ_API_KEY=your_groq_api_key

SECRET_KEY=your_flask_secret_key
```

**Note:**
AlgoDash uses two Supabase clients:

* Public (anon key) for safe reads
* Service role key for secure inserts/updates (feedback, timestamps)

### 5. Run the application

```bash
cd api
npm start
python views.py
```

The app will be available at:

```
http://localhost:5000
```

## Important Design Decisions

### No AI Solutions — By Design

AlgoDash intentionally blocks:

* Code generation
* Full solutions
* Direct answers

This is not a limitation—it’s the core philosophy.

The AI assists with how to think, not what to write.

### Caching Strategy

To reduce repeated API calls and improve load times:

* Flask-level caching is used for frequently accessed stats

This significantly improves dashboard responsiveness.

## Known Limitations

* CodeChef API restrictions limit detailed data access
  → Feedback is generated using aggregated performance instead
* Requires at least one connected platform profile

## Contributing

Contributions are welcome, especially around:

* API integrations
* UI/UX improvements
* Analytics depth

Please open an issue before submitting major changes.

## License

All rights reserved.
