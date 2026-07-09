import React from 'react';
import { useNotes } from '../lib/api';

export default function HomePage() {
  const { data, error, isLoading, isError } = useNotes();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (isError) {
    return <div>Error: {error.message}</div>;
  }

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