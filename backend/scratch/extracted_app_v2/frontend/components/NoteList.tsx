import React from 'react';
import { useCreateNote } from '../lib/api';

export default function NoteList({ notes }: { notes: any[] }) {
  const { mutate, isLoading, error } = useCreateNote();

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const note = event.target.note.value;
    mutate({ content: note });
  };

  return (
    <div>
      <h2>Notes</h2>
      <ul>
        {notes.map((note) => (
          <li key={note.id}>{note.content}</li>
        ))}
      </ul>
      <form onSubmit={handleSubmit}>
        <label>
          New Note:
          <input type="text" name="note" />
        </label>
        <br />
        <button type="submit">Create Note</button>
      </form>
      {isLoading ? <div>Loading...</div> : null}
      {error ? <div>Error: {error.message}</div> : null}
    </div>
  );
}