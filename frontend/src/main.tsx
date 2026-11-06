import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { PetView } from './components/PetView';
import './styles.css';

const petMode = new URLSearchParams(window.location.search).get('pet') === '1';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {petMode ? <PetView /> : <App />}
  </React.StrictMode>,
);
