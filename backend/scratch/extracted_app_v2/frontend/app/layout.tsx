import React from 'react';
import '../globals.css';
import { Navbar } from '../components/Navbar';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <head>
        <title>App</title>
      </head>
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  );
}