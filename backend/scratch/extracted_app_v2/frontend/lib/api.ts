import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const apiURL = 'http://localhost:8000';

export function useLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const { mutate, isLoading, isError } = useMutation(
    async () => {
      const response = await fetch(`${apiURL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      return data;
    },
    {
      onSuccess: (data) => {
        localStorage.setItem('token', data.access_token);
      },
    }
  );

  const handleLogin = async () => {
    mutate();
  };

  return { handleLogin, isLoading, isError, error };
}

export function useRegister() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const { mutate, isLoading, isError } = useMutation(
    async () => {
      const response = await fetch(`${apiURL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
      });
      const data = await response.json();
      return data;
    },
    {
      onSuccess: (data) => {
        localStorage.setItem('token', data.access_token);
      },
    }
  );

  const handleRegister = async () => {
    mutate();
  };

  return { handleRegister, isLoading, isError, error };
}

export function useNotes() {
  const { data, error, isLoading, isError } = useQuery(
    'notes',
    async () => {
      const response = await fetch(`${apiURL}/notes`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await response.json();
      return data;
    }
  );

  return { data, error, isLoading, isError };
}

export function useCreateNote() {
  const { mutate, isLoading, isError } = useMutation(
    async (note) => {
      const response = await fetch(`${apiURL}/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(note),
      });
      const data = await response.json();
      return data;
    }
  );

  const handleCreateNote = async (note) => {
    mutate(note);
  };

  return { handleCreateNote, isLoading, isError };
}
