import React from 'react';
import { Mail, ArrowRight } from 'lucide-react';
import api from '../services/api';

function Login() {
  const handleLogin = async () => {
    try {
      const response = await api.get('/auth/google/url');
      if (response.data && response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (error) {
      console.error("Failed to get Google login URL:", error);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="icon-wrapper">
          <Mail size={32} className="text-accent" />
        </div>
        <h1>Accountability Assistant</h1>
        <p className="subtitle">Never miss an important email or deadline again.</p>
        
        <button className="btn-primary login-btn" onClick={handleLogin}>
          <span>Continue with Google</span>
          <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}

export default Login;
