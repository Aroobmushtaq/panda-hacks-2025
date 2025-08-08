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

# Initialize session state for failed models
if 'failed_models' not in st.session_state:
    st.session_state.failed_models = set()
if 'working_model' not in st.session_state:
    st.session_state.working_model = None

# List of free models to try (in order of preference)
FREE_MODELS = [
    "openai-community/gpt2",         # Most reliable
    "google/flan-t5-small",          # Smaller, more accessible
    "distilgpt2",                    # Lightweight GPT-2
    "microsoft/DialoGPT-small",      # Smaller version
]

# Hugging Face API calls with smart caching
def call_huggingface_api(prompt: str, model: str = None) -> Optional[str]:
    if not HF_API_KEY:
        return None
    
    # If we found a working model before, try it first
    if st.session_state.working_model and st.session_state.working_model not in st.session_state.failed_models:
        models_to_try = [st.session_state.working_model]
    else:
        # Filter out models we know don't work
        models_to_try = [m for m in FREE_MODELS if m not in st.session_state.failed_models]
        if not models_to_try:
            # Reset failed models if all failed (maybe they work now)
            st.session_state.failed_models.clear()
            models_to_try = FREE_MODELS[:2]  # Try just 2 models
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    for current_model in models_to_try:
        if current_model in st.session_state.failed_models:
            continue
            
        url = f"https://api-inference.huggingface.co/models/{current_model}"
        
        # Adjust payload based on model type
        if "flan-t5" in current_model:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 100,
                    "temperature": 0.7
                }
            }
        else:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 100,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    generated_text = result.get("generated_text", "")
                else:
                    st.session_state.failed_models.add(current_model)
                    continue
                
                # Clean up the response
                if generated_text:
                    cleaned_text = generated_text.replace(prompt, "").strip()
                    if len(cleaned_text) > 10:
                        st.session_state.working_model = current_model
                        st.success(f"🤖 AI content generated!")
                        return cleaned_text
                
                st.session_state.failed_models.add(current_model)
                
            elif response.status_code == 403:
                st.session_state.failed_models.add(current_model)
                continue
            elif response.status_code == 503:
                continue  # Model loading, don't mark as failed
            else:
                st.session_state.failed_models.add(current_model)
                continue
                
        except:
            st.session_state.failed_models.add(current_model)
            continue
    
    # Only show this message once if no models work
    if len(st.session_state.failed_models) >= len(FREE_MODELS) and not hasattr(st.session_state, 'api_message_shown'):
        st.info("ℹ️ Using curated questions (AI models require premium access)")
        st.session_state.api_message_shown = True
    
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

# Groq API calls with fallback responses
def call_groq_api(prompt: str, model: str = "llama3-8b-8192") -> Optional[str]:
    if not GROQ_API_KEY:
        # Provide helpful fallback responses instead of just warning
        if "feedback" in prompt.lower():
            responses = [
                "Great work! Keep practicing to master this concept! 🎯",
                "Excellent! You're making real progress in your studies! 🌟",
                "Well done! This shows you understand the material! 🏆",
                "Nice job! Your hard work is paying off! 💪"
            ]
        elif "explanation" in prompt.lower():
            responses = [
                "Remember to review the key concepts and practice similar problems.",
                "Try breaking down the problem step by step and check your work.",
                "Consider reviewing your notes or asking your teacher for clarification.",
                "Don't worry - learning takes time and practice makes perfect!"
            ]
        elif "motivational" in prompt.lower() or "quote" in prompt.lower():
            responses = [
                "🌟 Every expert was once a beginner - keep going!",
                "🚀 Success comes from consistent daily effort!",
                "💪 You're building knowledge with every question!",
                "🎯 Focus on progress, not perfection!",
                "⭐ Great job staying committed to learning!"
            ]
        else:
            responses = [
                "Keep up the great work! You're learning and growing! 🌱",
                "Remember: every mistake is a learning opportunity! 📚",
                "Stay curious and keep asking questions! 🤔",
                "You've got this! Learning is a journey, not a race! 🏃‍♂️"
            ]
        
        import random
        return random.choice(responses)
    
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

# Generate AI quests with smart caching
def generate_quest(topic: str, difficulty: str = "medium") -> Optional[List[Dict]]:
    # Only try AI once per topic if we have an API key
    if HF_API_KEY and not st.session_state.get('api_attempted_for_topic') == topic:
        st.session_state.api_attempted_for_topic = topic
        
        # Simple prompt that works better with free models
        prompt = f"Create a quiz question about {topic}: What is"
        
        with st.spinner("🎲 Generating AI content..."):
            response = call_huggingface_api(prompt)
            
        if response and len(response.strip()) > 15:
            # Try to create a question from the AI response
            ai_question = create_question_from_ai_response(response, topic, difficulty)
            if ai_question:
                # Return AI-generated question plus fallbacks
                fallback_questions = get_subject_questions(topic, difficulty)
                return [ai_question] + fallback_questions[:2]
    
    # Use enhanced subject-specific questions
    return get_subject_questions(topic, difficulty)

