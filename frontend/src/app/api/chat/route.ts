"use server";
// @ts-expect-error: no types for ai-sdk yet
import { streamText, UIMessage } from "ai";
import { google } from "@ai-sdk/google";

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  const result = streamText({
    model: google("gemini-2.0-pro-exp-02-05"),
    messages,
  });

  function errorHandler(error: unknown) {
    if (error == null) {
      return "unknown error";
    }

    if (typeof error === "string") {
      return error;
    }

    if (error instanceof Error) {
      return error.message;
    }

    return JSON.stringify(error);
  }

  return result.toDataStreamResponse({
    getErrorMessage: errorHandler,
  });
}
