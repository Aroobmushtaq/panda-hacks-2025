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

# List of free models to try (in order of preference)
FREE_MODELS = [
    "google/flan-t5-base",           # Great for Q&A, very reliable
    "microsoft/DialoGPT-medium",     # Good for conversations
    "gpt2",                          # Classic, always works
    "distilbert-base-uncased",       # Fast and efficient
    "facebook/blenderbot-400M-distill", # Good for educational content
]

# Hugging Face API calls with multiple model fallback
def call_huggingface_api(prompt: str, model: str = None) -> Optional[str]:
    if not HF_API_KEY:
        st.warning("⚠️ Hugging Face API key not found. Add HF_API_KEY to get AI-generated questions!")
        return None
    
    # If no specific model provided, try our free models in order
    models_to_try = [model] if model else FREE_MODELS
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    for current_model in models_to_try:
        if not current_model:
            continue
            
        url = f"https://api-inference.huggingface.co/models/{current_model}"
        
        # Adjust payload based on model type
        if "flan-t5" in current_model:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 150,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
        elif "gpt2" in current_model:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 200,
                    "temperature": 0.8,
                    "do_sample": True,
                    "pad_token_id": 50256
                }
            }
        else:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 150,
                    "temperature": 0.7
                }
            }
        
        try:
            with st.spinner(f"🤖 Trying {current_model}..."):
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle different response formats
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                    elif isinstance(result, dict):
                        generated_text = result.get("generated_text", "")
                    else:
                        continue
                    
                    # Clean up the response
                    if generated_text:
                        # Remove the original prompt if it's included
                        cleaned_text = generated_text.replace(prompt, "").strip()
                        if cleaned_text:
                            st.success(f"✅ Generated content using {current_model}")
                            return cleaned_text
                
                elif response.status_code == 503:
                    st.info(f"⏳ Model {current_model} is loading, trying next...")
                    continue
                else:
                    st.warning(f"⚠️ Model {current_model} returned {response.status_code}, trying next...")
                    continue
                    
        except requests.exceptions.Timeout:
            st.warning(f"⏰ {current_model} timed out, trying next...")
            continue
        except Exception as e:
            st.warning(f"⚠️ {current_model} error: {str(e)[:50]}..., trying next...")
            continue
    
    st.info("🔄 All free models are busy. Using enhanced fallback questions!")
    return None
    if not HF_API_KEY:
        st.warning("⚠️ Hugging Face API key not found. Using fallback questions for now. Add HF_API_KEY to get AI-generated questions!")
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
        st.warning("⚠️ Groq API key not found. Add GROQ_API_KEY for AI feedback!")
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
    # Try AI generation first if API key is available
    if HF_API_KEY:
        # Simplified prompt that works better with free models
        prompt = f"Generate a {difficulty} level quiz question about {topic} for high school students. Include 4 multiple choice options and indicate the correct answer."
        
        response = call_huggingface_api(prompt)
        if response:
            # Since free models may not return perfect JSON, we'll use enhanced fallbacks
            # but still try to extract useful content
            pass
    
    # Enhanced fallback questions based on topic
    topic_lower = topic.lower()
    
    # Math questions
    if any(word in topic_lower for word in ['math', 'algebra', 'geometry', 'calculus', 'arithmetic']):
        return [
            {
                "question": f"If 3x - 7 = 14, what is the value of x?",
                "options": ["A) x = 7", "B) x = 5", "C) x = 9", "D) x = 3"],
                "answer": "A",
                "hint": "Add 7 to both sides, then divide by 3",
                "xp": 50
            },
            {
                "question": f"What is the area of a circle with radius 4?",
                "options": ["A) 8π", "B) 16π", "C) 4π", "D) 12π"],
                "answer": "B",
                "hint": "Use the formula A = πr²",
                "xp": 50
            },
            {
                "question": f"What is 15% of 200?",
                "options": ["A) 30", "B) 25", "C) 35", "D) 40"],
                "answer": "A",
                "hint": "Convert 15% to 0.15 and multiply",
                "xp": 50
            }
        ]
    
    # Science questions
    elif any(word in topic_lower for word in ['science', 'biology', 'chemistry', 'physics']):
        return [
            {
                "question": f"What is the powerhouse of the cell?",
                "options": ["A) Nucleus", "B) Mitochondria", "C) Ribosome", "D) Cytoplasm"],
                "answer": "B",
                "hint": "This organelle produces ATP energy",
                "xp": 50
            },
            {
                "question": f"What gas do plants absorb during photosynthesis?",
                "options": ["A) Oxygen", "B) Nitrogen", "C) Carbon dioxide", "D) Hydrogen"],
                "answer": "C",
                "hint": "Plants convert this gas into glucose using sunlight",
                "xp": 50
            },
            {
                "question": f"What is the speed of light in a vacuum?",
                "options": ["A) 300,000 km/s", "B) 150,000 km/s", "C) 299,792,458 m/s", "D) Both A and C"],
                "answer": "D",
                "hint": "Light travels at approximately 300,000 km/s or exactly 299,792,458 m/s",
                "xp": 50
            }
        ]
    
    # History questions
    elif any(word in topic_lower for word in ['history', 'historical', 'war', 'ancient', 'medieval']):
        return [
            {
                "question": f"In which year did World War II end?",
                "options": ["A) 1944", "B) 1945", "C) 1946", "D) 1947"],
                "answer": "B",
                "hint": "This was the year the atomic bombs were dropped on Japan",
                "xp": 50
            },
            {
                "question": f"Who was the first President of the United States?",
                "options": ["A) Thomas Jefferson", "B) John Adams", "C) George Washington", "D) Benjamin Franklin"],
                "answer": "C",
                "hint": "He led the Continental Army during the Revolutionary War",
                "xp": 50
            },
            {
                "question": f"The Renaissance began in which country?",
                "options": ["A) France", "B) England", "C) Spain", "D) Italy"],
                "answer": "D",
                "hint": "Think of cities like Florence and Venice",
                "xp": 50
            }
        ]
    
    # English/Literature questions
    elif any(word in topic_lower for word in ['english', 'literature', 'grammar', 'writing']):
        return [
            {
                "question": f"What is a metaphor?",
                "options": ["A) A direct comparison using 'like' or 'as'", "B) An indirect comparison", "C) A repeated sound", "D) An exaggeration"],
                "answer": "B",
                "hint": "Unlike a simile, this doesn't use 'like' or 'as'",
                "xp": 50
            },
            {
                "question": f"Who wrote 'Romeo and Juliet'?",
                "options": ["A) Charles Dickens", "B) William Shakespeare", "C) Jane Austen", "D) Mark Twain"],
                "answer": "B",
                "hint": "This playwright is known as the Bard of Avon",
                "xp": 50
            },
            {
                "question": f"What is the past tense of 'run'?",
                "options": ["A) Runned", "B) Running", "C) Ran", "D) Runs"],
                "answer": "C",
                "hint": "This is an irregular verb",
                "xp": 50
            }
        ]
    
    # Generic questions for any topic
    else:
        return [
            {
                "question": f"What is the most effective way to study {topic}?",
                "options": ["A) Cramming the night before", "B) Regular practice and review", "C) Reading once", "D) Memorizing without understanding"],
                "answer": "B",
                "hint": "Consistent practice leads to better retention",
                "xp": 50
            },
            {
                "question": f"Why is understanding {topic} important?",
                "options": ["A) Only for exams", "B) For practical applications", "C) To impress others", "D) It's not important"],
                "answer": "B",
                "hint": "Most subjects have real-world applications",
                "xp": 50
            },
            {
                "question": f"What should you do if you're struggling with {topic}?",
                "options": ["A) Give up", "B) Ask for help", "C) Ignore it", "D) Complain"],
                "answer": "B",
                "hint": "Teachers and peers are there to support your learning",
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