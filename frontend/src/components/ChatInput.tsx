"use client";
import React from "react"; // Removed useState
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mic, Send } from "lucide-react";

interface ChatInputProps {
  value: string; // Input value controlled by parent
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void; // Function to update parent state
  onSend: () => void; // Function to trigger sending in parent
  isLoading?: boolean; // Optional loading state from parent
  // onTranscribe?: () => void; // Optional: for future transcription feature
}

const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSend,
  isLoading,
}) => {
  // Removed internal message state: const [message, setMessage] = useState("");

  const handleSendClick = () => {
    // Call the onSend prop if not loading and value is not empty
    if (!isLoading && value.trim()) {
      onSend();
      // No need to setMessage("") here, parent's state update will clear the input via the value prop
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendClick(); // Use the same send logic
    }
  };

  return (
    // Fixed position at bottom center - Consider if this should be part of the parent layout instead
    // If the parent component already handles layout (like putting this at the bottom),
    // you might remove the 'fixed', 'bottom-4', 'left-1/2', '-translate-x-1/2' classes here.
    // For now, keeping it as per your original component.
    <div className="fixed bottom-4 left-1/2 z-50 w-full max-w-md -translate-x-1/2 px-4">
      <div className="flex w-full items-center space-x-2 rounded-full border bg-background p-1 shadow-md">
        <Input
          type="text"
          value={value} // Use the value prop
          onChange={onChange} // Use the onChange prop
          onKeyDown={handleKeyDown}
          placeholder="Ask the forest guide..."
          className="flex-1 border-none bg-transparent px-3 py-2 outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
          disabled={isLoading} // Disable input when loading
        />
        <Button
          type="button" // Changed to button as it's not submitting a form directly here
          size="icon"
          onClick={handleSendClick} // Use the updated handler
          // Disable if loading OR if the input value (trimmed) is empty
          disabled={isLoading || !value.trim()}
          className="flex-shrink-0 rounded-full"
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">Send message</span>
        </Button>
        <Button
          size="icon"
          variant="secondary"
          className="flex-shrink-0 rounded-full"
          disabled={isLoading} // Also disable mic button during loading? Optional.
          // onClick={onTranscribe} // Connect transcription later if needed
        >
          <Mic className="h-4 w-4" />
          <span className="sr-only">Use microphone</span>
        </Button>
      </div>
    </div>
  );
};

export default ChatInput;
