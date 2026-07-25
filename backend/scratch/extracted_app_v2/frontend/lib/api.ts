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
      const data = await response.json();
      return data;
    },
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries('user');
        localStorage.setItem('token', data.access_token);
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
      const data = await response.json();
      return data;
    },
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries('user');
        localStorage.setItem('token', data.access_token);
      },
    }
  );

  return { mutate, isLoading, error };
};

const useGetUser = () => {
  const token = localStorage.getItem('token');
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery(
    'user',
    async () => {
      const response = await fetch(`${apiURL}/users/me`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await response.json();
      return data;
    },
    {
      enabled: !!token,
    }
  );

  return { data, isLoading, error };
};

const useGetNotes = () => {
  const token = localStorage.getItem('token');
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery(
    'notes',
    async () => {
      const response = await fetch(`${apiURL}/notes`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await response.json();
      return data;
    },
    {
      enabled: !!token,
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
      const data = await response.json();
      return data;
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('notes');
      },
    }
  );

  return { mutate, isLoading, error };
};

const useUpdateNote = () => {
  const token = localStorage.getItem('token');
  const queryClient = useQueryClient();

  const { mutate, isLoading, error } = useMutation(
    async (note) => {
      const response = await fetch(`${apiURL}/notes/${note.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(note),
      });
      const data = await response.json();
      return data;
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('notes');
      },
    }
  );

  return { mutate, isLoading, error };
};

const useDeleteNote = () => {
  const token = localStorage.getItem('token');
  const queryClient = useQueryClient();

  const { mutate, isLoading, error } = useMutation(
    async (id) => {
      const response = await fetch(`${apiURL}/notes/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await response.json();
      return data;
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('notes');
      },
    }
  );

  return { mutate, isLoading, error };
};
