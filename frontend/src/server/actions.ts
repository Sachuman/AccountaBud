"use server";

// import { streamText, UIMessage } from "ai";
// import { google } from "@ai-sdk/google";
// export async function generate(messages: UIMessage[]) {
//   const result = streamText({
//     model: google("gemini-2.0-pro-exp-02-05"),
//     messages,
//   });
//   return result.toDataStreamResponse();
// }

import { experimental_transcribe as transcribe } from 'ai';
import { groq } from '@ai-sdk/groq';
import { readFile } from 'fs/promises';

const result = await transcribe({
  model: groq.transcription('whisper-large-v3'),
  audio: await readFile('audio.mp3'),
  providerOptions: { groq: { language: 'en' } },
});
