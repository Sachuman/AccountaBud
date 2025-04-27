// app/api/transcribe-audio/route.ts
import { NextRequest, NextResponse } from "next/server";
import Groq from "groq-sdk";
import fs from "fs";
import path from "path";
import os from "os";

// Initialize the Groq client
const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
  
});

export async function POST(req: NextRequest) {
  // Create a temporary file path
  const tempDir = os.tmpdir();
  const tempFilePath = path.join(tempDir, `audio-test.m4a`);

  try {
    // Get the FormData from the request
    const formData = await req.formData();

    // Extract the audio blob from the FormData
    const audioFile = formData.get("audio");

    if (!audioFile || !(audioFile instanceof Blob)) {
      return NextResponse.json(
        { error: "Invalid audio file in request" },
        { status: 400 }
      );
    }

    // Convert Blob to Buffer
    const arrayBuffer = await audioFile.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // Write the buffer to a temporary file
    fs.writeFileSync(tempFilePath, buffer);

    // Create a translation job using Groq SDK with the file path
    const translation = await groq.audio.translations.create({
      file: fs.createReadStream(tempFilePath),
      model: "whisper-large-v3",
      response_format: "json",
      temperature: 0.0,
    });
    console.log("Translation result:", translation.text)
    // Return the transcribed text
    return NextResponse.json({ text: translation.text });
  } catch (error) {
    console.error("Transcription error:", error);
    return NextResponse.json(
      {
        error: `Error transcribing audio: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
      },
      { status: 500 }
    );
  } finally {
    // Clean up the temporary file
    if (fs.existsSync(tempFilePath)) {
      try {
        fs.unlinkSync(tempFilePath);
      } catch (e) {
        console.error("Error deleting temporary file:", e);
      }
    }
  }
}
