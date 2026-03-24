import client from "../client";

export interface DictionaryDefinition {
  definition: string;
  example_sentences: string[];
}

export interface DictionaryEntryResponseData {
  word: string;
  definitions: DictionaryDefinition[];
  pronunciation: string | null;
  audio_url: string | null;
  suggestions?: string[];
}

export const getWordDefinition = (
  word: string,
): Promise<{ data: DictionaryEntryResponseData; error: string | null }> =>
  client.get(`/define/${encodeURIComponent(word)}`);

export default { getWordDefinition };
