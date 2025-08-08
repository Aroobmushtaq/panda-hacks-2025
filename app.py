import streamlit as st
import json
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random

# Configure Streamlit page
st.set_page_config(
    page_title="StudyQuest 🎮",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for gamified UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .xp-badge {
        background: linear-gradient(45deg, #ffd700, #ffed4e);
        color: #333;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .streak-counter {
        background: linear-gradient(45deg, #ff6b6b, #ffa500);
        color: white;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
    }
    .quest-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
        margin: 15px 0;
    }
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
        margin: 20px 0;
    }
    .badge {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 10px 15px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .focus-timer {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        color: white;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = {
        'xp': 0,
        'total_xp': 0,
        'streak': 0,
        'last_activity': None,
        'badges': [],
        'subjects_studied': {},
        'daily_xp': 0,
        'timer_active': False,
        'timer_start': None,
        'break_time': False
    }

# Load user data from file
def load_user_data():
    try:
        if os.path.exists('user_data.json'):
            with open('user_data.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return st.session_state.user_data

# Save user data to file
def save_user_data(data):
    try:
        with open('user_data.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except:
        pass

# Load data on app start
st.session_state.user_data = load_user_data()

# API Configuration
HF_API_KEY = os.getenv("HF_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Hugging Face API calls
def call_huggingface_api(prompt: str, model: str = "mistralai/Mistral-7B-Instruct-v0.2") -> Optional[str]:
    if not HF_API_KEY:
        st.error("Hugging Face API key not found. Please set HF_API_KEY in environment variables.")
        return None
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    url = f"https://api-inference.huggingface.co/models/{model}"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.7,
            "do_sample": True
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "").replace(prompt, "").strip()
        return result.get("generated_text", "").replace(prompt, "").strip()
    except Exception as e:
        st.error(f"Hugging Face API error: {str(e)}")
        return None

# Groq API calls
def call_groq_api(prompt: str, model: str = "llama3-8b-8192") -> Optional[str]:
    if not GROQ_API_KEY:
        st.error("Groq API key not found. Please set GROQ_API_KEY in environment variables.")
        return None
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": model,
        "max_tokens": 300,
        "temperature": 0.7
    }
    
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                               headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Groq API error: {str(e)}")
        return None

# Generate AI quests
def generate_quest(topic: str, difficulty: str = "medium") -> Optional[List[Dict]]:
    prompt = f"""Create 3 multiple-choice quiz questions for a high school student studying {topic} at {difficulty} level. 
    Return ONLY a valid JSON array with this exact format:
    [
      {{
        "question": "Question text here",
        "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
        "answer": "A",
        "hint": "Helpful hint here",
        "xp": 50
      }}
    ]
    Make questions engaging and educational."""
    
    response = call_huggingface_api(prompt)
    if not response:
        return None
    
    try:
        # Try to extract JSON from response
        start_idx = response.find('[')
        end_idx = response.rfind(']') + 1
        if start_idx != -1 and end_idx != -1:
            json_str = response[start_idx:end_idx]
            questions = json.loads(json_str)
            return questions
    except:
        pass
    
    # Fallback questions if API fails
    return [
        {
            "question": f"What is an important concept in {topic}?",
            "options": ["A) Concept A", "B) Concept B", "C) Concept C", "D) All of the above"],
            "answer": "D",
            "hint": f"Think about the key principles of {topic}",
            "xp": 50
        }
    ]

# Update streak and XP
def update_progress(xp_gained: int, subject: str):
    today = datetime.now().date()
    last_activity = st.session_state.user_data.get('last_activity')
    
    # Update streak
    if last_activity:
        last_date = datetime.fromisoformat(last_activity).date()
        if today == last_date:
            pass  # Same day, maintain streak
        elif today == last_date + timedelta(days=1):
            st.session_state.user_data['streak'] += 1
        else:
            st.session_state.user_data['streak'] = 1
    else:
        st.session_state.user_data['streak'] = 1
    
    # Update XP
    st.session_state.user_data['xp'] += xp_gained
    st.session_state.user_data['total_xp'] += xp_gained
    st.session_state.user_data['daily_xp'] += xp_gained
    st.session_state.user_data['last_activity'] = today.isoformat()
    
    # Update subjects studied
    if subject not in st.session_state.user_data['subjects_studied']:
        st.session_state.user_data['subjects_studied'][subject] = 0
    st.session_state.user_data['subjects_studied'][subject] += xp_gained
    
    # Check for new badges
    check_badges()
    save_user_data(st.session_state.user_data)

# Badge system
def check_badges():
    badges = st.session_state.user_data['badges']
    total_xp = st.session_state.user_data['total_xp']
    streak = st.session_state.user_data['streak']
    
    badge_thresholds = [
        (100, "🌟 First Steps", "Earned your first 100 XP!"),
        (500, "🎯 Focused Learner", "Reached 500 XP milestone!"),
        (1000, "🏆 Study Champion", "Achieved 1000 XP!"),
        (2500, "🎓 Academic Master", "Reached 2500 XP!"),
        (5000, "🦸 Learning Hero", "Epic 5000 XP achievement!")
    ]
    
    streak_badges = [
        (3, "🔥 Hot Streak", "3 days in a row!"),
        (7, "⚡ Weekly Warrior", "7 day streak!"),
        (14, "🚀 Study Rocket", "2 weeks strong!"),
        (30, "💎 Diamond Dedication", "30 day streak!")
    ]
    
    for threshold, title, desc in badge_thresholds:
        if total_xp >= threshold and title not in badges:
            badges.append(title)
            st.success(f"🎉 New Badge Unlocked: {title}!")
    
    for threshold, title, desc in streak_badges:
        if streak >= threshold and title not in badges:
            badges.append(title)
            st.success(f"🎉 Streak Badge Unlocked: {title}!")

# Motivational quotes
def get_motivational_quote():
    quotes = [
        "🌟 Every expert was once a beginner!",
        "🚀 Success is the sum of small efforts repeated daily!",
        "💪 You're making progress with every question!",
        "🎯 Focus on progress, not perfection!",
        "⭐ Great job staying consistent!",
        "🏆 Champions are made in study sessions like this!",
        "🔥 Your dedication is paying off!",
        "💎 Persistence is the key to mastery!"
    ]
    return random.choice(quotes)

# Main app layout
st.markdown('<div class="main-header"><h1>🎮 StudyQuest</h1><p>Level up your learning with AI-powered quests!</p></div>', 
            unsafe_allow_html=True)

# Sidebar with user stats
with st.sidebar:
    st.header("🏆 Your Progress")
    
    # XP Display
    st.markdown(f'<div class="xp-badge">⭐ {st.session_state.user_data["xp"]} XP</div>', 
                unsafe_allow_html=True)
    
    # Streak counter
    st.markdown(f'''<div class="streak-counter">
        🔥 {st.session_state.user_data["streak"]} Day Streak!
    </div>''', unsafe_allow_html=True)
    
    # Level calculation
    level = st.session_state.user_data['total_xp'] // 100 + 1
    xp_for_next = 100 - (st.session_state.user_data['total_xp'] % 100)
    st.progress((st.session_state.user_data['total_xp'] % 100) / 100)
    st.write(f"📊 Level {level} • {xp_for_next} XP to next level")
    
    # Badges
    if st.session_state.user_data['badges']:
        st.subheader("🏅 Your Badges")
        for badge in st.session_state.user_data['badges']:
            st.markdown(f'<div class="badge">{badge}</div>', unsafe_allow_html=True)

# Main app tabs
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home", "⚔️ Quests", "📊 Dashboard", "⏱️ Focus Mode"])

with tab1:
    st.header("🎯 Start Your Learning Adventure!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📚 Create Your Quest")
        
        topic = st.text_input("What would you like to study?", 
                            placeholder="e.g., Algebra, World History, Biology...")
        
        difficulty = st.selectbox("Choose difficulty:", 
                                ["easy", "medium", "hard"])
        
        study_time = st.slider("How long will you study? (minutes)", 
                             5, 120, 25)
        
        if st.button("🚀 Generate Quest", type="primary"):
            if topic:
                with st.spinner("🎲 AI is crafting your personalized quest..."):
                    quest_data = generate_quest(topic, difficulty)
                    if quest_data:
                        st.session_state.current_quest = quest_data
                        st.session_state.quest_topic = topic
                        st.success("✅ Quest generated! Go to the Quests tab to begin!")
                    else:
                        st.error("Failed to generate quest. Please try again.")
            else:
                st.warning("Please enter a topic first!")
    
    with col2:
        st.subheader("💫 Daily Motivation")
        quote = get_motivational_quote()
        st.info(quote)
        
        if st.session_state.user_data['daily_xp'] > 0:
            st.metric("Today's XP", st.session_state.user_data['daily_xp'])

with tab2:
    st.header("⚔️ Your Current Quest")
    
    if 'current_quest' in st.session_state and st.session_state.current_quest:
        quest = st.session_state.current_quest
        topic = st.session_state.get('quest_topic', 'Unknown')
        
        st.subheader(f"📖 {topic} Challenge")
        
        for i, question_data in enumerate(quest):
            st.markdown(f'<div class="quest-card">', unsafe_allow_html=True)
            st.write(f"**Question {i+1}:** {question_data['question']}")
            
            # Create unique key for each question
            answer_key = f"answer_{i}"
            
            selected = st.radio(
                "Choose your answer:",
                question_data['options'],
                key=answer_key,
                index=None
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"💡 Hint", key=f"hint_{i}"):
                    st.info(f"💭 {question_data['hint']}")
            
            with col2:
                if st.button(f"✅ Submit Answer", key=f"submit_{i}"):
                    if selected:
                        correct_answer = question_data['answer']
                        if selected.startswith(correct_answer):
                            st.success("🎉 Correct! Great job!")
                            xp_gained = question_data.get('xp', 50)
                            update_progress(xp_gained, topic)
                            
                            # Get AI feedback
                            feedback_prompt = f"Give encouraging feedback for correctly answering: {question_data['question']}"
                            feedback = call_groq_api(feedback_prompt)
                            if feedback:
                                st.info(f"🤖 AI Coach: {feedback}")
                        else:
                            st.error("❌ Not quite right. Try again!")
                            explanation_prompt = f"Explain why the answer to '{question_data['question']}' is {correct_answer}"
                            explanation = call_groq_api(explanation_prompt)
                            if explanation:
                                st.info(f"📚 Explanation: {explanation}")
                    else:
                        st.warning("Please select an answer first!")
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("🎯 No active quest! Go to the Home tab to generate one.")

with tab3:
    st.header("📊 Your Learning Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total XP", st.session_state.user_data['total_xp'], 
                 st.session_state.user_data.get('daily_xp', 0))
    
    with col2:
        st.metric("Current Streak", f"{st.session_state.user_data['streak']} days")
    
    with col3:
        level = st.session_state.user_data['total_xp'] // 100 + 1
        st.metric("Current Level", level)
    
    # Subjects studied
    if st.session_state.user_data['subjects_studied']:
        st.subheader("📚 Subjects Mastered")
        
        subjects_data = st.session_state.user_data['subjects_studied']
        for subject, xp in subjects_data.items():
            progress = min(xp / 500, 1.0)  # Max out at 500 XP per subject for progress bar
            st.write(f"**{subject}**: {xp} XP")
            st.progress(progress)
    
    # Achievement showcase
    st.subheader("🏅 Achievement Showcase")
    if st.session_state.user_data['badges']:
        st.markdown('<div class="badge-container">', unsafe_allow_html=True)
        for badge in st.session_state.user_data['badges']:
            st.markdown(f'<div class="badge">{badge}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Start completing quests to earn badges! 🎯")

with tab4:
    st.header("⏱️ Focus Mode - Pomodoro Timer")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Timer display
        if 'timer_start' not in st.session_state:
            st.session_state.timer_start = None
            st.session_state.timer_active = False
            st.session_state.break_time = False
        
        if st.session_state.timer_active and st.session_state.timer_start:
            elapsed = time.time() - st.session_state.timer_start
            focus_duration = 25 * 60  # 25 minutes
            break_duration = 5 * 60   # 5 minutes
            
            if st.session_state.break_time:
                remaining = max(0, break_duration - elapsed)
                if remaining <= 0:
                    st.session_state.timer_active = False
                    st.session_state.break_time = False
                    st.balloons()
                    st.success("Break time over! Ready for another focus session?")
                else:
                    mins, secs = divmod(int(remaining), 60)
                    st.markdown(f'<div class="focus-timer">🧘 Break Time<br>{mins:02d}:{secs:02d}</div>', 
                               unsafe_allow_html=True)
            else:
                remaining = max(0, focus_duration - elapsed)
                if remaining <= 0:
                    st.session_state.break_time = True
                    st.session_state.timer_start = time.time()
                    update_progress(25, "Focus Session")  # Award XP for completing focus session
                    st.success("🎉 Focus session complete! Time for a break!")
                else:
                    mins, secs = divmod(int(remaining), 60)
                    st.markdown(f'<div class="focus-timer">🎯 Focus Time<br>{mins:02d}:{secs:02d}</div>', 
                               unsafe_allow_html=True)
        else:
            st.markdown('<div class="focus-timer">⏱️ Ready to Focus?<br>25:00</div>', 
                       unsafe_allow_html=True)
        
        # Timer controls
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("▶️ Start Focus", disabled=st.session_state.timer_active):
                st.session_state.timer_active = True
                st.session_state.timer_start = time.time()
                st.session_state.break_time = False
                st.rerun()
        
        with col_b:
            if st.button("⏸️ Pause", disabled=not st.session_state.timer_active):
                st.session_state.timer_active = False
        
        with col_c:
            if st.button("🔄 Reset"):
                st.session_state.timer_active = False
                st.session_state.timer_start = None
                st.session_state.break_time = False
                st.rerun()
    
    with col2:
        st.subheader("🧠 Break Time Trivia")
        if st.button("🎲 Get Random Trivia"):
            trivia_prompt = "Generate a fun, educational trivia question with the answer for a high school student."
            trivia = call_groq_api(trivia_prompt)
            if trivia:
                st.info(trivia)
        
        st.subheader("💪 Study Tips")
        tips = [
            "💧 Stay hydrated during study sessions",
            "🌱 Take notes by hand to improve retention",
            "🎵 Try instrumental music for focus",
            "🚶 Take walking breaks between sessions",
            "📱 Put your phone in another room",
            "🌞 Study in good lighting",
            "🎯 Set specific goals for each session"
        ]
        st.info(random.choice(tips))

# Footer
st.markdown("---")
st.markdown("### 🎮 StudyQuest - Making Learning an Adventure!")
st.markdown("Built with ❤️ using Streamlit, Hugging Face, and Groq APIs")

# Auto-refresh for timer
if st.session_state.get('timer_active', False):
    time.sleep(1)
    st.rerun()