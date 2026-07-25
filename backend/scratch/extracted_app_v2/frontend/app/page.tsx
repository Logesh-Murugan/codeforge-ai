import React from 'react';
import { useGetUser } from '../lib/api';

export default function HomePage() {
  const { data, isLoading, error } = useGetUser();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Welcome, {data.username}!</h1>
    </div>
  );
}