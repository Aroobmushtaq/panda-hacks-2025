---
title: "StudyQuest"
emoji: "📚"
colorFrom: "red"
colorTo: "red"
sdk: "streamlit"
sdk_version: "1.48.0"
app_file: "app.py"
pinned: false
---
# 🎮 StudyQuest - AI-Powered Gamified Learning

Transform your study sessions into exciting adventures! StudyQuest uses AI to generate personalized learning challenges, track your progress, and reward you with XP, badges, and streaks.

## ✨ Features

### 🎯 Core Functionality
- **AI Quest Generator**: Input any topic and get personalized quiz questions
- **Instant AI Feedback**: Get explanations and encouragement from AI tutors
- **Gamification**: Earn XP, unlock badges, and maintain daily streaks
- **Progress Dashboard**: Track your learning journey across subjects
- **Focus Mode**: Pomodoro timer with AI-generated break activities

### 🤖 AI Integration
- **Hugging Face API**: Powers quest generation using Mistral-7B-Instruct
- **Groq API**: Provides ultra-fast feedback using Llama3-8B-8192
- **Smart Prompting**: Optimized prompts for educational content

### 🎨 User Experience
- Colorful, gamified interface designed for high school students
- Real-time progress tracking and streak counters
- Motivational quotes and achievement system
- Responsive design with modern gradients and animations

## 🚀 Quick Start

### Option 1: Deploy to Hugging Face Spaces (Recommended)

1. **Create a new Hugging Face Space**:
   - Go to [Hugging Face Spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose "Streamlit" as the SDK
   - Name it "studyquest" or your preferred name

2. **Upload the files**:
   - Upload `app.py`, `requirements.txt`, and `README.md`
   - The space will automatically start building

3. **Set up API keys** (IMPORTANT):
   - Go to your Space settings
   - Click on "Variables and secrets"
   - Add these secrets:
     - `HF_API_KEY`: Your Hugging Face API key
     - `GROQ_API_KEY`: Your Groq API key

4. **Get your API keys**:
   - **Hugging Face**: Get from [HF Settings > Access Tokens](https://huggingface.co/settings/tokens)
   - **Groq**: Sign up at [Groq Cloud](https://console.groq.com/) and get API key

### Option 2: Run Locally

1. **Clone and setup**:
```bash
git clone <your-repo>
cd studyquest
pip install -r requirements.txt
```

2. **Create `.env` file**:
```env
HF_API_KEY=your_hugging_face_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

3. **Run the app**:
```bash
streamlit run app.py
```

## 🔧 Configuration

### API Models Used
- **Hugging Face**: `mistralai/Mistral-7B-Instruct-v0.2` for quest generation
- **Groq**: `llama3-8b-8192` for instant feedback and explanations

### Customization Options
- Modify badge thresholds in the `check_badges()` function
- Add new subjects or difficulty levels
- Customize XP rewards for different activities
- Change timer durations in Focus Mode

## 📱 How to Use StudyQuest

### 🏠 Home Tab
1. Enter your study topic (e.g., "Algebra", "World History")
2. Select difficulty level (easy/medium/hard)
3. Set your study time
4. Click "Generate Quest" to create AI-powered questions

### ⚔️ Quests Tab
1. Answer the generated questions
2. Use hints when needed
3. Get instant AI feedback on your answers
4. Earn XP for correct answers

### 📊 Dashboard Tab
- View your total XP and current level
- Check your daily streak
- See subjects you've mastered
- Display your earned badges

### ⏱️ Focus Mode Tab
- Start 25-minute Pomodoro focus sessions
- Get AI trivia during 5-minute breaks
- Earn bonus XP for completed sessions

## 🏆 Gamification System

### XP (Experience Points)
- **Correct Answer**: 50 XP
- **Completed Focus Session**: 25 XP
- **Daily Study Goal**: Bonus XP

### Badges
- 🌟 **First Steps**: 100 XP
- 🎯 **Focused Learner**: 500 XP
- 🏆 **Study Champion**: 1000 XP
- 🎓 **Academic Master**: 2500 XP
- 🦸 **Learning Hero**: 5000 XP

### Streaks
- 🔥 **Hot Streak**: 3 days
- ⚡ **Weekly Warrior**: 7 days
- 🚀 **Study Rocket**: 14 days
- 💎 **Diamond Dedication**: 30 days

## 🛠️ Technical Details

### Architecture
```
StudyQuest/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── user_data.json     # Local storage (auto-generated)
└── .env              # Environment variables (local only)
```

### Data Storage
- **Local Mode**: JSON file storage for user progress
- **Production**: All data stored in memory/session state
- **Future**: Can be extended with Firebase or PostgreSQL

### API Integration
- **Error Handling**: Graceful fallbacks if APIs are unavailable
- **Rate Limiting**: Built-in request management
- **Retry Logic**: Automatic retries for failed requests

## 🔒 Security & Privacy

- API keys stored securely in environment variables
- No personal data collected beyond study progress
- All data stays local or in your Hugging Face Space
- No external tracking or analytics

## 🤝 Contributing

Want to improve StudyQuest? Here are some ideas:

### 🆕 Feature Ideas
- **Multiplayer Mode**: Compete with friends
- **Subject Categories**: Organize topics better
- **Study Plans**: Long-term learning paths
- **Voice Mode**: Audio questions and answers
- **Mobile App**: React Native version
- **Analytics**: Detailed progress reports


-