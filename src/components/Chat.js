import React, { useState } from 'react';
import axios from 'axios';

const Chat = ({ user }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    
    try {
      const response = await axios.post('http://localhost:5000/api/chat', {
        message: input,
        user_id: user.id
      });
      
      const botMessage = { text: response.data.response, sender: 'bot' };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = { text: 'Error: Could not get response', sender: 'bot' };
      setMessages(prev => [...prev, errorMessage]);
    }
    
    setInput('');
  };

  const uploadFile = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5000/api/upload', formData);
      const analysisMessage = { text: `File Analysis: ${response.data.analysis}`, sender: 'bot' };
      setMessages(prev => [...prev, analysisMessage]);
    } catch (error) {
      const errorMessage = { text: 'Error: Could not analyze file', sender: 'bot' };
      setMessages(prev => [...prev, errorMessage]);
    }
    
    setFile(null);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>File Analysis Chatbot</h2>
        <p>Welcome, {user.username}!</p>
      </div>
      
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}-message`}>
            <pre style={{whiteSpace: 'pre-wrap', fontFamily: 'inherit'}}>
              {message.text}
            </pre>
          </div>
        ))}
      </div>
      
      <div className="file-upload">
        <input
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
          accept=".txt,.pdf,.doc,.docx"
        />
        <button onClick={uploadFile} disabled={!file}>
          Upload & Analyze
        </button>
      </div>
      
      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};

export default Chat;