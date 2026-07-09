import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

const useLogin = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const { mutate, isLoading } = useMutation(
    async (credentials) => {
      const response = await api.post('/auth/login', credentials);
      return response.data;
    },
    {
      onSuccess: (data) => {
        localStorage.setItem('token', data.access_token);
      },
    }
  );

  const handleLogin = async () => {
    mutate({ username, password });
  };

  return { handleLogin, isLoading, error };
};

const useRegister = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const { mutate, isLoading } = useMutation(
    async (credentials) => {
      const response = await api.post('/auth/register', credentials);
      return response.data;
    },
    {
      onSuccess: (data) => {
        localStorage.setItem('token', data.access_token);
      },
    }
  );

  const handleRegister = async () => {
    mutate({ username, email, password });
  };

  return { handleRegister, isLoading, error };
};

const useNotes = () => {
  const { data, error, isLoading } = useQuery(
    ['notes'],
    async () => {
      const response = await api.get('/notes');
      return response.data;
    },
    {
      enabled: !!localStorage.getItem('token'),
    }
  );

  return { data, error, isLoading };
};

export { useLogin, useRegister, useNotes };