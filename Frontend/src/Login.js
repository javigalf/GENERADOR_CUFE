import React, { useState } from 'react';
import axios from 'axios';
import './Login.css'; // Asegúrate de importar el archivo CSS

const Login = ({ setToken }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:8000/api/token/', {
        username,
        password
      });
      setToken(response.data.access);
    } catch (err) {
      setError('Credenciales inválidas');
    }
  };

  return (
    <div className="container">
      <div className="heading">Iniciar Sesión</div>
      <form onSubmit={handleSubmit} className="form">
        <input
          required
          className="input"
          type="text"
          name="username"
          id="username"
          placeholder="Usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          required
          className="input"
          type="password"
          name="password"
          id="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <span className="forgot-password"><a href="#">¿Olvidaste tu contraseña?</a></span>
        <input className="login-button" type="submit" value="Ingresar" />
      </form>
      {/* Opcional: Agregar las cuentas sociales si lo deseas */}
      {/* <div className="social-account-container">
        <span className="title">O inicia sesión con</span>
        <div className="social-accounts">
          <button className="social-button google">
            // SVG de Google
          </button>
          <button className="social-button apple">
            // SVG de Apple
          </button>
          <button className="social-button twitter">
            // SVG de Twitter
          </button>
        </div>
      </div> */}
      <span className="agreement"><a href="#">Conoce el acuerdo de licencia de usuario</a></span>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default Login;
