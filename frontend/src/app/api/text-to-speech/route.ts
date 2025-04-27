// app/api/text-to-speech/route.ts
import { NextRequest, NextResponse } from "next/server";
import Groq from "groq-sdk";

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
});

export async function POST(req: NextRequest) {
  try {
    const { text } = await req.json();

    if (!text) {
      return NextResponse.json({ error: "No text provided" }, { status: 400 });
    }

    const response = await groq.audio.speech.create({
      model: "playai-tts",
      voice: "Fritz-PlayAI", // You can change this to any voice you prefer
      input: text,
      response_format: "mp3", // Using mp3 for better browser compatibility
    });

    // Get the audio data as an ArrayBuffer
    const arrayBuffer = await response.arrayBuffer();

    // Return the audio data with the appropriate content type
    return new Response(arrayBuffer, {
      headers: {
        "Content-Type": "audio/mpeg",
        "Content-Length": arrayBuffer.byteLength.toString(),
      },
    });
  } catch (error) {
    console.error("Text-to-speech error:", error);
    return NextResponse.json(
      {
        error: `Error generating speech: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
      },
      { status: 500 }
    );
  }
}
