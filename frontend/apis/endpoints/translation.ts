import client from "../client";

export interface TranslationResponseData {
  detectedSourceLang: string | null;
  translatedText: string;
}

export interface TranslationLanguageOption {
  code: string;
  name: string;
}

export interface SupportedTranslationLanguagesResponseData {
  source: TranslationLanguageOption[];
  target: TranslationLanguageOption[];
}

export const getTranslation = (
  text: string,
  targetLang: string,
  sourceLang?: string,
): Promise<{ data: TranslationResponseData; error: string | null }> => {
  const params = new URLSearchParams({
    text,
    target: targetLang,
  });

  if (sourceLang) {
    params.append("source", sourceLang);
  }

  return client.get(`/translate?${params.toString()}`);
};

export const getSupportedLanguages = (): Promise<{
  data: SupportedTranslationLanguagesResponseData;
  error: string | null;
}> => client.get(`/translate/languages`);

export default { getTranslation, getSupportedLanguages };
