import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from database import db, Order, SessionRoom
from werkzeug.utils import secure_filename

try:
    import stripe
except ImportError:
    stripe = None

session_bp = Blueprint('session', __name__)

SESSION_ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'zip', 'png', 'jpg', 'jpeg', 'webp'}

def allowed_session_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in SESSION_ALLOWED_EXTENSIONS

def generate_session_package(service_title, service_description, transcript_text):
    title_lower = service_title.lower()
    
    # 1. Development & Programming
    if any(k in title_lower for k in ['python', 'django', 'code', 'coding', 'java', 'programming', 'c++', 'html', 'react', 'web', 'script']):
        summary = (
            f"### Lecture Summary: {service_title}\n\n"
            "During this session, the tutor and student reviewed core software engineering concepts:\n"
            "- **Object-Oriented Programming (OOP)**: Discussed class designs, objects, encapsulation, and inheritance patterns.\n"
            "- **Debugging & Run-Time Analysis**: Explored common stack traces, off-by-one errors, and syntax anomalies.\n"
            "- **Key Algorithms**: Analyzed time complexity and walked through implementation details of logic blocks.\n"
            "- **Best Practices**: Reviewed code commenting structure and formatting standards."
        )
        
        notes = (
            f"### Lecture Notes & Cheat Sheet: {service_title}\n\n"
            "#### 1. Core Syntax Cheat Sheet\n"
            "```python\n"
            "# Quick Object definition in Python\n"
            "class Student:\n"
            "    def __init__(self, name, budget):\n"
            "        self.name = name\n"
            "        self.budget = budget\n"
            "        \n"
            "    def is_broke(self):\n"
            "        return self.budget < 500.0\n"
            "```\n\n"
            "#### 2. Key Takeaways\n"
            "- Keep functions focused (Single Responsibility Principle).\n"
            "- Always write unit tests for boundary conditions (e.g. empty lists, negative values).\n"
            "- Use clean variable naming conventions instead of abbreviations (e.g. `user_count` instead of `uc`)."
        )
        
        quiz_data = [
            {
                "question": "Which of the following is NOT a pillar of Object-Oriented Programming (OOP)?",
                "options": ["Encapsulation", "Compilation", "Inheritance", "Polymorphism"],
                "answer": "Compilation"
            },
            {
                "question": "In Python, which function is used to initialize an object's state?",
                "options": ["__init__", "__new__", "__class__", "__del__"],
                "answer": "__init__"
            },
            {
                "question": "What is the time complexity of searching in a balanced Binary Search Tree (BST)?",
                "options": ["O(1)", "O(n)", "O(log n)", "O(n log n)"],
                "answer": "O(log n)"
            }
        ]
        
    # 2. Career & Resume Placement
    elif any(k in title_lower for k in ['resume', 'cv', 'linkedin', 'career', 'interview', 'mock', 'job', 'placement']):
        summary = (
            f"### Lecture Summary: {service_title}\n\n"
            "The session covered vital steps in career placements and portfolio positioning:\n"
            "- **ATS Optimization**: Addressed key parameters scanned by applicant tracking systems.\n"
            "- **Action Verbs**: Replaced passive phrases with impact verbs (e.g., 'led', 'architected', 'optimized').\n"
            "- **LinkedIn Positioning**: Structured biography summaries and added skill tags to improve SEO visibility.\n"
            "- **Behavioral Interviewing**: Walked through the STAR method (Situation, Task, Action, Result) for case questions."
        )
        
        notes = (
            f"### Career Placement Guide: {service_title}\n\n"
            "#### 1. The STAR Method Worksheet\n"
            "- **Situation**: Set the scene and details of your challenge (15% of description).\n"
            "- **Task**: Outline your specific responsibility and requirements (15%).\n"
            "- **Action**: Explain the exact technical steps you took to resolve it (60%).\n"
            "- **Result**: Detail the measurable outcomes (e.g. saved 20 hours, optimized load time by 30%) (10%).\n\n"
            "#### 2. Power Verbs List\n"
            "- Instead of 'helped with database', use **'Architected relational schema'**.\n"
            "- Instead of 'wrote code', use **'Engineered scalable microservices'**.\n"
            "- Instead of 'ran meetings', use **'Facilitated cross-functional design reviews'**."
        )
        
        quiz_data = [
            {
                "question": "What does the 'A' stand for in the STAR method for answering interview questions?",
                "options": ["Analogy", "Assessment", "Action", "Attribute"],
                "answer": "Action"
            },
            {
                "question": "How should you format a resume to pass Applicant Tracking Systems (ATS)?",
                "options": ["Use multi-column complex tables", "Use clean, single-column text formatting", "Embed images of your certificates", "Use unique cursive fonts"],
                "answer": "Use clean, single-column text formatting"
            },
            {
                "question": "Where is the best place on LinkedIn to place core SEO keywords?",
                "options": ["In the headline and skills section", "In private messages only", "In profile picture metadata", "In settings menu"],
                "answer": "In the headline and skills section"
            }
        ]
        
    # 3. Creative & Graphics Design
    elif any(k in title_lower for k in ['logo', 'design', 'graphics', 'banner', 'branding', 'vector', 'illustrator', 'photoshop', 'art']):
        summary = (
            f"### Lecture Summary: {service_title}\n\n"
            "The lesson focused on creative designs and professional production pipelines:\n"
            "- **Vector vs Raster**: Discussed scaling limitations of resolution-dependent assets.\n"
            "- **Color Harmonies**: Explored color theory, contrast ratios, and accessible designs (WCAG standards).\n"
            "- **Typography Rules**: Analyzed kerning, leading, and font pairings (e.g., Sans-serif headers with Serif body text).\n"
            "- **Asset Delivery**: Reviewed file hand-off parameters including bleed areas and transparent exports."
        )
        
        notes = (
            f"### Graphic Design Handout: {service_title}\n\n"
            "#### 1. Common Design Formats\n"
            "- **SVG**: Scalable Vector Graphics. Best for logos and icons.\n"
            "- **PNG**: Portable Network Graphics. Best for screen designs requiring transparency.\n"
            "- **PDF**: Portable Document Format. Standard for print delivery.\n\n"
            "#### 2. Contrast Ratios & Accessibility\n"
            "- Text elements must have a contrast ratio of at least **4.5:1** against the background for AA compliance.\n"
            "- Limit typeface selections to **2 font families** per branding guide to avoid chaotic page designs."
        )
        
        quiz_data = [
            {
                "question": "Which file format is resolution-independent and can scale infinitely without pixelating?",
                "options": ["PNG", "JPEG", "SVG", "GIF"],
                "answer": "SVG"
            },
            {
                "question": "What is the standard contrast ratio required for normal text under WCAG AA standards?",
                "options": ["2.0:1", "3.0:1", "4.5:1", "7.0:1"],
                "answer": "4.5:1"
            },
            {
                "question": "What does the term 'leading' refer to in typography?",
                "options": ["Space between characters", "Space between lines of text", "The size of capital letters", "Horizontal alignment"],
                "answer": "Space between lines of text"
            }
        ]
        
    # 4. Lecture Notes & DSA study materials
    elif any(k in title_lower for k in ['notes', 'study', 'exam', 'dsa', 'lecture', 'cheat', 'semester']):
        summary = (
            f"### Lecture Summary: {service_title}\n\n"
            "Academic study strategies and structural breakdowns covered:\n"
            "- **Memory retention**: Discussed spaced repetition and visual card recall structures.\n"
            "- **Syllabus Mapping**: Created modular sections targeting high-scoring topics.\n"
            "- **Problem Solving**: Walked through analytical structures of past paper solutions.\n"
            "- **Exam Day Execution**: Managed time allotment strategies per mark."
        )
        
        notes = (
            f"### Academic Study Cheat Sheet: {service_title}\n\n"
            "#### 1. Pomodoro Technique Study Cycle\n"
            "1. Study focused for **25 minutes** (no notifications, single-tasking).\n"
            "2. Take a **5-minute break** to rest your eyes.\n"
            "3. Repeat 4 times, then take a **30-minute long break**.\n\n"
            "#### 2. Spaced Repetition Timeline\n"
            "- **Review 1**: 1 day after learning.\n"
            "- **Review 2**: 3 days after learning.\n"
            "- **Review 3**: 7 days after learning.\n"
            "- **Review 4**: 14 days after learning."
        )
        
        quiz_data = [
            {
                "question": "What is the core focus of the Pomodoro technique?",
                "options": ["Writing long outlines", "Dividing study sessions into focused intervals", "Doing group study checks", "Sleeping before exams"],
                "answer": "Dividing study sessions into focused intervals"
            },
            {
                "question": "According to memory retention science, what is the best timing for the first review of new material?",
                "options": ["1 day after learning", "1 week after learning", "1 month after learning", "Only on the exam day"],
                "answer": "1 day after learning"
            },
            {
                "question": "What is 'Active Recall'?",
                "options": ["Reading a page over and over", "Testing yourself without looking at the notes", "Listening to lecture recordings passively", "Highlighting text in multiple colors"],
                "answer": "Testing yourself without looking at the notes"
            }
        ]
        
    # 5. Default Fallback
    else:
        summary = (
            f"### Lecture Summary: {service_title}\n\n"
            "The learning session was completed successfully. Core discussions covered:\n"
            "- **Foundational principles**: Reviewed basic framework outlines and workflow definitions.\n"
            "- **Practical application**: Walked through exercises, examples, and hands-on drills.\n"
            "- **Troubleshooting & Q&A**: Solved edge-cases, common mistakes, and clarified peer feedback.\n"
            "- **Next Steps planning**: Formulated checklist timelines for self-directed study."
        )
        
        notes = (
            f"### Lecture Notes & Materials: {service_title}\n\n"
            "#### 1. Core Guidelines\n"
            "- Break complex tasks into smaller, manageable sub-goals.\n"
            "- Verify each step incrementally before moving forward.\n"
            "- Keep a log of errors or challenges encountered to build cumulative wisdom.\n\n"
            "#### 2. Study Recommendations\n"
            "- Allocate 1-2 hours of practice for every hour of lecture.\n"
            "- Collaborate with peers on Broke Geniuses to trade skills and reviews."
        )
        
        quiz_data = [
            {
                "question": "What is the recommended first step when solving a complex technical challenge?",
                "options": ["Code everything all at once", "Break it down into smaller, verify-able parts", "Skip planning and search online first", "Delegate the entire task immediately"],
                "answer": "Break it down into smaller, verify-able parts"
            },
            {
                "question": "How can you reinforce skills learned in a tutoring session?",
                "options": ["Reread slides passively", "Practice immediately with hands-on exercises", "Wait until the exam to review", "Uninstall your text editor"],
                "answer": "Practice immediately with hands-on exercises"
            },
            {
                "question": "What is the primary benefit of peer-to-peer student marketplaces?",
                "options": ["Avoiding homework entirely", "Trading skills and beating the student budget", "Replacing university degrees", "Earning millions overnight"],
                "answer": "Trading skills and beating the student budget"
            }
        ]
        
    if transcript_text:
        words = transcript_text.lower()
        additional_summary = []
        if "flask" in words or "route" in words:
            additional_summary.append("- **Technical Deep-dive**: Reviewed Flask routing mechanisms and HTTP request methods.")
        if "database" in words or "sql" in words or "query" in words:
            additional_summary.append("- **Database Analysis**: Inspected relational DB schemas, SQL joins, and query optimizations.")
        if "css" in words or "bootstrap" in words or "html" in words:
            additional_summary.append("- **UI Styling**: Addressed styling structures, selectors, and layout margins.")
            
        if additional_summary:
            summary += "\n" + "\n".join(additional_summary)
            
    return summary, json.dumps(quiz_data), notes


