from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import google.generativeai as genai
import os
from werkzeug.utils import secure_filename
import sqlite3
import hashlib
from datetime import datetime
import docx
import PyPDF2
import io

app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app)

# Configure Gemini AI
api_key = 'AIzaSyC802jbaH8nFnE2i7aM1XE1_ORYRXo-06M'
print(f"API Key configured: {api_key[:10]}...")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Database setup
def init_db():
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat_sessions
                 (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY, session_id INTEGER, user_id INTEGER, message TEXT, response TEXT, timestamp TEXT, file_content TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = hashlib.sha256(data.get('password').encode()).hexdigest()
    
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        user_id = c.lastrowid
        return jsonify({'success': True, 'user_id': user_id, 'email': email})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Email already exists'})
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = hashlib.sha256(data.get('password').encode()).hexdigest()
    
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute("SELECT id, email FROM users WHERE email=? AND password=?", (email, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({'success': True, 'user_id': user[0], 'email': user[1]})
    return jsonify({'success': False, 'error': 'Invalid email or password'})

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    user_id = request.args.get('user_id')
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute("SELECT id, title, created_at FROM chat_sessions WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    sessions = [{'id': row[0], 'title': row[1], 'created_at': row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify({'sessions': sessions})

@app.route('/api/sessions', methods=['POST'])
def create_session():
    data = request.json
    user_id = data.get('user_id')
    title = data.get('title', 'New Chat')
    
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute("INSERT INTO chat_sessions (user_id, title, created_at) VALUES (?, ?, ?)",
             (user_id, title, datetime.now().isoformat()))
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    
    return jsonify({'session_id': session_id, 'title': title})

@app.route('/api/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    c.execute("DELETE FROM chat_sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/sessions/<int:session_id>', methods=['PUT'])
def rename_session(session_id):
    data = request.json
    new_title = data.get('title')
    
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute("UPDATE chat_sessions SET title=? WHERE id=?", (new_title, session_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/sessions/<int:session_id>/update-title', methods=['POST'])
def update_session_title(session_id):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute("SELECT message FROM messages WHERE session_id=? ORDER BY timestamp LIMIT 1", (session_id,))
    first_message = c.fetchone()
    
    if first_message:
        title = first_message[0][:30] + "..." if len(first_message[0]) > 30 else first_message[0]
        c.execute("UPDATE chat_sessions SET title=? WHERE id=?", (title, session_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'title': title})
    
    conn.close()
    return jsonify({'success': False})

@app.route('/api/messages/<int:session_id>', methods=['GET'])
def get_messages(session_id):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute("SELECT message, response, timestamp FROM messages WHERE session_id=? ORDER BY timestamp", (session_id,))
    messages = []
    for row in c.fetchall():
        messages.append({'text': row[0], 'sender': 'user', 'timestamp': row[2]})
        messages.append({'text': row[1], 'sender': 'bot', 'timestamp': row[2]})
    conn.close()
    return jsonify({'messages': messages})

def extract_text_from_file(file):
    filename = file.filename.lower()
    if filename.endswith('.txt'):
        return file.read().decode('utf-8')
    elif filename.endswith('.docx'):
        doc = docx.Document(io.BytesIO(file.read()))
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    elif filename.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        return '\n'.join([page.extract_text() for page in pdf_reader.pages])
    else:
        return file.read().decode('utf-8', errors='ignore')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    file_context = data.get('file_context', '')
    
    if not message or not message.strip():
        return jsonify({'response': 'Please enter a message'})
    
    try:
        # Get recent conversation history
        conn = sqlite3.connect('chatbot.db')
        c = conn.cursor()
        c.execute("SELECT message, response FROM messages WHERE session_id=? ORDER BY timestamp DESC LIMIT 3", (session_id,))
        recent_messages = c.fetchall()
        conn.close()
        
        # Build conversation context
        conversation_history = ""
        for msg, resp in reversed(recent_messages):
            conversation_history += f"User: {msg}\nAI: {resp}\n\n"
        
        # Build intelligent prompt like ChatGPT/Gemini
        system_prompt = "You are an intelligent AI assistant. Use your full knowledge to provide helpful, accurate, and detailed responses. "
        
        if file_context and conversation_history:
            prompt = f"{system_prompt}Here's our conversation context:\n{conversation_history}\nDocument context:\n{file_context}\n\nUser: {message}\n\nProvide a comprehensive response using the document, our conversation, and your knowledge."
        elif file_context:
            prompt = f"{system_prompt}Document context:\n{file_context}\n\nUser: {message}\n\nAnalyze the document and answer using both the document content and your knowledge."
        elif conversation_history:
            prompt = f"{system_prompt}Previous conversation:\n{conversation_history}\nUser: {message}\n\nRespond naturally using our conversation context and your full knowledge base."
        else:
            prompt = f"{system_prompt}User: {message}\n\nProvide a helpful and informative response."
            
        response = model.generate_content(prompt)
        
        if response and response.text:
            ai_response = response.text
        else:
            ai_response = "I'm sorry, I couldn't generate a response. Please try again."
        
        # Save to database
        conn = sqlite3.connect('chatbot.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (session_id, user_id, message, response, timestamp, file_content) VALUES (?, ?, ?, ?, ?, ?)",
                 (session_id, user_id, message, ai_response, datetime.now().isoformat(), file_context))
        conn.commit()
        conn.close()
        
        return jsonify({'response': ai_response})
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({'response': f'Error: {str(e)}'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    try:
        file_content = extract_text_from_file(file)
        
        if not file_content.strip():
            return jsonify({'analysis': 'File appears to be empty', 'content': ''})
        
        filename = file.filename
        prompt = f"""Analyze the file '{filename}' and provide a structured summary:

### **Title:** [Extract main title/topic]

### **Purpose:**
[2-3 lines describing the main purpose/objective]

---

### **Sections Overview:**

#### ✅ **[Section 1 Name]**
- [Key points from this section]

#### 📝 **[Section 2 Name]**
- [Key points from this section]

#### 🚀 **[Section 3 Name]**
- [Key points from this section]

---

File content:
{file_content[:8000]}

Provide a professional, well-organized analysis."""
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return jsonify({'analysis': response.text, 'content': file_content[:8000]})
        else:
            return jsonify({'analysis': 'Unable to generate analysis for this file', 'content': file_content[:8000]})
            
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'analysis': f'Analysis failed: {str(e)}', 'content': ''})

@app.route('/')
def serve_react_app():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)