// Home.tsx
"use client";

import { useRef, useEffect, useState } from "react";
import { TreePine, Send, Mic, Volume2, VolumeX } from "lucide-react";
import ChatMessage from "@/components/ChatMessage";
import TranscriptionButton from "@/components/TranscriptionButton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useUIMode } from "@/contexts/UIModeContext";
import { useChat } from "@ai-sdk/react";

export default function Home() {
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const { mode, toggleMode } = useUIMode();
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Create an audio element ref if it doesn't exist
  useEffect(() => {
    if (!audioRef.current) {
      audioRef.current = new Audio();

      // Add event listeners
      audioRef.current.onplay = () => setIsSpeaking(true);
      audioRef.current.onended = () => setIsSpeaking(false);
      audioRef.current.onpause = () => setIsSpeaking(false);
      audioRef.current.onerror = () => {
        setIsSpeaking(false);
        console.error("Audio playback error");
      };
    }

    return () => {
      // Clean up audio element
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

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
    onFinish: async (message) => {
      console.log("Message finished");

      // Only play text-to-speech if it's enabled and the message is from the assistant
      if (audioEnabled && message.role === "assistant") {
        await playTextToSpeech(message.content);
      }
    },
  });

  // Function to play text-to-speech
  const playTextToSpeech = async (text: string) => {
    if (!text || !audioEnabled) return;

    try {
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }

      // Fetch the audio from our API
      const response = await fetch("/api/text-to-speech", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate speech: ${response.status}`);
      }

      const audioBlob = await response.blob();

      const audioUrl = URL.createObjectURL(audioBlob);

      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        await audioRef.current.play();
      }

      audioRef.current?.addEventListener(
        "ended",
        () => {
          URL.revokeObjectURL(audioUrl);
        },
        { once: true }
      );
    } catch (error) {
      console.error("Error playing text-to-speech:", error);
    }
  };

  // Toggle audio on/off
  const toggleAudio = () => {
    setAudioEnabled(!audioEnabled);

    // Stop any currently playing audio when turning off
    if (audioEnabled && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  };

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
    setInput(transcribedText);
    setIsTranscribing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen backdrop-blur-3xl">
      <header className="curved-header flex items-center gap-3 p-6 backdrop-blur shrink-0">
        <div className="shine-effect p-2 rounded-lg bg-background/20">
          <TreePine className="h-6 w-6 p-1 bg-emerald-950" />
        </div>
        <h1 className="text-2xl text-white font-semibold tracking-tight">
          Forest Guide
        </h1>
        <div className="ml-auto flex items-center gap-2">
          {/* Audio toggle button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleAudio}
            className="rounded-full"
            title={audioEnabled ? "Disable voice" : "Enable voice"}
          >
            {audioEnabled ? (
              <Volume2 className="h-5 w-5" />
            ) : (
              <VolumeX className="h-5 w-5" />
            )}
            <span className="sr-only">
              {audioEnabled ? "Disable voice" : "Enable voice"}
            </span>
          </Button>

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
              {isLoading && messages[messages.length - 1]?.role === "user" && (
                <ChatMessage
                  isAi={true}
                  message="..."
                  timestamp={new Date().toLocaleTimeString()}
                />
              )}
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
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask the forest guide..."
                  className="flex-1 border-none bg-transparent px-3 py-2 outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
                  disabled={isLoading}
                />
                <Button
                  type="button"
                  size="icon"
                  onClick={handleSendMessage}
                  disabled={isLoading || !input.trim()}
                  className="flex-shrink-0 rounded-full"
                >
                  <Send className="h-4 w-4" />
                  <span className="sr-only">Send message</span>
                </Button>
                <TranscriptionButton
                  onTranscriptionComplete={handleTranscriptionComplete}
                  disabled={isLoading}
                  handleSendMessage={handleSendMessage}
                  setInput={setInput}
                />
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <TranscriptionButton
              onTranscriptionComplete={handleTranscriptionComplete}
              disabled={isLoading}
              handleSendMessage={handleSendMessage}
              setInput={setInput}
            />
          </div>
        )}
      </div>
    </div>
  );
}