@session_bp.route('/orders/<int:order_id>/session', methods=['GET'])
@login_required
def join_session(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Access Control: Only buyer or seller
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        flash("You are not authorized to view this session.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    if order.status not in ['Accepted', 'Completed']:
        flash("Sessions can only be accessed for accepted or completed orders.", "warning")
        return redirect(url_for('profile.view_profile'))
        
    # Get or create SessionRoom
    session_room = SessionRoom.query.filter_by(order_id=order.id).first()
    if not session_room:
        session_room = SessionRoom(order_id=order.id)
        db.session.add(session_room)
        db.session.commit()
        
    # If session has already ended, redirect to the package view
    if not session_room.is_active or order.status == 'Completed':
        return redirect(url_for('session.view_package', order_id=order.id))
        
    # Determine roles
    is_seller = (current_user.id == order.seller_id)
    partner = order.buyer if is_seller else order.seller_user
    
    return render_template(
        'sessions/room.html',
        order=order,
        session_room=session_room,
        is_seller=is_seller,
        partner=partner
    )


@session_bp.route('/orders/<int:order_id>/session/consent', methods=['POST'])
@login_required
def toggle_consent(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    session_room = SessionRoom.query.filter_by(order_id=order.id).first()
    if not session_room:
        return jsonify({'error': 'Session not found'}), 404
        
    data = request.get_json() or {}
    consent = bool(data.get('consent', False))
    
    session_room.consent_given = consent
    db.session.commit()
    
    return jsonify({'success': True, 'consent': session_room.consent_given})


@session_bp.route('/orders/<int:order_id>/session/send-transcript', methods=['POST'])
@login_required
def send_transcript(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    session_room = SessionRoom.query.filter_by(order_id=order.id).first()
    if not session_room or not session_room.is_active:
        return jsonify({'error': 'Active session not found'}), 404
        
    data = request.get_json() or {}
    sender_name = data.get('sender', current_user.name)
    message_text = data.get('text', '').strip()
    
    if not message_text:
        return jsonify({'error': 'Message empty'}), 400
        
    # Append message to transcript with sender label
    timestamp = datetime.now().strftime('%H:%M:%S')
    new_entry = f"[{timestamp}] {sender_name}: {message_text}\n"
    session_room.transcript = (session_room.transcript or '') + new_entry
    db.session.commit()
    
    return jsonify({'success': True, 'transcript': session_room.transcript})


@session_bp.route('/orders/<int:order_id>/session/end', methods=['POST'])
@login_required
def end_session(order_id):
    order = Order.query.get_or_404(order_id)
    # Only the seller (tutor) can end the session
    if order.seller_id != current_user.id:
        flash("Only the seller (tutor) can end this session.", "danger")
        return redirect(url_for('session.join_session', order_id=order.id))
        
    session_room = SessionRoom.query.filter_by(order_id=order.id).first()
    if not session_room:
        flash("Session not found.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    # Mark active as False
    session_room.is_active = False
    order.status = 'Completed'
    
    # AI Generator call: if consent is given, process notes, quizzes and summary!
    if session_room.consent_given:
        summary, quiz, notes = generate_session_package(
            order.service.title, 
            order.service.description, 
            session_room.transcript
        )
        session_room.summary = summary
        session_room.quiz = quiz
        session_room.notes = notes
        session_room.is_locked = True # locked by default
    else:
        # No consent: session package is empty
        session_room.summary = ""
        session_room.quiz = ""
        session_room.notes = ""
        session_room.is_locked = False
        
    db.session.commit()
    
    flash("Tutoring session has ended. Order marked as completed!", "success")
    return redirect(url_for('session.view_package', order_id=order.id))


@session_bp.route('/orders/<int:order_id>/session/package', methods=['GET'])
@login_required
def view_package(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    session_room = SessionRoom.query.filter_by(order_id=order.id).first()
    if not session_room:
        flash("Session room not found.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    # Parse quiz JSON if unlocked and exists
    quiz_list = []
    if session_room.quiz:
        try:
            quiz_list = json.loads(session_room.quiz)
        except Exception as e:
            print("Error parsing quiz JSON:", e)
            
    is_seller = (current_user.id == order.seller_id)
    
    # If the current user is the seller, they can see the package contents without paying
    show_locked = session_room.is_locked and not session_room.is_paid and not is_seller
    
    # Check if there files shared in the directory
    shared_files = []
    folder_path = os.path.join(current_app.config['SESSION_FILES_DIR'], str(order.id))
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_url = url_for('static', filename=f'session_files/{order.id}/{filename}')
            shared_files.append({
                'name': filename,
                'url': file_url
            })
            
    stripe_enabled = bool(current_app.config.get('STRIPE_SECRET_KEY')) and (stripe is not None)
    
    return render_template(
        'sessions/package.html',
        order=order,
        session_room=session_room,
        quiz_list=quiz_list,
        show_locked=show_locked,
        is_seller=is_seller,
        shared_files=shared_files,
        stripe_enabled=stripe_enabled,
        stripe_public_key=current_app.config.get('STRIPE_PUBLIC_KEY', '')
    )


@session_bp.route('/orders/<int:order_id>/session/unlock', methods=['POST'])
@login_required
def unlock_package(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        return jsonify({'error': 'Only the buyer can unlock this package'}), 403
        
    session_room = SessionRoom.query.filter_by(order_id=order.id).first()
    if not session_room:
        return jsonify({'error': 'Session not found'}), 404
        
    # Process mock payment
    session_room.is_paid = True
    session_room.is_locked = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Session package successfully unlocked! Enjoy your summaries and quizzes.'
    })


@session_bp.route('/orders/<int:order_id>/session/upload-file', methods=['POST'])
@login_required
def upload_file(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error': 'No file uploaded'}), 400
        
    if not allowed_session_file(file.filename):
        return jsonify({'error': 'Invalid file format. Allowed formats: pdf, doc, docx, ppt, pptx, txt, zip, png, jpg, jpeg.'}), 400
        
    # Save file in order-specific directory: static/session_files/<order_id>/<filename>
    order_folder = os.path.join(current_app.config['SESSION_FILES_DIR'], str(order.id))
    os.makedirs(order_folder, exist_ok=True)
    
    filename = secure_filename(file.filename)
    # Check if file exists, make unique if needed
    name, ext = os.path.splitext(filename)
            
    unique_filename = filename
    counter = 1
    while os.path.exists(os.path.join(order_folder, unique_filename)):
        unique_filename = f"{name}_{counter}{ext}"
        counter += 1
        
    file_path = os.path.join(order_folder, unique_filename)
    file.save(file_path)
    
    file_url = url_for('static', filename=f'session_files/{order.id}/{unique_filename}')
    
    return jsonify({
        'success': True,
        'filename': unique_filename,
        'url': file_url
    })


@session_bp.route('/orders/<int:order_id>/session/create-checkout', methods=['POST'])
@login_required
def create_checkout(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash("Only the buyer can purchase this package.", "danger")
        return redirect(url_for('session.view_package', order_id=order.id))
        
    if not stripe or not current_app.config.get('STRIPE_SECRET_KEY'):
        flash("Stripe payment gateway is not configured on this server.", "warning")
        return redirect(url_for('session.view_package', order_id=order.id))
        
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': f"Study Package - {order.service.title}",
                        'description': f"AI-generated study materials for your tutoring session on Order #{order.id}.",
                    },
                    'unit_amount': 10000, # ₹100.00 in paise
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('session.payment_success', order_id=order.id, _external=True),
            cancel_url=url_for('session.view_package', order_id=order.id, _external=True),
            metadata={
                'order_id': str(order.id),
                'buyer_id': str(current_user.id)
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        print("Stripe Checkout Error:", e)
        flash("Failed to generate payment session. Please try again.", "danger")
        return redirect(url_for('session.view_package', order_id=order.id))


@session_bp.route('/orders/<int:order_id>/session/success', methods=['GET'])
@login_required
def payment_success(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    session_room = SessionRoom.query.filter_by(order_id=order.id).first()
    if session_room:
        session_room.is_paid = True
        session_room.is_locked = False
        db.session.commit()
        flash("Payment completed successfully! Your study materials are unlocked.", "success")
        
    return redirect(url_for('session.view_package', order_id=order.id))


@session_bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    if not stripe:
        return 'Stripe not installed', 400
        
    payload = request.data
    sig_header = request.headers.get('STRIPE_SIGNATURE')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    
    if not sig_header or not webhook_secret:
        return 'Signature or Secret missing', 400
        
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        metadata = session_obj.get('metadata', {})
        order_id_str = metadata.get('order_id')
        
        if order_id_str:
            try:
                order_id = int(order_id_str)
                session_room = SessionRoom.query.filter_by(order_id=order_id).first()
                if session_room:
                    session_room.is_paid = True
                    session_room.is_locked = False
                    db.session.commit()
            except Exception as e:
                print("Webhook DB Update Error:", e)
                return 'DB Update Error', 500
                
    return 'Success', 200
