"use client";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input"; // Using Input for a simpler box
import { Mic, Send } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend }) => {
  const [message, setMessage] = useState("");

  const handleSend = () => {
    if (message.trim()) {
      onSend(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Use KeyboardEvent<HTMLInputElement> if using Input
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    // Fixed position at bottom center
    <div className="fixed bottom-4 left-1/2 z-50 w-full max-w-md -translate-x-1/2 px-4">
      {/* Flex container for input and buttons */}
      <div className="flex w-full items-center space-x-2 rounded-full border bg-background p-1 shadow-md">
        <Input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          // Minimal styling: take available space, remove default borders/outline
          className="flex-1 border-none bg-transparent px-3 py-2 outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
        />
        <Button
          type="submit" // Use type="submit" if inside a form, otherwise button is fine
          size="icon"
          onClick={handleSend}
          disabled={!message.trim()}
          className="flex-shrink-0 rounded-full" // Ensure button doesn't shrink
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">Send message</span>
        </Button>
        <Button
          size="icon"
          variant="secondary"
          className="flex-shrink-0 rounded-full" // Ensure button doesn't shrink
        >
          <Mic className="h-4 w-4" />
          <span className="sr-only">Use microphone</span>
        </Button>
      </div>
    </div>
  );
};

export default ChatInput;
