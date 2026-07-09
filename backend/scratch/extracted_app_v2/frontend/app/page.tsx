import React from 'react';
import { useLogin } from '../lib/api';

export default function HomePage() {
  const { handleLogin, isLoading, error } = useLogin();

  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');

  const handleUsernameChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setUsername(event.target.value);
  };

  const handlePasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    handleLogin();
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <label>
          Username:
          <input type="text" value={username} onChange={handleUsernameChange} />
        </label>
        <br />
        <label>
          Password:
          <input type="password" value={password} onChange={handlePasswordChange} />
        </label>
        <br />
        <button type="submit" disabled={isLoading}>{isLoading ? 'Loading...' : 'Login'}</button>
        {error && <p style={{ color: 'red' }}>{error.message}</p>}
      </form>
    </div>
  );
}