"use client";

import { useRef, useEffect, useState } from "react";
import { TreePine, Send, Mic } from "lucide-react";
import ChatMessage from "@/components/ChatMessage";
import TranscriptionButton from "@/components/TranscriptionButton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useUIMode } from "@/contexts/UIModeContext";
import { useChat } from "@ai-sdk/react";

export default function Home() {
  const [isTranscribing, setIsTranscribing] = useState(false);
  const { mode, toggleMode } = useUIMode();
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const { messages, input, setInput, append, isLoading, error } = useChat({
    api: "/api/chat",
    initialMessages: [
      {
        id: "initial-ai-message",
        role: "assistant",
        content: "Hello! I'm your forest guide. How can I assist you today?",
      },
    ],
    onError: (err) => {
      console.log("Chat error:", err);
    },
    onFinish: () => {
      console.log("Message finished");
      console.log("Messages:", messages);
    },
  });

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages]);

  const handleSendMessage = () => {
    if (!input.trim() || isLoading) return; // Prevent sending empty or while loading
    append({
      role: "user",
      content: input,
    });
  };

  const handleTranscriptionComplete = (transcribedText: string) => {
    setInput(transcribedText); // Set the transcribed text into the input
    setIsTranscribing(false); // Clear the transcribing state

  };
  const handleTranscriptionButtonClick = () => {
    setIsTranscribing((prev) => !prev); 
  };

  // Handler for key down events on the input
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // Prevent default newline behavior
      handleSendMessage(); // Trigger send message action
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background">
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

      <div className="flex-1 flex flex-col overflow-hidden p-4 pb-24">
        {mode === "chat" ? (
          <>
            <div
              ref={messagesContainerRef}
              className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2"
            >
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  isAi={message.role === "assistant"}
                  message={message.content}
                  timestamp={new Date().toLocaleTimeString()} // Placeholder
                />
              ))}
              {isLoading &&
                messages[messages.length - 1]?.role === "user" && ( // Show loading only if last message was user
                  <ChatMessage
                    isAi={true}
                    message="..."
                    timestamp={new Date().toLocaleTimeString()}
                  />
                )}
              {/* Error message */}
              {error && (
                <div className="text-red-500 text-center p-2">
                  Error: {error.message}
                </div>
              )}
            </div>

            <div className="fixed bottom-4 left-1/2 z-50 w-full max-w-md -translate-x-1/2 px-4">
              <div className="flex w-full items-center space-x-2 rounded-full border bg-background p-1 shadow-md">
                <Input
                  type="text"
                  value={input} // Use input state from useChat
                  onChange={(e) => setInput(e.target.value)} // Use setInput from useChat
                  onKeyDown={handleKeyDown} // Use the keydown handler
                  placeholder="Ask the forest guide..."
                  className="flex-1 border-none bg-transparent px-3 py-2 outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
                  disabled={isLoading} // Disable when loading
                />
                <Button
                  type="button"
                  size="icon"
                  onClick={handleSendMessage} // Use the send handler
                  disabled={isLoading || !input.trim()} // Disable when loading or input empty
                  className="flex-shrink-0 rounded-full"
                >
                  <Send className="h-4 w-4" />
                  <span className="sr-only">Send message</span>
                </Button>
                <Button
                  size="icon"
                  variant="secondary"
                  className="flex-shrink-0 rounded-full"
                  disabled={isLoading} // Disable mic when loading
                >
                  <Mic className="h-4 w-4" />
                  <span className="sr-only">Use microphone</span>
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <TranscriptionButton
              onTranscriptionComplete={handleTranscriptionComplete}
              disabled={isLoading} // Disable transcription button if the chat is loading
            />
          </div>
        )}
      </div>
    </div>
  );
}
