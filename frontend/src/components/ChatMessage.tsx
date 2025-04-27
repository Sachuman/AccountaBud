
import React from 'react';
import { cn } from "@/lib/utils";
import { User, TreePine } from "lucide-react";

interface ChatMessageProps {
  isAi: boolean;
  message: string;
  timestamp: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ isAi, message, timestamp }) => {
  return (
    <div className  ={cn(
      "flex gap-3 message-appear",
      isAi ? "flex-row" : "flex-row-reverse"
    )}>
      <div className={cn(
        "flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md border",
        isAi ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
      )}>
        {isAi ? <TreePine className="h-4 w-4" /> : <User className="h-4 w-4" />}
      </div>
      <div className={cn(
        "flex flex-col gap-1 min-w-0 max-w-[80%]",
        isAi ? "items-start" : "items-end"
      )}>
        <div className={cn(
          "rounded-lg px-4 py-2 text-sm",
          isAi ? "bg-card text-card-foreground" : "bg-primary text-primary-foreground"
        )}>
          {message}
        </div>
        <span className="text-xs text-muted-foreground px-2">{timestamp}</span>
      </div>
    </div>
  );
};

export default ChatMessage;
