import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const apiURL = 'http://localhost:8000';

const useLogin = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const queryClient = useQueryClient();

  const { mutate, isLoading, error } = useMutation(
    async () => {
      const response = await fetch(`${apiURL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      return response.json();
    },
    {
      onSuccess: (data) => {
        localStorage.setItem('token', data.access_token);
        queryClient.invalidateQueries();
      },
    }
  );

  return { mutate, isLoading, error };
};

const useRegister = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const queryClient = useQueryClient();

  const { mutate, isLoading, error } = useMutation(
    async () => {
      const response = await fetch(`${apiURL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
      });
      return response.json();
    },
    {
      onSuccess: (data) => {
        localStorage.setItem('token', data.access_token);
        queryClient.invalidateQueries();
      },
    }
  );

  return { mutate, isLoading, error };
};

const useGetNotes = () => {
  const token = localStorage.getItem('token');
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery(
    ['notes'],
    async () => {
      const response = await fetch(`${apiURL}/notes`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.json();
    },
    {
      staleTime: 10000,
    }
  );

  return { data, isLoading, error };
};

const useCreateNote = () => {
  const token = localStorage.getItem('token');
  const queryClient = useQueryClient();

  const { mutate, isLoading, error } = useMutation(
    async (note) => {
      const response = await fetch(`${apiURL}/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(note),
      });
      return response.json();
    },
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries('notes');
      },
    }
  );

  return { mutate, isLoading, error };
};

export { useLogin, useRegister, useGetNotes, useCreateNote };