def create_question_from_ai_response(response: str, topic: str, difficulty: str) -> Optional[Dict]:
    """Create a structured question from AI response"""
    try:
        # Clean the response
        response = response.strip()[:200]  # Limit length
        
        # If the response looks like it could be turned into a question
        if len(response) > 10:
            return {
                "question": f"Based on {topic}: {response.split('.')[0]}?",
                "options": [
                    f"A) This is correct about {topic}",
                    f"B) This relates to {topic} differently", 
                    f"C) This is not about {topic}",
                    f"D) More information is needed"
                ],
                "answer": "A",
                "hint": f"Think about the key concepts in {topic}",
                "xp": 60  # Bonus XP for AI-generated content
            }
    except:
        pass
    return None

def get_subject_questions(topic: str, difficulty: str) -> List[Dict]:
    """Get subject-specific questions based on topic"""
    topic_lower = topic.lower()
    base_xp = 40 if difficulty == "easy" else 50 if difficulty == "medium" else 60
    
    
    # Math questions
    if any(word in topic_lower for word in ['math', 'algebra', 'geometry', 'calculus', 'arithmetic', 'trigonometry']):
        questions = [
            {
                "question": f"If 3x - 7 = 14, what is the value of x?",
                "options": ["A) x = 7", "B) x = 5", "C) x = 9", "D) x = 3"],
                "answer": "A",
                "hint": "Add 7 to both sides, then divide by 3",
                "xp": base_xp
            },
            {
                "question": f"What is the area of a circle with radius 5?",
                "options": ["A) 10π", "B) 25π", "C) 5π", "D) 15π"],
                "answer": "B",
                "hint": "Use the formula A = πr²",
                "xp": base_xp
            },
            {
                "question": f"What is 25% of 80?",
                "options": ["A) 20", "B) 25", "C) 15", "D) 30"],
                "answer": "A",
                "hint": "Convert 25% to 0.25 and multiply",
                "xp": base_xp
            },
            {
                "question": f"What is the slope of the line y = 3x + 2?",
                "options": ["A) 2", "B) 3", "C) 5", "D) 1"],
                "answer": "B",
                "hint": "In y = mx + b, m is the slope",
                "xp": base_xp
            }
        ]
    
    # Science questions  
    elif any(word in topic_lower for word in ['science', 'biology', 'chemistry', 'physics', 'anatomy']):
        questions = [
            {
                "question": f"What is the powerhouse of the cell?",
                "options": ["A) Nucleus", "B) Mitochondria", "C) Ribosome", "D) Cytoplasm"],
                "answer": "B",
                "hint": "This organelle produces ATP energy",
                "xp": base_xp
            },
            {
                "question": f"What gas do plants absorb during photosynthesis?",
                "options": ["A) Oxygen", "B) Nitrogen", "C) Carbon dioxide", "D) Hydrogen"],
                "answer": "C",
                "hint": "Plants convert this gas into glucose using sunlight",
                "xp": base_xp
            },
            {
                "question": f"What is the chemical symbol for sodium?",
                "options": ["A) So", "B) S", "C) Na", "D) N"],
                "answer": "C",
                "hint": "It comes from the Latin word 'natrium'",
                "xp": base_xp
            },
            {
                "question": f"What type of energy does a moving object have?",
                "options": ["A) Potential energy", "B) Kinetic energy", "C) Chemical energy", "D) Nuclear energy"],
                "answer": "B",
                "hint": "This energy depends on mass and velocity",
                "xp": base_xp
            }
        ]
    
    # History questions
    elif any(word in topic_lower for word in ['history', 'historical', 'war', 'ancient', 'medieval', 'civilization']):
        questions = [
            {
                "question": f"In which year did World War II end?",
                "options": ["A) 1944", "B) 1945", "C) 1946", "D) 1947"],
                "answer": "B",
                "hint": "This was the year the atomic bombs were dropped on Japan",
                "xp": base_xp
            },
            {
                "question": f"Who was the first President of the United States?",
                "options": ["A) Thomas Jefferson", "B) John Adams", "C) George Washington", "D) Benjamin Franklin"],
                "answer": "C",
                "hint": "He led the Continental Army during the Revolutionary War",
                "xp": base_xp
            },
            {
                "question": f"The Renaissance began in which country?",
                "options": ["A) France", "B) England", "C) Spain", "D) Italy"],
                "answer": "D",
                "hint": "Think of cities like Florence and Venice",
                "xp": base_xp
            },
            {
                "question": f"Which empire built Machu Picchu?",
                "options": ["A) Aztec", "B) Maya", "C) Inca", "D) Roman"],
                "answer": "C",
                "hint": "This empire was located in modern-day Peru",
                "xp": base_xp
            }
        ]
    
    # English/Literature questions
    elif any(word in topic_lower for word in ['english', 'literature', 'grammar', 'writing', 'poetry']):
        questions = [
            {
                "question": f"What is a metaphor?",
                "options": ["A) A direct comparison using 'like' or 'as'", "B) An indirect comparison", "C) A repeated sound", "D) An exaggeration"],
                "answer": "B",
                "hint": "Unlike a simile, this doesn't use 'like' or 'as'",
                "xp": base_xp
            },
            {
                "question": f"Who wrote 'Romeo and Juliet'?",
                "options": ["A) Charles Dickens", "B) William Shakespeare", "C) Jane Austen", "D) Mark Twain"],
                "answer": "B",
                "hint": "This playwright is known as the Bard of Avon",
                "xp": base_xp
            },
            {
                "question": f"What is the past tense of 'run'?",
                "options": ["A) Runned", "B) Running", "C) Ran", "D) Runs"],
                "answer": "C",
                "hint": "This is an irregular verb",
                "xp": base_xp
            },
            {
                "question": f"What is alliteration?",
                "options": ["A) Rhyming words", "B) Repeated consonant sounds", "C) A type of poem", "D) A figure of speech"],
                "answer": "B",
                "hint": "Think 'Peter Piper picked...'",
                "xp": base_xp
            }
        ]
    
    # Computer Science/Programming
    elif any(word in topic_lower for word in ['computer', 'programming', 'coding', 'python', 'javascript', 'html']):
        questions = [
            {
                "question": f"What does HTML stand for?",
                "options": ["A) Hyper Text Markup Language", "B) High Tech Modern Language", "C) Home Tool Markup Language", "D) Hyperlink and Text Markup Language"],
                "answer": "A",
                "hint": "It's used to structure web pages",
                "xp": base_xp
            },
            {
                "question": f"Which symbol is used for comments in Python?",
                "options": ["A) //", "B) #", "C) /*", "D) --"],
                "answer": "B",
                "hint": "It's also called a hash or pound symbol",
                "xp": base_xp
            },
            {
                "question": f"What is a variable in programming?",
                "options": ["A) A fixed value", "B) A container for data", "C) A type of loop", "D) An error"],
                "answer": "B",
                "hint": "It stores information that can change",
                "xp": base_xp
            }
        ]
    
    # Geography
    elif any(word in topic_lower for word in ['geography', 'countries', 'continents', 'capitals', 'maps']):
        questions = [
            {
                "question": f"What is the largest continent?",
                "options": ["A) Africa", "B) North America", "C) Asia", "D) Europe"],
                "answer": "C",
                "hint": "It contains countries like China, India, and Russia",
                "xp": base_xp
            },
            {
                "question": f"What is the capital of Australia?",
                "options": ["A) Sydney", "B) Melbourne", "C) Canberra", "D) Perth"],
                "answer": "C",
                "hint": "It's not the largest city, but the planned capital",
                "xp": base_xp
            },
            {
                "question": f"Which river is the longest in the world?",
                "options": ["A) Amazon", "B) Nile", "C) Mississippi", "D) Yangtze"],
                "answer": "B",
                "hint": "It flows through Egypt",
                "xp": base_xp
            }
        ]
    
    # Generic questions for any topic
    else:
        questions = [
            {
                "question": f"What is the most effective way to study {topic}?",
                "options": ["A) Cramming the night before", "B) Regular practice and review", "C) Reading once", "D) Memorizing without understanding"],
                "answer": "B",
                "hint": "Consistent practice leads to better retention",
                "xp": base_xp
            },
            {
                "question": f"Why is understanding {topic} important?",
                "options": ["A) Only for exams", "B) For practical applications", "C) To impress others", "D) It's not important"],
                "answer": "B",
                "hint": "Most subjects have real-world applications",
                "xp": base_xp
            },
            {
                "question": f"What should you do if you're struggling with {topic}?",
                "options": ["A) Give up", "B) Ask for help", "C) Ignore it", "D) Complain"],
                "answer": "B",
                "hint": "Teachers and peers are there to support your learning",
                "xp": base_xp
            }
        ]
    
    # Return 3 random questions from the category
    import random
    return random.sample(questions, min(3, len(questions)))

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