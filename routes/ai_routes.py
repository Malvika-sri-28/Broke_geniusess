import re
import random
from flask import Blueprint, request, jsonify
from flask_login import login_required
from database import db, Service

ai_bp = Blueprint('ai', __name__)

JOKES = [
    "Why do student programmers prefer dark mode? Because light attracts bugs!",
    "What's a broke student's favorite matrix? The Identity Matrix—because it has all the ones, just like their wallet.",
    "Why was the student's database project crying? Because it had too many relations, and none of them worked.",
    "How do students study for exams? 1% studying, 99% calculating the minimum score they need to pass.",
    "Student budget: 'I can buy this book, or I can eat for the next three weeks. Decisions, decisions.'",
    "Why did the computer science student fail their exam? They kept looking for index 1, but the arrays started at 0.",
    "Professor: 'Your assignment must be original.' Student: *Right click -> Inspect -> Edit as HTML*",
    "I told my professor that my dog ate my coding assignment. He said, 'That's impossible, it was on GitHub.' He said, 'Well, he took a byte out of it!'"
]

# Simple stop words to clean chat queries
STOP_WORDS = {
    'find', 'search', 'need', 'want', 'looking', 'for', 'who', 'does', 'is', 
    'there', 'any', 'help', 'with', 'please', 'can', 'you', 'recommend', 'me'
}

@ai_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'response': "Hey! I didn't catch that. Type something to start searching."})
        
    normalized = message.lower()
    
    # 1. Check for Jokes requests
    if any(k in normalized for k in ['joke', 'laugh', 'funny', 'humor']):
        return jsonify({'response': f"🤖 Here is a campus joke for you:\n\n*\"{random.choice(JOKES)}\"*" })
        
    # 2. Check for Greetings
    if normalized in ['hi', 'hello', 'hey', 'greetings', 'yo', 'hola']:
        return jsonify({
            'response': "👋 Hello! I am your **Broke Geniuses AI Assistant**.\n\nI can help you search the student marketplace. Ask me things like:\n- *\"Find Python tutoring\"*\n- *\"I need a logo designer\"*\n- *\"Show me notes sharing\"*\n\nHow can I help you today?"
        })
        
    # 3. Process search query tokens
    # Replace non-alphanumeric with spaces, tokenize
    words = re.sub(r'[^\w\s]', ' ', normalized).split()
    search_tokens = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    
    if not search_tokens:
        # If all words were stop words, search using the original clean message
        search_tokens = [normalized]
        
    # Query database for matching services using OR conditions
    matching_services = []
    
    # We query services where title, description or keywords match any token
    for token in search_tokens:
        pattern = f"%{token}%"
        services = Service.query.filter(
            (Service.title.ilike(pattern)) |
            (Service.description.ilike(pattern)) |
            (Service.keywords.ilike(pattern))
        ).all()
        for s in services:
            if s not in matching_services:
                matching_services.append(s)
                
    # 4. Format Recommendations
    if matching_services:
        response_text = "✨ I found the following campus services matching your query:\n\n"
        # Limit to top 3 recommendations
        for service in matching_services[:3]:
            # Markdown link format: [Title](/services/id)
            response_text += f"- **[{service.title}](/services/{service.id})**\n"
            response_text += f"  Price: `₹{service.price:,.2f}` | Offered by: @{service.seller.username} ({service.university})\n"
            if service.seller.is_top_rated:
                response_text += "  🏆 *Top Rated Seller*\n"
            response_text += "\n"
        
        response_text += "Click on a title to view details or book the gig!"
        return jsonify({'response': response_text})
        
    # 5. Default Fallback
    return jsonify({
        'response': f"🔍 I couldn't find any services matching *\"{message}\"* in our database.\n\nTry searching for topics like **'python'**, **'resume'**, **'logo'**, or **'notes'**.\n\nIf you have this skill, you can list it! Click **'Post a Service'** at the top."
    })

