// app/api/transcribe-audio/route.ts
import { experimental_transcribe as generateTranscription } from "ai";
import { createGroq } from "@ai-sdk/groq";

const groq = createGroq({ apiKey: process.env.GROQ_API_KEY });

export async function POST(req: Request) {
  if (!req.body) {
    return new Response("No audio data provided", { status: 400 });
  }

  // Assuming the client sends the audio data as a Blob or File in the request body
  const audioFile = await req.blob(); // Or req.file() if using a library that handles multipart forms

  try {
    const { text } = await generateTranscription({
      model: groq.transcription("whisper-large-v3"),
      file: audioFile,
      // Optional: specify language, e.g., language: 'en'
    });

    // Return the transcribed text
    return new Response(JSON.stringify({ text }), {
      headers: {
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    console.error("Transcription error:", error);
    return new Response("Error transcribing audio", { status: 500 });
  }
}
