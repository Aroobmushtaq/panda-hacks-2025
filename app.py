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

# Load user data from session state (no file I/O needed)
def load_user_data():
    return st.session_state.user_data

# Save user data to session state
def save_user_data(data):
    st.session_state.user_data = data

# Enhanced question generation using free Open Trivia Database API
def generate_quest_from_trivia_api(topic: str, difficulty: str = "medium") -> Optional[List[Dict]]:
    """Generate questions using the free Open Trivia Database API"""
    try:
        # Map topics to Open Trivia categories
        category_mapping = {
            'science': 17, 'biology': 17, 'chemistry': 17, 'physics': 17,
            'math': 19, 'mathematics': 19, 'algebra': 19, 'geometry': 19,
            'history': 23, 'geography': 22, 'politics': 24,
            'computer': 18, 'programming': 18, 'technology': 18,
            'art': 25, 'literature': 10, 'books': 10,
            'music': 12, 'film': 11, 'sports': 21,
            'animals': 27, 'nature': 17
        }
        
        # Find matching category
        category = None
        topic_lower = topic.lower()
        for key, cat_id in category_mapping.items():
            if key in topic_lower:
                category = cat_id
                break
        
        # Prepare API URL
        url = "https://opentdb.com/api.php"
        params = {
            'amount': 3,
            'type': 'multiple',
            'difficulty': difficulty.lower()
        }
        
        if category:
            params['category'] = category
        
        # Make API call
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('response_code') == 0 and data.get('results'):
                questions = []
                
                for item in data['results']:
                    # Decode HTML entities
                    import html
                    question = html.unescape(item['question'])
                    correct = html.unescape(item['correct_answer'])
                    incorrect = [html.unescape(ans) for ans in item['incorrect_answers']]
                    
                    # Create options list
                    all_options = [correct] + incorrect
                    random.shuffle(all_options)
                    
                    # Find correct answer position
                    correct_index = all_options.index(correct)
                    answer_labels = ['A', 'B', 'C', 'D']
                    correct_label = answer_labels[correct_index]
                    
                    # Format options with labels
                    formatted_options = [f"{label}) {option}" for label, option in zip(answer_labels, all_options)]
                    
                    questions.append({
                        "question": question,
                        "options": formatted_options,
                        "answer": correct_label,
                        "hint": f"Think about {item['category'].lower().replace('entertainment: ', '').replace('science: ', '')}",
                        "xp": 60  # Bonus XP for API questions
                    })
                
                if questions:
                    st.success("🌐 Generated questions from Open Trivia Database!")
                    return questions
    
    except Exception as e:
        pass  # Silently fall back to curated questions
    
    return None

# Free Random Facts API for trivia
def get_random_trivia_fact():
    """Get a random educational fact from free APIs"""
    try:
        # Try Numbers API first
        response = requests.get("http://numbersapi.com/random/trivia", timeout=5)
        if response.status_code == 200:
            return f"🔢 {response.text}"
    except:
        pass
    
    try:
        # Try Cat Facts API as backup
        response = requests.get("https://catfact.ninja/fact", timeout=5)
        if response.status_code == 200:
            fact = response.json().get('fact', '')
            return f"🐱 Fun Fact: {fact}"
    except:
        pass
    
    # Fallback to static educational facts
    facts = [
        "🧠 The human brain has about 86 billion neurons!",
        "🌍 Earth is about 4.5 billion years old!",
        "📚 Reading for just 6 minutes can reduce stress by 68%!",
        "⚡ Lightning strikes the Earth about 100 times per second!",
        "🌙 The Moon is moving away from Earth at 3.8 cm per year!",
        "🐘 Elephants can recognize themselves in mirrors!",
        "🌊 The Pacific Ocean contains more than half of the world's free water!",
        "🦋 Butterflies taste with their feet!"
    ]
    return random.choice(facts)

