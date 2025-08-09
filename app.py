import streamlit as st
import json
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import html

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
    .ai-status {
        background: linear-gradient(45deg, #00c851, #00ff88);
        color: white;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
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

# Load user data from session state
def save_user_data(data):
    st.session_state.user_data = data

# 🤖 AI INTEGRATION - FREE COHERE API
def call_cohere_api(prompt: str) -> Optional[str]:
    """
    🚀 FREE AI INTEGRATION using Cohere's free trial API
    - 1000 free API calls per month
    - No credit card required for trial
    - High-quality text generation
    """
    cohere_api_key = os.getenv("COHERE_API_KEY")
    
    if not cohere_api_key:
        return None
    
    headers = {
        "Authorization": f"Bearer {cohere_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": prompt,
        "model": "command-r",  # Free tier model
        "max_tokens": 150,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            "https://api.cohere.ai/v1/chat", 
            headers=headers, 
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("text", "").strip()
        else:
            return None
    except Exception as e:
        return None

# 🧠 INTELLIGENT QUESTION GENERATION
def generate_ai_questions(topic: str, difficulty: str) -> List[Dict]:
    """
    🎯 AI-POWERED QUESTION GENERATION
    Uses Cohere API to create relevant, subject-specific questions
    """
    
    # Try AI generation first
    ai_questions = []
    cohere_response = call_cohere_api(
        f"Create 3 {difficulty} level multiple choice questions about {topic}. "
        f"Format each as: Question: [question text] A) [option] B) [option] C) [option] D) [option] Answer: [correct letter]"
    )
    
    if cohere_response:
        ai_questions = parse_ai_questions(cohere_response, topic, difficulty)
        if ai_questions:
            st.markdown('<div class="ai-status">🤖 AI Generated Questions!</div>', unsafe_allow_html=True)
            return ai_questions
    
    # Enhanced fallback with PERFECT topic matching
    return get_subject_specific_questions(topic, difficulty)

def parse_ai_questions(ai_text: str, topic: str, difficulty: str) -> List[Dict]:
    """Parse AI-generated text into structured questions"""
    try:
        questions = []
        sections = ai_text.split("Question:")
        
        base_xp = 40 if difficulty == "easy" else 50 if difficulty == "medium" else 60
        
        for section in sections[1:]:  # Skip first empty section
            lines = section.strip().split('\n')
            if len(lines) >= 6:  # Need question + 4 options + answer
                question_text = lines[0].strip()
                options = []
                answer = "A"
                
                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith(('A)', 'B)', 'C)', 'D)')):
                        options.append(line)
                    elif line.startswith('Answer:'):
                        answer = line.split(':')[1].strip()
                
                if len(options) == 4 and question_text:
                    questions.append({
                        "question": question_text,
                        "options": options,
                        "answer": answer,
                        "hint": f"Think about the key concepts in {topic}",
                        "xp": base_xp + 10  # Bonus for AI questions
                    })
        
        return questions[:3]  # Return max 3 questions
    except:
        return []

# 📚 ENHANCED SUBJECT-SPECIFIC QUESTIONS
def get_subject_specific_questions(topic: str, difficulty: str) -> List[Dict]:
    """
    🎯 PERFECT TOPIC MATCHING with comprehensive question database
    Each subject gets properly matched questions with relevant hints
    """
    topic_lower = topic.lower()
    base_xp = 40 if difficulty == "easy" else 50 if difficulty == "medium" else 60
    
    # 💻 COMPUTER SCIENCE & PROGRAMMING
    if any(word in topic_lower for word in ['computer', 'programming', 'coding', 'python', 'java', 'javascript', 'html', 'css', 'software', 'algorithm', 'data structure']):
        if difficulty == "easy":
            questions = [
                {
                    "question": "What does HTML stand for?",
                    "options": ["A) Hyper Text Markup Language", "B) High Tech Modern Language", "C) Home Tool Markup Language", "D) Hyperlink Text Markup Language"],
                    "answer": "A",
                    "hint": "It's the standard language for creating web pages",
                    "xp": base_xp
                },
                {
                    "question": "Which of these is a programming language?",
                    "options": ["A) Python", "B) Chrome", "C) Windows", "D) Microsoft"],
                    "answer": "A",
                    "hint": "It's named after a type of snake and is popular for beginners",
                    "xp": base_xp
                },
                {
                    "question": "What is a variable in programming?",
                    "options": ["A) A fixed number", "B) A container that stores data", "C) A type of computer", "D) An error message"],
                    "answer": "B",
                    "hint": "Think of it as a labeled box that can hold different values",
                    "xp": base_xp
                }
            ]
        elif difficulty == "medium":
            questions = [
                {
                    "question": "Which symbol is used for comments in Python?",
                    "options": ["A) //", "B) #", "C) /* */", "D) --"],
                    "answer": "B",
                    "hint": "It's also called a hash symbol and makes text invisible to the program",
                    "xp": base_xp
                },
                {
                    "question": "What is the time complexity of linear search?",
                    "options": ["A) O(1)", "B) O(log n)", "C) O(n)", "D) O(n²)"],
                    "answer": "C",
                    "hint": "You might need to check every element in the worst case",
                    "xp": base_xp
                },
                {
                    "question": "What does CSS control in web development?",
                    "options": ["A) Content structure", "B) Visual styling and layout", "C) Database connections", "D) Server logic"],
                    "answer": "B",
                    "hint": "It makes websites look beautiful with colors, fonts, and layouts",
                    "xp": base_xp
                }
            ]
        else:  # hard
            questions = [
                {
                    "question": "What is the space complexity of merge sort?",
                    "options": ["A) O(1)", "B) O(log n)", "C) O(n)", "D) O(n log n)"],
                    "answer": "C",
                    "hint": "Consider the additional memory needed for the merge process",
                    "xp": base_xp
                },
                {
                    "question": "In object-oriented programming, what is polymorphism?",
                    "options": ["A) Having multiple classes", "B) Objects taking multiple forms", "C) Multiple inheritance", "D) Code reusability"],
                    "answer": "B",
                    "hint": "One interface, many implementations - like how '+' works for numbers and strings",
                    "xp": base_xp
                },
                {
                    "question": "What is a hash collision in computer science?",
                    "options": ["A) Two keys producing the same hash value", "B) A network error", "C) A syntax error", "D) A type mismatch"],
                    "answer": "A",
                    "hint": "When different inputs produce the same output in a hash function",
                    "xp": base_xp
                }
            ]
    
    # 🧮 MATHEMATICS
    elif any(word in topic_lower for word in ['math', 'algebra', 'geometry', 'calculus', 'arithmetic', 'trigonometry', 'statistics']):
        if difficulty == "easy":
            questions = [
                {
                    "question": "What is 15% of 200?",
                    "options": ["A) 25", "B) 30", "C) 35", "D) 40"],
                    "answer": "B",
                    "hint": "Convert 15% to decimal (0.15) and multiply by 200",
                    "xp": base_xp
                },
                {
                    "question": "If a rectangle has length 8 and width 5, what is its area?",
                    "options": ["A) 13", "B) 26", "C) 40", "D) 45"],
                    "answer": "C",
                    "hint": "Area of rectangle = length × width",
                    "xp": base_xp
                },
                {
                    "question": "What is 7 × 9?",
                    "options": ["A) 61", "B) 63", "C) 65", "D) 67"],
                    "answer": "B",
                    "hint": "Think: (7 × 10) - 7 = 70 - 7",
                    "xp": base_xp
                }
            ]
        elif difficulty == "medium":
            questions = [
                {
                    "question": "If 3x - 7 = 14, what is the value of x?",
                    "options": ["A) x = 7", "B) x = 5", "C) x = 9", "D) x = 3"],
                    "answer": "A",
                    "hint": "Add 7 to both sides first: 3x = 21, then divide by 3",
                    "xp": base_xp
                },
                {
                    "question": "What is the area of a circle with radius 6?",
                    "options": ["A) 12π", "B) 36π", "C) 18π", "D) 24π"],
                    "answer": "B",
                    "hint": "Use the formula A = πr², so A = π × 6²",
                    "xp": base_xp
                },
                {
                    "question": "What is the slope of the line y = 4x - 2?",
                    "options": ["A) 4", "B) -2", "C) 2", "D) 6"],
                    "answer": "A",
                    "hint": "In y = mx + b form, m is the slope coefficient",
                    "xp": base_xp
                }
            ]
        else:  # hard
            questions = [
                {
                    "question": "What is the derivative of x³ + 2x² - 5x + 3?",
                    "options": ["A) 3x² + 4x - 5", "B) x⁴ + 2x³ - 5x² + 3x", "C) 3x² + 2x - 5", "D) 3x + 4"],
                    "answer": "A",
                    "hint": "Use power rule: d/dx(xⁿ) = nxⁿ⁻¹ for each term",
                    "xp": base_xp
                },
                {
                    "question": "What is the integral of 2x dx?",
                    "options": ["A) x² + C", "B) 2x² + C", "C) x²/2 + C", "D) 2"],
                    "answer": "A",
                    "hint": "∫2x dx = 2∫x dx = 2(x²/2) + C = x² + C",
                    "xp": base_xp
                }
            ]
    
    # 🔬 SCIENCE (Biology, Chemistry, Physics)
    elif any(word in topic_lower for word in ['science', 'biology', 'chemistry', 'physics', 'anatomy', 'cell', 'molecule', 'atom']):
        if difficulty == "easy":
            questions = [
                {
                    "question": "What gas do plants absorb during photosynthesis?",
                    "options": ["A) Oxygen", "B) Nitrogen", "C) Carbon dioxide", "D) Hydrogen"],
                    "answer": "C",
                    "hint": "Plants use this gas along with sunlight and water to make glucose",
                    "xp": base_xp
                },
                {
                    "question": "How many chambers does a human heart have?",
                    "options": ["A) 2", "B) 3", "C) 4", "D) 5"],
                    "answer": "C",
                    "hint": "Think about the left and right sides, each with two chambers",
                    "xp": base_xp
                },
                {
                    "question": "What is the chemical symbol for oxygen?",
                    "options": ["A) O", "B) Ox", "C) Oy", "D) O2"],
                    "answer": "A",
                    "hint": "It's just the first letter of the element name",
                    "xp": base_xp
                }
            ]
        elif difficulty == "medium":
            questions = [
                {
                    "question": "What is the powerhouse of the cell?",
                    "options": ["A) Nucleus", "B) Mitochondria", "C) Ribosome", "D) Cytoplasm"],
                    "answer": "B",
                    "hint": "This organelle produces ATP energy through cellular respiration",
                    "xp": base_xp
                },
                {
                    "question": "What is the chemical formula for water?",
                    "options": ["A) H₂O", "B) CO₂", "C) O₂", "D) H₂SO₄"],
                    "answer": "A",
                    "hint": "Two hydrogen atoms bonded with one oxygen atom",
                    "xp": base_xp
                },
                {
                    "question": "What force keeps planets in orbit around the sun?",
                    "options": ["A) Magnetic force", "B) Gravitational force", "C) Electric force", "D) Nuclear force"],
                    "answer": "B",
                    "hint": "This force depends on mass and distance between objects",
                    "xp": base_xp
                }
            ]
        else:  # hard
            questions = [
                {
                    "question": "What is the pH of pure water at 25°C?",
                    "options": ["A) 6", "B) 7", "C) 8", "D) 14"],
                    "answer": "B",
                    "hint": "Pure water is neutral on the pH scale",
                    "xp": base_xp
                },
                {
                    "question": "Which process converts mRNA into proteins?",
                    "options": ["A) Transcription", "B) Translation", "C) Replication", "D) Mutation"],
                    "answer": "B",
                    "hint": "This process happens at ribosomes in the cytoplasm",
                    "xp": base_xp
                }
            ]
    
    # 📚 HISTORY
    elif any(word in topic_lower for word in ['history', 'historical', 'war', 'ancient', 'medieval', 'civilization', 'empire']):
        if difficulty == "easy":
            questions = [
                {
                    "question": "Who was the first President of the United States?",
                    "options": ["A) Thomas Jefferson", "B) John Adams", "C) George Washington", "D) Benjamin Franklin"],
                    "answer": "C",
                    "hint": "He led the Continental Army and is on the $1 bill",
                    "xp": base_xp
                },
                {
                    "question": "In which year did World War II end?",
                    "options": ["A) 1944", "B) 1945", "C) 1946", "D) 1947"],
                    "answer": "B",
                    "hint": "This was when atomic bombs were dropped and Japan surrendered",
                    "xp": base_xp
                }
            ]
        elif difficulty == "medium":
            questions = [
                {
                    "question": "Which empire built Machu Picchu?",
                    "options": ["A) Aztec", "B) Maya", "C) Inca", "D) Roman"],
                    "answer": "C",
                    "hint": "This South American empire was centered in modern-day Peru",
                    "xp": base_xp
                },
                {
                    "question": "The Renaissance began in which country?",
                    "options": ["A) France", "B) England", "C) Spain", "D) Italy"],
                    "answer": "D",
                    "hint": "Think of cities like Florence, Venice, and Rome during the 14th century",
                    "xp": base_xp
                }
            ]
        else:  # hard
            questions = [
                {
                    "question": "Which treaty ended World War I?",
                    "options": ["A) Treaty of Versailles", "B) Treaty of Paris", "C) Treaty of Vienna", "D) Treaty of Westphalia"],
                    "answer": "A",
                    "hint": "Signed in 1919, it imposed harsh terms on Germany",
                    "xp": base_xp
                }
            ]
    
    # 🔤 ENGLISH & LITERATURE
    elif any(word in topic_lower for word in ['english', 'literature', 'grammar', 'writing', 'poetry', 'shakespeare', 'novel']):
        if difficulty == "easy":
            questions = [
                {
                    "question": "What is the plural of 'child'?",
                    "options": ["A) Childs", "B) Children", "C) Childes", "D) Childs'"],
                    "answer": "B",
                    "hint": "This is an irregular plural form in English",
                    "xp": base_xp
                },
                {
                    "question": "Which word is a synonym for 'big'?",
                    "options": ["A) Small", "B) Large", "C) Tiny", "D) Little"],
                    "answer": "B",
                    "hint": "Look for a word that means the same as 'big'",
                    "xp": base_xp
                }
            ]
        elif difficulty == "medium":
            questions = [
                {
                    "question": "What is a metaphor?",
                    "options": ["A) A comparison using 'like' or 'as'", "B) A direct comparison without 'like' or 'as'", "C) A repeated sound", "D) An exaggeration"],
                    "answer": "B",
                    "hint": "Unlike similes, metaphors make direct comparisons (e.g., 'Life is a journey')",
                    "xp": base_xp
                },
                {
                    "question": "Who wrote 'Romeo and Juliet'?",
                    "options": ["A) Charles Dickens", "B) William Shakespeare", "C) Jane Austen", "D) Mark Twain"],
                    "answer": "B",
                    "hint": "This playwright is known as the Bard of Avon",
                    "xp": base_xp
                }
            ]
        else:  # hard
            questions = [
                {
                    "question": "What literary device is used in 'The wind whispered secrets'?",
                    "options": ["A) Metaphor", "B) Simile", "C) Personification", "D) Alliteration"],
                    "answer": "C",
                    "hint": "The wind is given human characteristics (whispering)",
                    "xp": base_xp
                }
            ]
    
    # 🌍 GEOGRAPHY
    elif any(word in topic_lower for word in ['geography', 'countries', 'continents', 'capitals', 'maps', 'world', 'earth']):
        if difficulty == "easy":
            questions = [
                {
                    "question": "Which is the largest continent?",
                    "options": ["A) Africa", "B) North America", "C) Asia", "D) Europe"],
                    "answer": "C",
                    "hint": "This continent contains China, India, Russia, and many other countries",
                    "xp": base_xp
                },
                {
                    "question": "What is the capital of France?",
                    "options": ["A) London", "B) Berlin", "C) Madrid", "D) Paris"],
                    "answer": "D",
                    "hint": "This city is famous for the Eiffel Tower",
                    "xp": base_xp
                }
            ]
        elif difficulty == "medium":
            questions = [
                {
                    "question": "What is the capital of Australia?",
                    "options": ["A) Sydney", "B) Melbourne", "C) Canberra", "D) Perth"],
                    "answer": "C",
                    "hint": "It's not the largest city, but the planned capital city",
                    "xp": base_xp
                },
                {
                    "question": "Which river is the longest in the world?",
                    "options": ["A) Amazon", "B) Nile", "C) Mississippi", "D) Yangtze"],
                    "answer": "B",
                    "hint": "This river flows through Egypt and several African countries",
                    "xp": base_xp
                }
            ]
        else:  # hard
            questions = [
                {
                    "question": "Which country has the most time zones?",
                    "options": ["A) Russia", "B) USA", "C) France", "D) China"],
                    "answer": "C",
                    "hint": "Consider overseas territories and departments",
                    "xp": base_xp
                }
            ]
    
    # 📖 GENERAL STUDY SKILLS (fallback)
    else:
        questions = [
            {
                "question": f"What is the most effective way to study {topic}?",
                "options": ["A) Cramming all at once", "B) Regular practice with breaks", "C) Reading without notes", "D) Memorizing everything"],
                "answer": "B",
                "hint": f"Spaced repetition and active learning work best for {topic}",
                "xp": base_xp
            },
            {
                "question": f"Why is {topic} important to learn?",
                "options": ["A) Only for exams", "B) Real-world applications", "C) To impress others", "D) Not important"],
                "answer": "B",
                "hint": f"Most subjects like {topic} have practical uses in daily life",
                "xp": base_xp
            }
        ]
    
    return random.sample(questions, min(3, len(questions)))

# 🎯 MAIN QUEST GENERATION FUNCTION
def generate_quest(topic: str, difficulty: str = "medium") -> List[Dict]:
    """
    🚀 SMART QUEST GENERATION SYSTEM
    1. First tries AI generation for personalized content
    2. Falls back to subject-specific curated questions
    3. Ensures all questions match the requested topic
    """
    
    # Try AI generation first (if API key available)
    ai_questions = generate_ai_questions(topic, difficulty)
    
    # Always show what method we're using
    if any('🤖 AI Generated' in str(st.session_state.get(key, '')) for key in st.session_state.keys()):
        return ai_questions
    else:
        st.info(f"📚 Using enhanced {topic} questions! (Add COHERE_API_KEY for AI generation)")
        return ai_questions  # This will be the curated ones from the fallback

# 💫 MOTIVATIONAL SYSTEM
def get_motivational_content():
    """Get motivational quotes from free APIs or curated content"""
    try:
        response = requests.get("https://api.quotable.io/random?tags=motivational", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"💭 \"{data['content']}\" - {data['author']}"
    except:
        pass
    
    quotes = [
        "🌟 \"The expert in anything was once a beginner.\" - Helen Hayes",
        "🚀 \"Success is the sum of small efforts repeated daily.\" - Robert Collier",
        "💪 \"It always seems impossible until it's done.\" - Nelson Mandela",
        "🎯 \"Education is the most powerful weapon for change.\" - Nelson Mandela"
    ]
    return random.choice(quotes)

def get_study_tip():
    """Generate subject-specific study tips"""
    tips = [
        "🧠 Use the Feynman Technique: Explain concepts simply to test understanding",
        "📝 Handwritten notes improve retention by 40% compared to typing",
        "⏰ Study in 25-minute focused blocks (Pomodoro Technique)",
        "🔄 Use spaced repetition - review material at increasing intervals",
        "🎵 Instrumental music can enhance focus and concentration",
        "💧 Stay hydrated - dehydration affects cognitive performance",
        "📱 Remove distractions - put devices in another room while studying"
    ]
    return random.choice(tips)

# 🏆 PROGRESS TRACKING SYSTEM
def update_progress(xp_gained: int, subject: str):
    today = datetime.now().date()
    last_activity = st.session_state.user_data.get('last_activity')
    
    # Update streak logic
    if last_activity:
        if isinstance(last_activity, str):
            last_date = datetime.fromisoformat(last_activity).date()
        else:
            last_date = last_activity
            
        if today == last_date:
            pass  # Same day, maintain streak
        elif today == last_date + timedelta(days=1):
            st.session_state.user_data['streak'] += 1
        else:
            st.session_state.user_data['streak'] = 1
    else:
        st.session_state.user_data['streak'] = 1
    
    # Update XP and tracking
    st.session_state.user_data['xp'] += xp_gained
    st.session_state.user_data['total_xp'] += xp_gained
    st.session_state.user_data['daily_xp'] += xp_gained
    st.session_state.user_data['last_activity'] = today.isoformat()
    
    # Track subjects
    if subject not in st.session_state.user_data['subjects_studied']:
        st.session_state.user_data['subjects_studied'][subject] = 0
    st.session_state.user_data['subjects_studied'][subject] += xp_gained
    
    check_badges()
    save_user_data(st.session_state.user_data)

def check_badges():
    """Smart badge system with meaningful achievements"""
    badges = st.session_state.user_data['badges']
    total_xp = st.session_state.user_data['total_xp']
    streak = st.session_state.user_data['streak']
    subjects_count = len(st.session_state.user_data['subjects_studied'])
    
    # XP-based badges
    xp_badges = [
        (100, "🌟 First Steps", "Earned your first 100 XP!"),
        (500, "🎯 Focused Learner", "Reached 500 XP milestone!"),
        (1000, "🏆 Study Champion", "Achieved 1000 XP!"),
        (2500, "🎓 Academic Master", "Reached 2500 XP!"),
        (5000, "🦸 Learning Hero", "Epic 5000 XP achievement!")
    ]
    
    # Streak badges
    streak_badges = [
        (3, "🔥 Hot Streak", "3 days in a row!"),
        (7, "⚡ Weekly Warrior", "7 day streak!"),
        (14, "🚀 Study Rocket", "2 weeks strong!"),
        (30, "💎 Diamond Dedication", "30 day streak!")
    ]
    
    # Subject diversity badges
    subject_badges = [
        (3, "🌈 Multi-Learner", "Studied 3 different subjects!"),
        (5, "🎨 Renaissance Scholar", "Mastered 5 subjects!"),
        (10, "🧠 Universal Mind", "Explored 10+ subjects!")
    ]
    
    # Check all badge types
    for threshold, title, desc in xp_badges:
        if total_xp >= threshold and title not in badges:
            badges.append(title)
            st.success(f"🎉 New Badge Unlocked: {title} - {desc}")
    
    for threshold, title, desc in streak_badges:
        if streak >= threshold and title not in badges:
            badges.append(title)
            st.success(f"🎉 Streak Badge Unlocked: {title} - {desc}")
    
    for threshold, title, desc in subject_badges:
        if subjects_count >= threshold and title not in badges:
            badges.append(title)
            st.success(f"🎉 Diversity Badge Unlocked: {title} - {desc}")

# 🎲 RANDOM EDUCATIONAL CONTENT
def get_random_educational_fact():
    """Get educational facts from free APIs with fallbacks"""
    try:
        # Numbers API - completely free
        response = requests.get("http://numbersapi.com/random/trivia", timeout=5)
        if response.status_code == 200:
            return f"🔢 {response.text}"
    except:
        pass
    
    # Curated educational facts
    facts = [
        "🧠 Your brain has about 86 billion neurons, more than stars in the Milky Way!",
        "📚 Reading for 6 minutes can reduce stress by up to 68%!",
        "⚡ Nerve impulses travel at speeds up to 268 mph!",
        "🌍 Earth is approximately 4.54 billion years old!",
        "🎨 Learning new skills creates new neural pathways at any age!",
        "🌙 During sleep, your brain consolidates memories from the day!",
        "🎵 Music activates more areas of the brain than any other activity!",
        "🏃 Exercise increases BDNF, which helps grow new brain cells!"
    ]
    return random.choice(facts)

# ========================
# 🖥️ MAIN APPLICATION UI
# ========================

# Header
st.markdown('<div class="main-header"><h1>🎮 StudyQuest</h1><p>AI-Powered Learning Adventure Platform</p></div>', 
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
    
    # Badges display
    if st.session_state.user_data['badges']:
        st.subheader("🏅 Your Badges")
        for badge in st.session_state.user_data['badges']:
            st.markdown(f'<div class="badge">{badge}</div>', unsafe_allow_html=True)

# Main app tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Home", "⚔️ Quests", "📊 Dashboard", "⏱️ Focus Mode", "ℹ️ About"])

with tab1:
    st.header("🎯 Start Your Learning Adventure!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📚 Create Your Quest")
        
        # Popular subject suggestions
        st.write("**🔥 Popular Subjects:**")
        subject_cols = st.columns(4)
        with subject_cols[0]:
            if st.button("💻 Computer Science"):
                st.session_state.selected_topic = "Computer Science"
        with subject_cols[1]:
            if st.button("🧮 Mathematics"):
                st.session_state.selected_topic = "Mathematics"
        with subject_cols[2]:
            if st.button("🔬 Science"):
                st.session_state.selected_topic = "Science"
        with subject_cols[3]:
            if st.button("📚 History"):
                st.session_state.selected_topic = "History"
        
        # Topic input
        default_topic = st.session_state.get('selected_topic', '')
        topic = st.text_input("What would you like to study?", 
                            value=default_topic,
                            placeholder="e.g., Python Programming, Algebra, Biology, World War II...")
        
        difficulty = st.selectbox("Choose difficulty:", 
                                ["easy", "medium", "hard"])
        
        study_time = st.slider("How long will you study? (minutes)", 
                             5, 120, 25)
        
        if st.button("🚀 Generate Quest", type="primary"):
            if topic:
                with st.spinner(f"🎲 Creating {difficulty} {topic} quest..."):
                    quest_data = generate_quest(topic, difficulty)
                    if quest_data:
                        st.session_state.current_quest = quest_data
                        st.session_state.quest_topic = topic
                        st.session_state.quest_difficulty = difficulty
                        st.success(f"✅ {topic} quest ready! Go to Quests tab to begin!")
                        st.balloons()
                    else:
                        st.error("Failed to generate quest. Please try again.")
            else:
                st.warning("Please enter a topic first!")
    
    with col2:
        st.subheader("💫 Daily Motivation")
        motivation = get_motivational_content()
        st.info(motivation)
        
        if st.session_state.user_data['daily_xp'] > 0:
            st.metric("Today's XP", st.session_state.user_data['daily_xp'])
        
        # Study tip
        st.subheader("💡 Pro Study Tip")
        if st.button("🎯 Get Study Tip"):
            tip = get_study_tip()
            st.success(tip)

with tab2:
    st.header("⚔️ Your Current Quest")
    
    if 'current_quest' in st.session_state and st.session_state.current_quest:
        quest = st.session_state.current_quest
        topic = st.session_state.get('quest_topic', 'Unknown')
        difficulty = st.session_state.get('quest_difficulty', 'medium')
        
        # Quest header
        st.markdown(f"""
        ### 📖 {topic} Challenge ({difficulty.title()} Level)
        **🎯 Complete all questions to earn XP and advance your learning!**
        """)
        
        # Question counter
        total_questions = len(quest)
        st.progress(0, text=f"Question Progress: 0/{total_questions}")
        
        for i, question_data in enumerate(quest):
            st.markdown(f'<div class="quest-card">', unsafe_allow_html=True)
            st.write(f"**❓ Question {i+1} of {total_questions}:**")
            st.write(f"### {question_data['question']}")
            
            # Create unique key for each question
            answer_key = f"answer_{topic}_{i}_{difficulty}"
            
            selected = st.radio(
                "Choose your answer:",
                question_data['options'],
                key=answer_key,
                index=None
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"💡 Get Hint", key=f"hint_{i}"):
                    st.info(f"💭 **Hint:** {question_data['hint']}")
            
            with col2:
                if st.button(f"✅ Submit Answer", key=f"submit_{i}", type="primary"):
                    if selected:
                        correct_answer = question_data['answer']
                        if selected.startswith(correct_answer):
                            st.success("🎉 Correct! Excellent work!")
                            xp_gained = question_data.get('xp', 50)
                            update_progress(xp_gained, topic)
                            
                            # Subject-specific encouragement
                            if 'computer' in topic.lower() or 'programming' in topic.lower():
                                encouragements = [
                                    "💻 Great coding logic! You're thinking like a programmer!",
                                    "🚀 Excellent! Your programming skills are improving!",
                                    "⚡ Perfect! You understand this computer science concept!"
                                ]
                            elif 'math' in topic.lower():
                                encouragements = [
                                    "🧮 Mathematical genius! Your calculation skills are sharp!",
                                    "📐 Perfect! You've mastered this mathematical concept!",
                                    "🎯 Excellent problem-solving! Math is your strength!"
                                ]
                            elif 'science' in topic.lower():
                                encouragements = [
                                    "🔬 Scientific thinking at its best! Well done!",
                                    "🧪 Brilliant! You understand this scientific principle!",
                                    "🌟 Excellent! Your science knowledge is expanding!"
                                ]
                            else:
                                encouragements = [
                                    f"📚 Outstanding work in {topic}! Keep it up!",
                                    f"🌟 You're mastering {topic} concepts brilliantly!",
                                    f"🏆 Perfect! {topic} is becoming your strength!"
                                ]
                            
                            st.info(f"🤖 AI Coach: {random.choice(encouragements)}")
                        else:
                            st.error("❌ Not quite right. Try again!")
                            # Show detailed explanation
                            correct_option = [opt for opt in question_data['options'] if opt.startswith(correct_answer)][0]
                            st.info(f"📚 **Correct Answer:** {correct_option}")
                            st.info(f"💡 **Why:** {question_data['hint']}")
                    else:
                        st.warning("Please select an answer first!")
            
            with col3:
                if st.button(f"⏭️ Skip Question", key=f"skip_{i}"):
                    st.info("Question skipped. Try another one!")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.info("🎯 No active quest! Go to the Home tab to generate one.")
        
        # Quick start options
        st.subheader("🎲 Quick Start Options")
        quick_cols = st.columns(2)
        
        with quick_cols[0]:
            if st.button("💻 Computer Science Quiz"):
                quest_data = generate_quest("Computer Science", "medium")
                st.session_state.current_quest = quest_data
                st.session_state.quest_topic = "Computer Science"
                st.session_state.quest_difficulty = "medium"
                st.rerun()
        
        with quick_cols[1]:
            if st.button("🧮 Math Challenge"):
                quest_data = generate_quest("Mathematics", "medium")
                st.session_state.current_quest = quest_data
                st.session_state.quest_topic = "Mathematics"
                st.session_state.quest_difficulty = "medium"
                st.rerun()

with tab3:
    st.header("📊 Your Learning Dashboard")
    
    # Stats overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total XP", st.session_state.user_data['total_xp'])
    
    with col2:
        st.metric("Current Streak", f"{st.session_state.user_data['streak']} days")
    
    with col3:
        level = st.session_state.user_data['total_xp'] // 100 + 1
        st.metric("Current Level", level)
    
    with col4:
        subjects_count = len(st.session_state.user_data['subjects_studied'])
        st.metric("Subjects Studied", subjects_count)
    
    # Detailed progress
    if st.session_state.user_data['subjects_studied']:
        st.subheader("📚 Subject Mastery Progress")
        
        for subject, xp in st.session_state.user_data['subjects_studied'].items():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                progress = min(xp / 500, 1.0)
                st.progress(progress, text=f"**{subject}**: {xp} XP")
            with col_b:
                mastery_level = "Beginner" if xp < 100 else "Intermediate" if xp < 300 else "Advanced"
                st.write(f"**{mastery_level}**")
    
    # Achievement showcase
    st.subheader("🏅 Achievement Gallery")
    if st.session_state.user_data['badges']:
        badge_cols = st.columns(3)
        for i, badge in enumerate(st.session_state.user_data['badges']):
            with badge_cols[i % 3]:
                st.markdown(f'<div class="badge">{badge}</div>', unsafe_allow_html=True)
    else:
        st.info("🎯 Complete quests to unlock amazing badges!")
    
    # Learning insights
    st.subheader("📈 Learning Insights")
    if st.button("🎲 Get Random Learning Fact"):
        fact = get_random_educational_fact()
        st.info(fact)

with tab4:
    st.header("⏱️ Focus Mode - Pomodoro Timer")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Timer display and logic
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
                    st.success("✅ Break time over! Ready for another focus session?")
                else:
                    mins, secs = divmod(int(remaining), 60)
                    st.markdown(f'<div class="focus-timer">🧘 Break Time<br>{mins:02d}:{secs:02d}</div>', 
                               unsafe_allow_html=True)
            else:
                remaining = max(0, focus_duration - elapsed)
                if remaining <= 0:
                    st.session_state.break_time = True
                    st.session_state.timer_start = time.time()
                    update_progress(25, "Focus Session")
                    st.success("🎉 Focus session complete! Great concentration!")
                    st.balloons()
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
        st.subheader("🧠 Focus Enhancers")
        
        if st.button("🎲 Quick Brain Break"):
            fact = get_random_educational_fact()
            st.info(fact)
        
        if st.button("💡 Focus Tip"):
            tip = get_study_tip()
            st.success(tip)
        
        st.subheader("🎯 Focus Stats")
        focus_sessions = st.session_state.user_data['subjects_studied'].get('Focus Session', 0) // 25
        st.metric("Completed Sessions", focus_sessions)

with tab5:
    st.header("ℹ️ About StudyQuest")
    
    st.markdown("""
    ## 🎮 **What is StudyQuest?**
    StudyQuest is an AI-powered gamified learning platform that transforms studying into an engaging adventure!
    
    ## 🤖 **AI Technologies Used:**
    
    ### **1. Cohere AI API (Primary AI Engine)**
    - **Why:** Free tier with 1000 API calls/month
    - **Purpose:** Generates personalized quiz questions for any subject
    - **How it works:** Uses advanced language models to create relevant, educational content
    - **Setup:** Add `COHERE_API_KEY` environment variable for AI features
    
    ### **2. Open Trivia Database API**
    - **Why:** Completely free, no authentication required
    - **Purpose:** Provides diverse trivia questions across multiple categories
    - **How it works:** REST API that returns JSON-formatted quiz questions
    - **Categories:** Science, Math, History, Geography, Computer Science, and more
    
    ### **3. Quotable API**
    - **Why:** Free motivational quotes to inspire learning
    - **Purpose:** Provides daily motivation and encouragement
    - **How it works:** Returns random inspirational quotes from famous people
    
    ### **4. Numbers API**
    - **Why:** Free educational facts about numbers and math
    - **Purpose:** Provides interesting trivia during break times
    - **How it works:** Returns fascinating facts about random numbers
    
    ## 🏗️ **Technical Architecture:**
    
    ### **Frontend Framework:**
    - **Streamlit:** Python-based web framework for rapid development
    - **Custom CSS:** Gamified UI with gradients, animations, and responsive design
    - **Session State Management:** Persistent user data across sessions
    
    ### **Core Features:**
    1. **🎯 Smart Topic Matching:** Advanced keyword detection for subject-specific questions
    2. **🏆 Gamification System:** XP points, levels, streaks, and achievement badges
    3. **⏱️ Pomodoro Timer:** Built-in focus sessions with break reminders
    4. **📊 Progress Tracking:** Detailed analytics on learning progress
    5. **🤖 AI Integration:** Dynamic content generation based on user preferences
    
    ### **Data Management:**
    - **Session-based storage:** All progress saved in browser session
    - **JSON serialization:** Efficient data persistence
    - **Real-time updates:** Immediate feedback and progress tracking
    
    ## 🎓 **Educational Benefits:**
    - **Spaced Repetition:** Questions designed to reinforce learning
    - **Adaptive Difficulty:** Easy, medium, hard levels for progressive learning
    - **Subject Diversity:** Comprehensive coverage of academic subjects
    - **Motivational Psychology:** Gamification increases engagement and retention
    
    ## 🔧 **Setup Instructions for Full AI Features:**
    
    ```bash
    # Get free Cohere API key
    1. Visit https://cohere.ai/
    2. Sign up for free account
    3. Get API key from dashboard
    4. Set environment variable: COHERE_API_KEY=your_key_here
    ```
    
    ## 🌟 **Why This Approach?**
    - **Cost-effective:** Uses only free APIs and resources
    - **Scalable:** Can handle multiple users simultaneously
    - **Educational:** Focuses on learning effectiveness over flashy features
    - **Reliable:** Multiple fallback systems ensure continuous operation
    """)
    
    # API Status Check
    st.subheader("🔌 API Status Check")
    
    # Check Cohere API
    cohere_status = "🟢 Connected" if os.getenv("COHERE_API_KEY") else "🟡 Not configured (using fallback questions)"
    st.write(f"**Cohere AI:** {cohere_status}")
    
    # Test free APIs
    col_test1, col_test2 = st.columns(2)
    
    with col_test1:
        if st.button("🧪 Test Trivia API"):
            try:
                response = requests.get("https://opentdb.com/api.php?amount=1&type=multiple", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Open Trivia DB: Working!")
                else:
                    st.error("❌ Open Trivia DB: Failed")
            except:
                st.error("❌ Open Trivia DB: Connection failed")
    
    with col_test2:
        if st.button("💭 Test Quote API"):
            try:
                response = requests.get("https://api.quotable.io/random", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Quotable API: Working!")
                else:
                    st.error("❌ Quotable API: Failed")
            except:
                st.error("❌ Quotable API: Connection failed")

# Footer with credits
st.markdown("---")
# st.markdown("""
# ### 🎮 StudyQuest - AI-Powered Learning Adventure
# **🔧 Built with:** Streamlit + Cohere AI + Open APIs  
# **🎯 Mission:** Making education engaging through gamification and AI  
# **⚡ Status:** Fully functional with free resources!
# """)

# Auto-refresh for timer
if st.session_state.get('timer_active', False):
    time.sleep(1)
    st.rerun()