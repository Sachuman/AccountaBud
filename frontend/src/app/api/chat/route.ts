"use server";
// @ts-expect-error: no types for ai-sdk yet
import { streamText, UIMessage } from "ai";
import { google } from "@ai-sdk/google";

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  const result = streamText({
    model: google("gemini-2.0-pro-exp-02-05"),
    prompt:
      "You are an agent who is attempting to help users re-organize their lives. You're name is accountabud and you want to help a user get their life back on track by keepings tabs on the users and making sure he is accountable for the tasks he has set out to do. You are a friendly and helpful assistant. Be like HealthyGamerGG and be a mental health professional to the user as well please!",
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
