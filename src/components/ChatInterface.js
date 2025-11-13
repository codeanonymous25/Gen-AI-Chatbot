import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const ChatInterface = ({ user, onLogout, theme, onToggleTheme }) => {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [fileContext, setFileContext] = useState('');
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [loading, setLoading] = useState(false);
  const [editingSession, setEditingSession] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadSessions = async () => {
    try {
      const response = await axios.get(`/api/sessions?user_id=${user.id}`);
      setSessions(response.data.sessions);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await axios.post('/api/sessions', {
        user_id: user.id,
        title: 'New Chat'
      });
      const newSession = { id: response.data.session_id, title: response.data.title };
      setSessions([newSession, ...sessions]);
      setCurrentSession(newSession);
      setMessages([]);
      setFileContext('');
      setUploadedFileName('');
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const selectSession = async (session) => {
    setCurrentSession(session);
    try {
      const response = await axios.get(`/api/messages/${session.id}`);
      setMessages(response.data.messages);
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      await axios.delete(`/api/sessions/${sessionId}`);
      setSessions(sessions.filter(s => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const startRenaming = (session) => {
    setEditingSession(session.id);
    setEditTitle(session.title);
  };

  const saveRename = async (sessionId) => {
    try {
      await axios.put(`/api/sessions/${sessionId}`, {
        title: editTitle
      });
      setSessions(sessions.map(s => 
        s.id === sessionId ? { ...s, title: editTitle } : s
      ));
      if (currentSession?.id === sessionId) {
        setCurrentSession({ ...currentSession, title: editTitle });
      }
      setEditingSession(null);
    } catch (error) {
      console.error('Error renaming session:', error);
    }
  };

  const updateSessionTitle = async (sessionId) => {
    try {
      const response = await axios.post(`/api/sessions/${sessionId}/update-title`);
      if (response.data.success) {
        setSessions(sessions.map(s => 
          s.id === sessionId ? { ...s, title: response.data.title } : s
        ));
        if (currentSession?.id === sessionId) {
          setCurrentSession({ ...currentSession, title: response.data.title });
        }
      }
    } catch (error) {
      console.error('Error updating title:', error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !currentSession) return;

    const userMessage = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await axios.post('/api/chat', {
        message: input,
        user_id: user.id,
        session_id: currentSession.id,
        file_context: fileContext
      });

      const botMessage = { text: response.data.response, sender: 'bot' };
      setMessages(prev => [...prev, botMessage]);
      
      // Update session title if it's still "New Chat"
      if (currentSession.title === 'New Chat') {
        updateSessionTitle(currentSession.id);
      }
    } catch (error) {
      const errorMessage = { text: 'Error: Could not get response', sender: 'bot' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file || !currentSession) return;

    // Show file upload message
    const fileMessage = { text: `📎 Uploaded: ${file.name}`, sender: 'user' };
    setMessages(prev => [...prev, fileMessage]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/upload', formData);
      setFileContext(response.data.content);
      setUploadedFileName(file.name);
      
      const analysisMessage = { text: response.data.analysis, sender: 'bot' };
      setMessages(prev => [...prev, analysisMessage]);
      
      // Update session title with filename if it's still "New Chat"
      if (currentSession.title === 'New Chat') {
        const newTitle = `📄 ${file.name}`;
        await axios.put(`/api/sessions/${currentSession.id}`, {
          title: newTitle
        });
        setSessions(sessions.map(s => 
          s.id === currentSession.id ? { ...s, title: newTitle } : s
        ));
        setCurrentSession({ ...currentSession, title: newTitle });
      }
    } catch (error) {
      const errorMessage = { text: 'Error: Could not analyze file', sender: 'bot' };
      setMessages(prev => [...prev, errorMessage]);
    }
    
    // Reset file input
    event.target.value = '';
  };

  return (
    <div className="chat-interface">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={createNewSession}>
            ✨ New AI Chat
          </button>
        </div>
        
        <div className="sessions-list">
          {sessions.map(session => (
            <div 
              key={session.id} 
              className={`session-item ${currentSession?.id === session.id ? 'active' : ''}`}
              onClick={() => selectSession(session)}
            >
              {editingSession === session.id ? (
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onBlur={() => saveRename(session.id)}
                  onKeyPress={(e) => e.key === 'Enter' && saveRename(session.id)}
                  className="edit-title-input"
                  autoFocus
                />
              ) : (
                <span className="session-title">{session.title}</span>
              )}
              <div className="session-actions">
                <button 
                  className="rename-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    startRenaming(session);
                  }}
                  title="Rename"
                >
                  ✏️
                </button>
                <button 
                  className="delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                  title="Delete"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <button className="theme-btn" onClick={onToggleTheme}>
            {theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
          </button>
          <div className="user-info">
            <span>{user.email}</span>
            <button className="logout-btn" onClick={onLogout}>Logout</button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="main-chat">
        {currentSession ? (
          <>
            <div className="messages-container">
              {uploadedFileName && (
                <div className="file-indicator">
                  📄 Active Document: {uploadedFileName}
                  <br />🧠 AI is ready to answer questions about this file!
                </div>
              )}
              {messages.map((message, index) => (
                <div key={index} className={`message ${message.sender}`}>
                  <div className="message-content">
                    <pre>{message.text}</pre>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="message bot">
                  <div className="message-content">
                    <div className="typing-indicator">🧠 AI is thinking...</div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
              <div className="input-container">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  accept=".txt,.pdf,.doc,.docx"
                  style={{ display: 'none' }}
                />
                <button 
                  className="file-btn"
                  onClick={() => fileInputRef.current?.click()}
                  title="Upload file"
                >
                  📎
                </button>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={fileContext ? "💬 Ask me anything about your document..." : "🚀 What would you like to know?"}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  disabled={loading}
                />
                <button 
                  className="send-btn"
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                >
                  ➤
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="welcome-screen">
            <h2>🤖 AI Document Genius</h2>
            <p>🚀 Transform your documents into intelligent conversations</p>
            <div className="welcome-features">
              <div className="feature">📄 Smart Analysis - PDF, DOCX, TXT files</div>
              <div className="feature">💬 Interactive Q&A - Ask anything about your docs</div>
              <div className="feature">🔍 Instant Insights - Get structured summaries</div>
              <div className="feature">🧠 AI-Powered - Gemini 2.5 Flash technology</div>
            </div>
            <button className="btn-primary" onClick={createNewSession}>
              ✨ Start Your AI Journey
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;