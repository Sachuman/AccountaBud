'use server';

import { streamText } from 'ai';
import { google } from '@ai-sdk/google';
import { createStreamableValue } from 'ai/rsc';

export async function generate(input: string) {
  const stream = createStreamableValue('');

  (async () => {
    const { textStream } = streamText({
      model: google('gemini-2.0-flash-001'),
      prompt: input,
    });

    for await (const delta of textStream) {
      stream.update(delta);
    }

    stream.done();
  })();

  return { output: stream.value };
}