# Enhanced quest generation with multiple free sources
def generate_quest(topic: str, difficulty: str = "medium") -> List[Dict]:
    """Generate quests using multiple free sources"""
    
    # First try the free trivia API
    trivia_questions = generate_quest_from_trivia_api(topic, difficulty)
    if trivia_questions:
        return trivia_questions
    
    # Fallback to enhanced curated questions
    st.info("🎯 Using enhanced curated questions!")
    return get_enhanced_subject_questions(topic, difficulty)

def get_enhanced_subject_questions(topic: str, difficulty: str) -> List[Dict]:
    """Enhanced curated questions with more variety and AI-like generation"""
    topic_lower = topic.lower()
    base_xp = 40 if difficulty == "easy" else 50 if difficulty == "medium" else 60
    
    # Math questions with more variety
    if any(word in topic_lower for word in ['math', 'algebra', 'geometry', 'calculus', 'arithmetic', 'trigonometry']):
        easy_questions = [
            {
                "question": "What is 7 × 8?",
                "options": ["A) 54", "B) 56", "C) 58", "D) 52"],
                "answer": "B",
                "hint": "Think of 7 × 8 as (7 × 10) - (7 × 2)",
                "xp": base_xp
            },
            {
                "question": "What is 15% of 200?",
                "options": ["A) 25", "B) 30", "C) 35", "D) 40"],
                "answer": "B",
                "hint": "15% = 0.15, so multiply 200 × 0.15",
                "xp": base_xp
            }
        ]
        
        medium_questions = [
            {
                "question": "If 3x - 7 = 14, what is x?",
                "options": ["A) x = 7", "B) x = 5", "C) x = 9", "D) x = 3"],
                "answer": "A",
                "hint": "Add 7 to both sides, then divide by 3",
                "xp": base_xp
            },
            {
                "question": "What is the area of a circle with radius 4?",
                "options": ["A) 8π", "B) 16π", "C) 12π", "D) 4π"],
                "answer": "B",
                "hint": "Use A = πr², so A = π × 4²",
                "xp": base_xp
            }
        ]
        
        hard_questions = [
            {
                "question": "What is the derivative of x² + 3x?",
                "options": ["A) 2x + 3", "B) x + 3", "C) 2x", "D) 3x"],
                "answer": "A",
                "hint": "Use the power rule: d/dx(xⁿ) = nxⁿ⁻¹",
                "xp": base_xp
            },
            {
                "question": "In a right triangle, if one angle is 30°, what is the other acute angle?",
                "options": ["A) 45°", "B) 60°", "C) 90°", "D) 120°"],
                "answer": "B",
                "hint": "The sum of angles in any triangle is 180°",
                "xp": base_xp
            }
        ]
    
    # Science questions
    elif any(word in topic_lower for word in ['science', 'biology', 'chemistry', 'physics', 'anatomy']):
        easy_questions = [
            {
                "question": "What do plants need to make food?",
                "options": ["A) Only water", "B) Sunlight, water, and CO₂", "C) Only sunlight", "D) Only soil"],
                "answer": "B",
                "hint": "Photosynthesis requires three main ingredients",
                "xp": base_xp
            },
            {
                "question": "How many bones are in an adult human body?",
                "options": ["A) 196", "B) 206", "C) 216", "D) 186"],
                "answer": "B",
                "hint": "It's just over 200 bones",
                "xp": base_xp
            }
        ]
        
        medium_questions = [
            {
                "question": "What is the powerhouse of the cell?",
                "options": ["A) Nucleus", "B) Mitochondria", "C) Ribosome", "D) Cytoplasm"],
                "answer": "B",
                "hint": "This organelle produces ATP energy",
                "xp": base_xp
            },
            {
                "question": "What is the chemical formula for water?",
                "options": ["A) H₂O", "B) CO₂", "C) O₂", "D) NaCl"],
                "answer": "A",
                "hint": "Two hydrogen atoms and one oxygen atom",
                "xp": base_xp
            }
        ]
        
        hard_questions = [
            {
                "question": "What is the first law of thermodynamics?",
                "options": ["A) Energy cannot be created or destroyed", "B) Entropy always increases", "C) Objects at rest stay at rest", "D) F = ma"],
                "answer": "A",
                "hint": "Also known as the law of conservation of energy",
                "xp": base_xp
            },
            {
                "question": "Which process converts mRNA into proteins?",
                "options": ["A) Transcription", "B) Translation", "C) Replication", "D) Mutation"],
                "answer": "B",
                "hint": "This happens at the ribosome",
                "xp": base_xp
            }
        ]
    
    # History questions
    elif any(word in topic_lower for word in ['history', 'historical', 'war', 'ancient', 'medieval', 'civilization']):
        easy_questions = [
            {
                "question": "Who was the first President of the United States?",
                "options": ["A) Thomas Jefferson", "B) John Adams", "C) George Washington", "D) Benjamin Franklin"],
                "answer": "C",
                "hint": "He's on the one-dollar bill",
                "xp": base_xp
            },
            {
                "question": "In which year did the Titanic sink?",
                "options": ["A) 1910", "B) 1912", "C) 1914", "D) 1916"],
                "answer": "B",
                "hint": "It was during its maiden voyage",
                "xp": base_xp
            }
        ]
        
        medium_questions = [
            {
                "question": "Which ancient wonder of the world was located in Alexandria?",
                "options": ["A) Hanging Gardens", "B) Lighthouse of Alexandria", "C) Colossus of Rhodes", "D) Statue of Zeus"],
                "answer": "B",
                "hint": "It was a famous lighthouse guiding ships",
                "xp": base_xp
            },
            {
                "question": "The Renaissance began in which country?",
                "options": ["A) France", "B) England", "C) Spain", "D) Italy"],
                "answer": "D",
                "hint": "Think of cities like Florence and Venice",
                "xp": base_xp
            }
        ]
        
        hard_questions = [
            {
                "question": "Which treaty ended World War I?",
                "options": ["A) Treaty of Versailles", "B) Treaty of Paris", "C) Treaty of Vienna", "D) Treaty of Westphalia"],
                "answer": "A",
                "hint": "Signed in 1919 in France",
                "xp": base_xp
            },
            {
                "question": "Who was the last Pharaoh of Ancient Egypt?",
                "options": ["A) Nefertiti", "B) Cleopatra VII", "C) Hatshepsut", "D) Ankhesenamun"],
                "answer": "B",
                "hint": "She was involved with Julius Caesar and Mark Antony",
                "xp": base_xp
            }
        ]
    
    # English/Literature questions
    elif any(word in topic_lower for word in ['english', 'literature', 'grammar', 'writing', 'poetry']):
        easy_questions = [
            {
                "question": "What is the plural of 'child'?",
                "options": ["A) Childs", "B) Children", "C) Childes", "D) Child's"],
                "answer": "B",
                "hint": "This is an irregular plural form",
                "xp": base_xp
            },
            {
                "question": "Which word is a synonym for 'happy'?",
                "options": ["A) Sad", "B) Angry", "C) Joyful", "D) Tired"],
                "answer": "C",
                "hint": "Look for a word with similar meaning",
                "xp": base_xp
            }
        ]
        
        medium_questions = [
            {
                "question": "What is a metaphor?",
                "options": ["A) A direct comparison using 'like' or 'as'", "B) An indirect comparison", "C) A repeated sound", "D) An exaggeration"],
                "answer": "B",
                "hint": "Unlike a simile, this doesn't use 'like' or 'as'",
                "xp": base_xp
            },
            {
                "question": "Who wrote 'To Kill a Mockingbird'?",
                "options": ["A) Harper Lee", "B) Mark Twain", "C) F. Scott Fitzgerald", "D) Ernest Hemingway"],
                "answer": "A",
                "hint": "This author's first name is Harper",
                "xp": base_xp
            }
        ]
        
        hard_questions = [
            {
                "question": "What literary device is used in 'The wind whispered through the trees'?",
                "options": ["A) Metaphor", "B) Simile", "C) Personification", "D) Alliteration"],
                "answer": "C",
                "hint": "Wind is given human characteristics",
                "xp": base_xp
            },
            {
                "question": "In Shakespeare's plays, what is a soliloquy?",
                "options": ["A) A conversation between two characters", "B) A character speaking alone", "C) Stage directions", "D) The play's ending"],
                "answer": "B",
                "hint": "Famous example: 'To be or not to be...'",
                "xp": base_xp
            }
        ]
    
    # Computer Science/Programming
    elif any(word in topic_lower for word in ['computer', 'programming', 'coding', 'python', 'javascript', 'html']):
        easy_questions = [
            {
                "question": "What does HTML stand for?",
                "options": ["A) Hyper Text Markup Language", "B) High Tech Modern Language", "C) Home Tool Markup Language", "D) Hyperlink Text Markup Language"],
                "answer": "A",
                "hint": "It's used to create web pages",
                "xp": base_xp
            },
            {
                "question": "Which of these is a programming language?",
                "options": ["A) Python", "B) Lion", "C) Eagle", "D) Tiger"],
                "answer": "A",
                "hint": "It's named after a snake",
                "xp": base_xp
            }
        ]
        
        medium_questions = [
            {
                "question": "Which symbol is used for comments in Python?",
                "options": ["A) //", "B) #", "C) /*", "D) --"],
                "answer": "B",
                "hint": "It's also called a hash or pound symbol",
                "xp": base_xp
            },
            {
                "question": "What is a variable in programming?",
                "options": ["A) A fixed value", "B) A container for data", "C) A type of loop", "D) An error"],
                "answer": "B",
                "hint": "It stores information that can change",
                "xp": base_xp
            }
        ]
        
        hard_questions = [
            {
                "question": "What is the time complexity of binary search?",
                "options": ["A) O(n)", "B) O(log n)", "C) O(n²)", "D) O(1)"],
                "answer": "B",
                "hint": "It divides the search space in half each time",
                "xp": base_xp
            },
            {
                "question": "What does API stand for?",
                "options": ["A) Application Programming Interface", "B) Advanced Programming Integration", "C) Automated Program Interaction", "D) Application Process Integration"],
                "answer": "A",
                "hint": "It allows different software applications to communicate",
                "xp": base_xp
            }
        ]
    
    # Geography
    elif any(word in topic_lower for word in ['geography', 'countries', 'continents', 'capitals', 'maps']):
        easy_questions = [
            {
                "question": "Which is the largest ocean?",
                "options": ["A) Atlantic", "B) Indian", "C) Pacific", "D) Arctic"],
                "answer": "C",
                "hint": "It's between Asia and America",
                "xp": base_xp
            },
            {
                "question": "How many continents are there?",
                "options": ["A) 5", "B) 6", "C) 7", "D) 8"],
                "answer": "C",
                "hint": "Africa, Antarctica, Asia, Australia, Europe, North America, South America",
                "xp": base_xp
            }
        ]
        
        medium_questions = [
            {
                "question": "What is the capital of Canada?",
                "options": ["A) Toronto", "B) Vancouver", "C) Ottawa", "D) Montreal"],
                "answer": "C",
                "hint": "It's not the largest city",
                "xp": base_xp
            },
            {
                "question": "Which country has the most time zones?",
                "options": ["A) Russia", "B) USA", "C) China", "D) France"],
                "answer": "D",
                "hint": "Consider overseas territories",
                "xp": base_xp
            }
        ]
        
        hard_questions = [
            {
                "question": "What is the smallest country in the world?",
                "options": ["A) Monaco", "B) San Marino", "C) Vatican City", "D) Liechtenstein"],
                "answer": "C",
                "hint": "It's located within Rome, Italy",
                "xp": base_xp
            },
            {
                "question": "Which strait separates Europe and Africa?",
                "options": ["A) Strait of Gibraltar", "B) Bosphorus Strait", "C) Strait of Hormuz", "D) Bass Strait"],
                "answer": "A",
                "hint": "It connects the Atlantic Ocean and Mediterranean Sea",
                "xp": base_xp
            }
        ]
    
    # Generic study skills questions
    else:
        easy_questions = [
            {
                "question": f"What is the best way to start studying {topic}?",
                "options": ["A) Start with the hardest concepts", "B) Begin with basics and build up", "C) Skip to the test", "D) Study everything at once"],
                "answer": "B",
                "hint": "Building a strong foundation is key",
                "xp": base_xp
            }
        ]
        
        medium_questions = [
            {
                "question": f"How often should you review {topic} material?",
                "options": ["A) Only before exams", "B) Regularly throughout the course", "C) Once at the end", "D) Never"],
                "answer": "B",
                "hint": "Spaced repetition improves retention",
                "xp": base_xp
            }
        ]
        
        hard_questions = [
            {
                "question": f"What is the most effective study technique for {topic}?",
                "options": ["A) Passive reading", "B) Active recall and practice", "C) Highlighting everything", "D) Memorizing without understanding"],
                "answer": "B",
                "hint": "Testing yourself is more effective than just reading",
                "xp": base_xp
            }
        ]
    
    # Select questions based on difficulty
    if difficulty == "easy":
        available_questions = easy_questions + medium_questions[:1]
    elif difficulty == "medium":
        available_questions = easy_questions[:1] + medium_questions + hard_questions[:1]
    else:  # hard
        available_questions = medium_questions[:1] + hard_questions
    
    # Return 3 random questions
    return random.sample(available_questions, min(3, len(available_questions)))

