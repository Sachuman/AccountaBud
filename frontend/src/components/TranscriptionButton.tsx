// components/TranscriptionButton.tsx
"use client";

import React, { useState, useRef } from "react";
import { Mic, StopCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUIMode } from "@/contexts/UIModeContext";

interface TranscriptionButtonProps {
  onTranscriptionComplete: (text: string) => void;
  disabled?: boolean;
  handleSendMessage?: () => void; // Optional: for future use if needed
  setInput?: (text: string) => void; // Optional: for future use if needed
}

const TranscriptionButton: React.FC<TranscriptionButtonProps> = ({
  onTranscriptionComplete,
  disabled = false,
  handleSendMessage,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioStreamRef = useRef<MediaStream | null>(null);

  const startRecording = async () => {
    if (disabled || isRecording || isLoading) return;

    try {
      // Request microphone access with specific constraints for better audio quality
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100,
        },
      });

      audioStreamRef.current = stream;
      audioChunksRef.current = [];

      // Try to use a format that works well with Groq's Whisper model
      // m4a/mp4 is preferred for Whisper
      let options = {};

      if (MediaRecorder.isTypeSupported("audio/mp4")) {
        options = { mimeType: "audio/mp4" };
      } else if (MediaRecorder.isTypeSupported("audio/webm")) {
        options = { mimeType: "audio/webm" };
      } else if (MediaRecorder.isTypeSupported("audio/ogg")) {
        options = { mimeType: "audio/ogg" };
      }

      mediaRecorderRef.current = new MediaRecorder(stream, options);

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        setIsLoading(true);

        try {
          // Get the correct MIME type from the recorder
          const mimeType = mediaRecorderRef.current?.mimeType || "audio/webm";
          const audioBlob = new Blob(audioChunksRef.current, {
            type: mimeType,
          });

          // Create a filename with the appropriate extension
          const extension =
            mimeType.split("/")[1] === "mp4" ? "m4a" : mimeType.split("/")[1];
          const filename = `recording.${extension}`;

          const formData = new FormData();
          formData.append("audio", audioBlob, filename);

          const response = await fetch("/api/transcribe-audio", {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.status} - ${errorText}`);
          }

          const data = await response.json();
          console.log("Transcription response:", data);

          if (data.text) {
            onTranscriptionComplete(data.text);
            handleSendMessage?.(); // Call this function to send the message after transcription
            setIsLoading(false);
            setIsRecording(false);
          } else {
            throw new Error("No transcription text returned");
          }
        } catch (error) {
          console.error("Transcription failed:", error);
          // You could add UI feedback for errors here
        } finally {
          setIsLoading(false);
          setIsRecording(false);
          // Always clean up the audio stream
          if (audioStreamRef.current) {
            audioStreamRef.current.getTracks().forEach((track) => track.stop());
            audioStreamRef.current = null;
          }
        }
      };

      // Request data at regular intervals for longer recordings
      mediaRecorderRef.current.start(1000);
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      // You could add UI feedback for microphone access errors here
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    setIsLoading(false);
    handleSendMessage?.(); // Call this function to send the message after stopping recording
  };

  const buttonIcon = isLoading ? (
    <Loader2 className="h-4 w-4 animate-spin" />
  ) : isRecording ? (
    <StopCircle className="h-4 w-4" />
  ) : (
    <Mic className="h-4 w-4" />
  );

  const buttonVariant = isRecording ? "destructive" : "secondary";
  const { mode } = useUIMode();

  return (
    <Button
      size="icon"
      variant={buttonVariant}
      className={`flex-shrink-0 rounded-full ${
        mode === "chat"
          ? "w-auto h-auto"
          : "w-24 h-24 transition-all duration-300 hover:scale-105 shine-effect"
      }`}
      onClick={isRecording ? stopRecording : startRecording}
      disabled={disabled || isLoading}
    >
      {buttonIcon}
      <span className="sr-only">
        {isRecording ? "Stop recording" : "Start recording"}
      </span>
    </Button>
  );
};

export default TranscriptionButton;
