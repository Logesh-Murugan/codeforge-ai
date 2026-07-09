import React from 'react';
import { useNotes } from '../lib/api';

export default function DashboardPage() {
  const { data, error, isLoading } = useNotes();

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p style={{ color: 'red' }}>{error.message}</p>;

  return (
    <div>
      <h1>Notes</h1>
      <ul>
        {data.map((note) => (
          <li key={note.id}>{note.content}</li>
        ))}
      </ul>
    </div>
  );
}