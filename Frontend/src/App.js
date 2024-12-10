import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Login from './Login';
import FileProcessor from './FileProcessor';

function App() {
  const [token, setToken] = useState(null);

  useEffect(() => {
    // Al montar el componente, leer el token del localStorage
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  useEffect(() => {
    // Cada vez que el token cambie, actualizar localStorage
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);

  return (
    <Router>
      <Routes>
        {!token ? (
          <Route path="/" element={<Login setToken={setToken} />} />
        ) : (
          <Route path="/" element={<FileProcessor token={token} setToken={setToken} />} />
        )}
      </Routes>
    </Router>
  );
}

export default App;