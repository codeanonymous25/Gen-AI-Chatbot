import unittest
import json
import tempfile
import os
import sqlite3
from app import app, init_db
import uuid

class ChatbotTestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Use unique email for each test
        self.test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
    def tearDown(self):
        # Clean up test data
        try:
            conn = sqlite3.connect('chatbot.db')
            c = conn.cursor()
            # Get user IDs to delete related data
            c.execute("SELECT id FROM users WHERE email LIKE 'test_%@example.com'")
            user_ids = [row[0] for row in c.fetchall()]
            
            # Delete related data
            for user_id in user_ids:
                c.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
                c.execute("DELETE FROM chat_sessions WHERE user_id=?", (user_id,))
            
            # Delete test users
            c.execute("DELETE FROM users WHERE email LIKE 'test_%@example.com'")
            conn.commit()
            conn.close()
        except:
            pass
        
    def test_register_user(self):
        """Test user registration"""
        response = self.app.post('/api/register', 
                                json={'email': self.test_email, 'password': 'password123'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['email'], self.test_email)
    
    def test_register_duplicate_user(self):
        """Test duplicate user registration"""
        # Register first user
        self.app.post('/api/register', 
                     json={'email': self.test_email, 'password': 'password123'})
        # Try to register same user again
        response = self.app.post('/api/register', 
                                json={'email': self.test_email, 'password': 'password123'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Email already exists')
    
    def test_login_valid_user(self):
        """Test login with valid credentials"""
        # Register user first
        self.app.post('/api/register', 
                     json={'email': self.test_email, 'password': 'password123'})
        # Login
        response = self.app.post('/api/login', 
                                json={'email': self.test_email, 'password': 'password123'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['email'], self.test_email)
    
    def test_login_invalid_user(self):
        """Test login with invalid credentials"""
        response = self.app.post('/api/login', 
                                json={'email': 'invalid@example.com', 'password': 'wrongpassword'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Invalid email or password')
    
    def test_create_session(self):
        """Test creating a chat session"""
        # Register and get user_id
        reg_response = self.app.post('/api/register', 
                                    json={'email': self.test_email, 'password': 'password123'})
        reg_data = json.loads(reg_response.data)
        if not reg_data.get('success'):
            self.skipTest(f"Registration failed: {reg_data}")
        user_id = reg_data['user_id']
        
        # Create session
        response = self.app.post('/api/sessions', 
                                json={'user_id': user_id, 'title': 'Test Chat'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], 'Test Chat')
        self.assertIsNotNone(data['session_id'])
    
    def test_get_sessions(self):
        """Test getting user sessions"""
        # Register and create session
        reg_response = self.app.post('/api/register', 
                                    json={'email': self.test_email, 'password': 'password123'})
        reg_data = json.loads(reg_response.data)
        if not reg_data.get('success'):
            self.skipTest(f"Registration failed: {reg_data}")
        user_id = reg_data['user_id']
        self.app.post('/api/sessions', json={'user_id': user_id, 'title': 'Test Chat'})
        
        # Get sessions
        response = self.app.get(f'/api/sessions?user_id={user_id}')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['sessions']), 1)
        self.assertEqual(data['sessions'][0]['title'], 'Test Chat')
    
    def test_chat_without_message(self):
        """Test chat with empty message"""
        response = self.app.post('/api/chat', 
                                json={'message': '', 'user_id': 1, 'session_id': 1})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['response'], 'Please enter a message')
    
    def test_file_upload_no_file(self):
        """Test file upload without file"""
        response = self.app.post('/api/upload')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['error'], 'No file uploaded')
    
    def test_file_upload_txt(self):
        """Test text file upload"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('This is a test document for analysis.')
            f.flush()
            
            with open(f.name, 'rb') as test_file:
                response = self.app.post('/api/upload', 
                                        data={'file': (test_file, 'test.txt')})
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertIn('analysis', data)
                self.assertIn('content', data)
        
        os.unlink(f.name)
    
    def test_delete_session(self):
        """Test deleting a session"""
        # Create session first
        reg_response = self.app.post('/api/register', 
                                    json={'email': self.test_email, 'password': 'password123'})
        reg_data = json.loads(reg_response.data)
        if not reg_data.get('success'):
            self.skipTest(f"Registration failed: {reg_data}")
        user_id = reg_data['user_id']
        session_response = self.app.post('/api/sessions', 
                                        json={'user_id': user_id, 'title': 'Test Chat'})
        session_id = json.loads(session_response.data)['session_id']
        
        # Delete session
        response = self.app.delete(f'/api/sessions/{session_id}')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
    
    def test_rename_session(self):
        """Test renaming a session"""
        # Create session first
        reg_response = self.app.post('/api/register', 
                                    json={'email': self.test_email, 'password': 'password123'})
        reg_data = json.loads(reg_response.data)
        if not reg_data.get('success'):
            self.skipTest(f"Registration failed: {reg_data}")
        user_id = reg_data['user_id']
        session_response = self.app.post('/api/sessions', 
                                        json={'user_id': user_id, 'title': 'Old Title'})
        session_id = json.loads(session_response.data)['session_id']
        
        # Rename session
        response = self.app.put(f'/api/sessions/{session_id}', 
                               json={'title': 'New Title'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])

if __name__ == '__main__':
    unittest.main()