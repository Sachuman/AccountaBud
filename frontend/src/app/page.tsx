"use client";
import { useState, useRef, useEffect } from "react"; // Import useRef and useEffect
import { TreePine } from "lucide-react";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import TranscriptionButton from "@/components/TranscriptionButton";
import { Button } from "@/components/ui/button";
import { useUIMode } from "@/contexts/UIModeContext";

interface Message {
  id: number;
  isAi: boolean;
  text: string;
  timestamp: string;
}

export default function Home() {
  const { mode, toggleMode } = useUIMode();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      isAi: true,
      text: "Hello! I'm your forest guide. How can I assist you today?",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const messagesContainerRef = useRef<HTMLDivElement>(null); // Ref for the messages container

  // Effect to scroll down when messages change
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages]); // Run effect when messages array updates

  const handleSend = (message: string) => {
    const newMessage: Message = {
      id: Date.now(), // Use timestamp for potentially more unique ID during rapid sends
      isAi: false,
      text: message,
      timestamp: new Date().toLocaleTimeString(),
    };

    // Use functional update to get the latest state
    setMessages((prev) => [...prev, newMessage]);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: Date.now() + 1, // Use timestamp + offset
        isAi: true,
        text: "I understand your message and I'm here to help. What would you like to know about?",
        timestamp: new Date().toLocaleTimeString(),
      };
      // Use functional update here as well
      setMessages((prev) => [...prev, aiResponse]);
    }, 1000);
  };

  return (
    // Main container takes full screen height
    <div className="flex flex-col h-screen bg-background">
      {/* Header remains fixed at the top */}
      <header className="curved-header flex items-center gap-3 p-6 backdrop-blur shrink-0">
        <div className="shine-effect p-2 rounded-lg bg-background/20">
          <TreePine className="h-6 w-6 p-1 bg-emerald-950" />
        </div>
        <h1 className="text-2xl text-white font-semibold tracking-tight">
          Forest Guide
        </h1>
        <div className="ml-auto">
          <Button
            variant="secondary"
            onClick={toggleMode}
            className="font-spaceGrotesk"
          >
            {mode === "chat" ? "Switch to Transcription" : "Switch to Chat"}
          </Button>
        </div>
      </header>

      {/* Main content area takes remaining height and allows internal scrolling */}
      <div className="flex-1 flex flex-col overflow-hidden p-4">
        {mode === "chat" ? (
          <>
            {/* Scrollable messages container */}
            <div
              ref={messagesContainerRef}
              className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2" // Added space-y and pr for scrollbar padding
            >
              {messages.map((message) => (
                // Removed outer div with mb-4, using space-y on parent now
                <ChatMessage
                  key={message.id} // Key should be on the mapped element
                  isAi={message.isAi}
                  message={message.text}
                  timestamp={message.timestamp}
                />
              ))}
            </div>
            {/* Input area fixed at the bottom of the content area */}
            <div className="shrink-0">
              <ChatInput onSend={handleSend} />
            </div>
          </>
        ) : (
          // Transcription view centered
          <div className="flex-1 flex items-center justify-center">
            <TranscriptionButton />
          </div>
        )}
      </div>
    </div>
  );
}
