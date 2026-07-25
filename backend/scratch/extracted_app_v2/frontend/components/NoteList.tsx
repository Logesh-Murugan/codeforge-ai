import React from 'react';

interface NoteListProps {
  notes: any[];
}

export const NoteList: React.FC<NoteListProps> = ({ notes }) => {
  return (
    <ul>
      {notes.map((note) => (
        <li key={note.id}>{note.content}</li>
      ))}
    </ul>
  );
};