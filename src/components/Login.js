import React, { useState } from 'react';
import axios from 'axios';

const Login = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const endpoint = isLogin ? '/api/login' : '/api/register';
    
    try {
      const response = await axios.post(endpoint, {
        email,
        password
      });
      
      if (response.data.success) {
        onLogin({
          id: response.data.user_id,
          email: response.data.email
        });
      } else {
        setError(response.data.error);
      }
    } catch (error) {
      setError('Connection error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>🤖 AI Analyzer</h1>
        <h2>{isLogin ? '🚀 Welcome back!' : '✨ Join the future'}</h2>
        
        {error && <div className="error-message">⚠️ {error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <input
              type="email"
              placeholder="📧 Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <input
              type="password"
              placeholder="🔒 Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? '⏳ Processing...' : (isLogin ? '🚀 Sign In' : '✨ Create Account')}
          </button>
        </form>
        
        <div className="toggle-auth">
          {isLogin ? "New to AI Analyzer? " : "Already have an account? "}
          <button 
            type="button"
            className="link-button"
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
          >
            {isLogin ? '✨ Sign up' : '🚀 Sign in'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;