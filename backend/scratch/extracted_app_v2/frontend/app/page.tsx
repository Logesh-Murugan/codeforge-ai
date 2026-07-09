import React from 'react';
import { useGetNotes } from '../lib/api';
import { NoteList } from '../components/NoteList';

export default function HomePage() {
  const { data, isLoading, error } = useGetNotes();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Notes</h1>
      <NoteList notes={data} />
    </div>
  );
}