# Generate motivational content using free APIs or fallbacks
def get_motivational_content():
    """Get motivational quotes from free APIs or use fallbacks"""
    try:
        # Try Quotable API (free)
        response = requests.get("https://api.quotable.io/random?tags=motivational|inspirational", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"💭 \"{data['content']}\" - {data['author']}"
    except:
        pass
    
    # Fallback motivational quotes
    quotes = [
        "🌟 \"The only way to do great work is to love what you do.\" - Steve Jobs",
        "🚀 \"Success is not final, failure is not fatal: it is the courage to continue that counts.\" - Winston Churchill",
        "💪 \"Don't watch the clock; do what it does. Keep going.\" - Sam Levenson",
        "🎯 \"The expert in anything was once a beginner.\" - Helen Hayes",
        "⭐ \"Success is the sum of small efforts repeated day in and day out.\" - Robert Collier",
        "🏆 \"It always seems impossible until it's done.\" - Nelson Mandela",
        "🔥 \"The future belongs to those who believe in the beauty of their dreams.\" - Eleanor Roosevelt",
        "💎 \"Education is the most powerful weapon which you can use to change the world.\" - Nelson Mandela"
    ]
    return random.choice(quotes)

# Generate study tips using structured content
def get_study_tip():
    """Generate helpful study tips"""
    tips = [
        "🧠 Use the Feynman Technique: Explain concepts in simple terms as if teaching someone else",
        "📝 Take handwritten notes - it improves retention by 40%",
        "⏰ Study in 25-minute blocks (Pomodoro Technique) for better focus",
        "🔄 Use spaced repetition - review material at increasing intervals",
        "🎵 Try instrumental or classical music to enhance concentration",
        "💧 Stay hydrated - even mild dehydration affects cognitive performance",
        "🌅 Study your most challenging subjects when you're most alert",
        "📱 Eliminate distractions - put devices in another room",
        "🎯 Set specific, measurable goals for each study session",
        "🚶 Take short walks between study sessions to refresh your mind",
        "🍎 Eat brain foods: blueberries, nuts, and dark chocolate",
        "😴 Get 7-9 hours of sleep - it's when your brain consolidates memories"
    ]
    return random.choice(tips)

# Update streak and XP
def update_progress(xp_gained: int, subject: str):
    today = datetime.now().date()
    last_activity = st.session_state.user_data.get('last_activity')
    
    # Update streak
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

# Main app layout
st.markdown('<div class="main-header"><h1>🎮 StudyQuest</h1><p>Level up your learning with enhanced quests!</p></div>', 
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
                with st.spinner("🎲 Crafting your personalized quest..."):
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
        quote = get_motivational_content()
        st.info(quote)
        
        if st.session_state.user_data['daily_xp'] > 0:
            st.metric("Today's XP", st.session_state.user_data['daily_xp'])
        
        # Random study tip
        if st.button("💡 Get Study Tip"):
            tip = get_study_tip()
            st.success(tip)

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
                            
                            # Show encouraging message
                            encouragements = [
                                "🌟 Excellent work! You're mastering this!",
                                "🎯 Perfect! Your hard work is paying off!",
                                "🏆 Outstanding! Keep up the momentum!",
                                "⚡ Brilliant! You're on fire today!",
                                "💎 Superb! Knowledge level increasing!"
                            ]
                            st.info(f"🤖 Coach: {random.choice(encouragements)}")
                        else:
                            st.error("❌ Not quite right. Try again!")
                            # Show explanation
                            explanations = {
                                'A': "The correct answer is A. Review this concept and try similar problems.",
                                'B': "The correct answer is B. Think about the key principles involved.",
                                'C': "The correct answer is C. Consider the context and relationships.",
                                'D': "The correct answer is D. Break down the problem step by step."
                            }
                            correct_letter = question_data['answer']
                            st.info(f"📚 Explanation: {explanations.get(correct_letter, 'Review the material and try again!')}")
                    else:
                        st.warning("Please select an answer first!")
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("🎯 No active quest! Go to the Home tab to generate one.")
        
        # Show sample questions to encourage engagement
        st.subheader("🎲 Quick Challenge")
        if st.button("🎯 Try a Random Question"):
            sample_questions = get_enhanced_subject_questions("general knowledge", "medium")
            if sample_questions:
                st.session_state.current_quest = [sample_questions[0]]
                st.session_state.quest_topic = "Quick Challenge"
                st.rerun()

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
    
    # Fun fact section
    st.subheader("🎲 Random Learning Fact")
    if st.button("🌟 Get Random Fact"):
        fact = get_random_trivia_fact()
        st.info(fact)

# Free Random Facts function
def get_random_trivia_fact():
    """Get educational facts from free APIs or use fallbacks"""
    try:
        # Try Numbers API
        response = requests.get("http://numbersapi.com/random/trivia", timeout=5)
        if response.status_code == 200:
            return f"🔢 {response.text}"
    except:
        pass
    
    # Fallback educational facts
    facts = [
        "🧠 Your brain uses about 20% of your body's total energy!",
        "📚 Reading for just 6 minutes can reduce stress by up to 68%!",
        "🌍 The human brain has about 86 billion neurons!",
        "⚡ Information travels through your nerves at up to 268 mph!",
        "🎨 Learning a new skill increases brain plasticity at any age!",
        "🌙 Sleep helps consolidate memories from the day!",
        "🎵 Music can improve memory and learning ability!",
        "🏃 Exercise increases brain-derived neurotrophic factor (BDNF)!"
    ]
    return random.choice(facts)

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
        st.subheader("🧠 Break Time Activities")
        
        if st.button("🎲 Get Fun Fact"):
            fact = get_random_trivia_fact()
            st.info(fact)
        
        if st.button("💡 Study Tip"):
            tip = get_study_tip()
            st.success(tip)
        
        if st.button("💫 Motivation Boost"):
            motivation = get_motivational_content()
            st.info(motivation)

# Footer
st.markdown("---")
st.markdown("### 🎮 StudyQuest - Making Learning an Adventure!")
st.markdown("**✨ Now powered by free APIs and enhanced content!**")

# Auto-refresh for timer
if st.session_state.get('timer_active', False):
    time.sleep(1)
    st.rerun()