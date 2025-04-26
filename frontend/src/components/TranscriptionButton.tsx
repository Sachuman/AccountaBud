import React from 'react';
import { Mic } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface TranscriptionButtonProps {
  isActive?: boolean;
  onClick?: () => void;
}

const TranscriptionButton = ({ isActive = false, onClick }: TranscriptionButtonProps) => {
  return (
    <Button
      size="icon"
      variant="secondary"
      className="w-24 h-24 rounded-full transition-all duration-300 hover:scale-105 shine-effect"
      onClick={onClick}
    >
      <Mic className={`w-12 h-12 transition-colors ${isActive ? 'text-primary' : 'text-secondary-foreground'}`} />
    </Button>
  );
};

export default TranscriptionButton;
