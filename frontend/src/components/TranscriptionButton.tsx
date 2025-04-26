// components/TranscriptionButton.tsx
"use client"; // Ensure this is present for client-side features

import React, { useState, useRef } from 'react';
import { Mic, StopCircle, Loader2 } from 'lucide-react'; // Import StopCircle and Loader2
import { Button } from '@/components/ui/button';
import { useUIMode } from '@/contexts/UIModeContext';

interface TranscriptionButtonProps {
  onTranscriptionComplete: (text: string) => void; // Add a prop to receive the transcribed text
  disabled?: boolean; // Keep the disabled prop
}

const TranscriptionButton: React.FC<TranscriptionButtonProps> = ({
  onTranscriptionComplete,
  disabled = false,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false); // State for loading indicator while transcribing
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioStreamRef = useRef<MediaStream | null>(null); // Ref to store the audio stream

  const startRecording = async () => {
    if (disabled || isRecording || isLoading) return; // Prevent starting if disabled, already recording, or loading

    try {
      // Request access to the user's microphone
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream; // Store the stream

      // Create a MediaRecorder instance
      mediaRecorderRef.current = new MediaRecorder(stream);

      // Array to store audio data chunks
      audioChunksRef.current = [];

      // Event listener for when audio data is available
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      // Event listener for when recording stops
      mediaRecorderRef.current.onstop = async () => {
        setIsLoading(true); // Set loading state while transcribing
        setIsRecording(false); // Recording has stopped

        // Combine the audio chunks into a single Blob
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' }); // Use 'audio/wav' or the appropriate type

        const formData = new FormData();
        // Append the audio blob to the form data. 'audio' is the field name expected by the API route.
        formData.append('audio', audioBlob, 'recording.wav');

        try {
          // Send the audio data to your API route for transcription
          const response = await fetch('/api/transcribe-audio', {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            const errorText = await response.text(); // Get error details from the response
            throw new Error(`API error: ${response.status} - ${errorText}`);
          }

          // Parse the JSON response to get the transcribed text
          const data = await response.json();
          console.log("Transcription response:", data); // Log the response

          // Call the callback function with the transcribed text
          onTranscriptionComplete(data.text);

        } catch (error) {
          console.error('Transcription failed:', error);
          // TODO: Handle error in the UI (e.g., show an error message to the user)
        } finally {
          setIsLoading(false); // Clear loading state
          // Stop all tracks in the audio stream to release the microphone
          if (audioStreamRef.current) {
              audioStreamRef.current.getTracks().forEach(track => track.stop());
          }
        }
      };

      // Start recording
      mediaRecorderRef.current.start();
      setIsRecording(true);

    } catch (error) {
      console.error('Error accessing microphone:', error);
      // TODO: Handle error in the UI (e.g., show a message asking for microphone permission)
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      // The onstop event handler will manage the rest (setting loading, sending data)
    }
  };

  // Determine the icon and variant based on the state
  const buttonIcon = isLoading ? (
    <Loader2 className="h-4 w-4 animate-spin" />
  ) : isRecording ? (
    <StopCircle className="h-4 w-4" />
  ) : (
    <Mic className="h-4 w-4" />
  );

  const buttonVariant = isRecording ? "destructive" : "secondary";
  const { mode } = useUIMode(); // Get the current UI mode (chat or transcription)
  // Adjust button size based on mode
  return (
    <Button
      size="icon"
      variant={buttonVariant}
      className={`flex-shrink-0 rounded-full ${mode === "chat" ? "w-auto h-auto" : "w-24 h-24 transition-all duration-300 hover:scale-105 shine-effect"}`}
      onClick={isRecording ? stopRecording : startRecording}
      disabled={disabled || isLoading} // Disable button while loading or if explicitly disabled
    >
      {buttonIcon}
      {/* The text inside the Mic icon's class in your original component is not needed here */}
      <span className="sr-only">{isRecording ? "Stop recording" : "Start recording"}</span>
    </Button>
  );
};

export default TranscriptionButton;
