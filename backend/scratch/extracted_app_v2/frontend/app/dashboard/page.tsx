import React from 'react';
import { useNotes } from '../lib/api';
import { useCreateNote } from '../lib/api';

export default function DashboardPage() {
  const { data, error, isLoading, isError } = useNotes();
  const { handleCreateNote, isLoading: isCreating, isError: isCreateError } = useCreateNote();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (isError) {
    return <div>Error: {error.message}</div>;
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const note = { content: event.currentTarget.elements.content.value };
    handleCreateNote(note);
  };

  return (
    <div>
      <h1>Dashboard</h1>
      <ul>
        {data.map((note) => (
          <li key={note.id}>{note.content}</li>
        ))}
      </ul>
      <form onSubmit={handleSubmit}>
        <label>
          Content:
          <input type='text' name='content' />
        </label>
        <br />
        <button type='submit'>Create Note</button>
        {isCreating ? <div>Loading...</div> : null}
        {isCreateError ? <div>Error: {error.message}</div> : null}
      </form>
    </div>
  );
}