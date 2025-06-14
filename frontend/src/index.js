import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import axios from 'axios';

// axios 기본 설정
axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);