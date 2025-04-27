"use client";

import React, { createContext, useContext, useState, ReactNode } from 'react';

type UIMode = 'chat' | 'transcription';

interface UIModeContextType {
  mode: UIMode;
  toggleMode: () => void;
}

const UIModeContext = createContext<UIModeContextType | undefined>(undefined);

export const UIModeProvider = ({ children }: { children: ReactNode }) => {
  const [mode, setMode] = useState<UIMode>('chat');

  const toggleMode = () => {
    setMode(prev => prev === 'chat' ? 'transcription' : 'chat');
  };

  return (
    <UIModeContext.Provider value={{ mode, toggleMode }}>
      {children}
    </UIModeContext.Provider>
  );
};

export const useUIMode = () => {
  const context = useContext(UIModeContext);
  if (!context) {
    throw new Error('useUIMode must be used within a UIModeProvider');
  }
  return context;
};