@ai_bp.route('/ai/generate-description', methods=['POST'])
@login_required
def generate_description():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    
    if not title:
        return jsonify({'description': "Please write a title first so I can generate a tailored description for you."})
        
    title_lower = title.lower()
    
    # Development / Programming
    if any(k in title_lower for k in ['python', 'django', 'code', 'coding', 'java', 'programming', 'c++', 'html', 'react', 'web', 'script']):
        desc = (
            f"Struggling with coding projects or university coursework? I am offering expert help for \"{title}\".\n\n"
            "Here is what I will cover:\n"
            "- Step-by-step guidance and mentorship on code structure.\n"
            "- Debugging, code cleaning, and optimization.\n"
            "- Explanations of OOP concepts, algorithms, and data structures used.\n"
            "- 1-on-1 explanation sessions via Zoom/Meet if required.\n\n"
            "Why choose me?\n"
            "- I am a CS major student and write clean, commented code.\n"
            "- Delivered within 48-72 hours.\n"
            "- 100% explanations so you can defend your assignment easily!\n\n"
            "Prerequisites: Please share your problem description sheet when booking."
        )
    # Resume / Interview / Career
    elif any(k in title_lower for k in ['resume', 'cv', 'linkedin', 'career', 'interview', 'mock', 'job', 'placement']):
        desc = (
            f"Get ready to ace your placements and get callbacks with my \"{title}\" service!\n\n"
            "What this service includes:\n"
            "- Complete ATS-friendly review of your resume structure and wording.\n"
            "- Action verb optimization and bullet-point rewriting for maximum impact.\n"
            "- LinkedIn profile audit to highlight your projects, skills, and bio.\n"
            "- One 30-minute mock feedback call to discuss career strategies and review questions.\n\n"
            "About me:\n"
            "- I am a final-year student and have successfully bagged internships/placement offers at top companies.\n"
            "- Quick delivery within 2-3 days.\n\n"
            "Let's land that dream job together!"
        )
    # Logo / Banner / Graphic Design
    elif any(k in title_lower for k in ['logo', 'design', 'graphics', 'banner', 'branding', 'vector', 'illustrator', 'photoshop', 'art']):
        desc = (
            f"Need a stunning visual identity for your startup, YouTube channel, college club, or profile? I offer high-quality \"{title}\".\n\n"
            "What you will get:\n"
            "- 2 to 3 unique creative concept drafts to choose from.\n"
            "- High-resolution exports (PNG, JPEG, transparent backgrounds).\n"
            "- Fully editable source files (.ai, .psd, or Canva link) included.\n"
            "- Up to 3 rounds of revisions to tweak colors, fonts, and layouts.\n\n"
            "Timeline:\n"
            "- Initial drafts ready within 48 hours.\n"
            "- Clean, modern, minimalist aesthetics optimized for print or screen.\n\n"
            "Please send your design preferences and color scheme ideas after booking!"
        )
    # Notes / Study Material / Exams
    elif any(k in title_lower for k in ['notes', 'study', 'exam', 'dsa', 'lecture', 'cheat', 'semester']):
        desc = (
            f"Save time and prepare smart for your exams! I am sharing my comprehensive, high-scoring \"{title}\".\n\n"
            "What is included in these notes:\n"
            "- Clean, hand-written or digitally typed PDF summaries of the entire syllabus.\n"
            "- Simplified step-by-step explanations of difficult concepts and proofs.\n"
            "- Clear charts, flowcharts, and diagrams to help visual memorization.\n"
            "- Top exam questions and solved previous year solutions.\n\n"
            "Details:\n"
            "- Format: High-quality scanned PDF.\n"
            "- Highly rated by peers during previous semesters.\n\n"
            "Instant download link / email file delivery immediately upon booking acceptance!"
        )
    # Default Fallback Template
    else:
        desc = (
            f"Providing professional student-to-student support for \"{title}\".\n\n"
            "What is included in this service:\n"
            "- High-quality custom deliverables tailored exactly to your guidelines.\n"
            "- Regular progress updates and revisions.\n"
            "- Fast turnaround times fitting student deadlines.\n\n"
            "Please message me with your project details, files, and deadlines so I can customize the workflow for you. Legitimate academic services only."
        )
        
    return jsonify({'description': desc})
