export type BasicLanguageCode = "EN" | "KO" | "JA" | "ZH" | "FR";

interface ExamplePlaceholders {
  word: string;
  translation: string;
  exampleSource: string;
  exampleTarget: string;
}

export const BASIC_LANGUAGE_PLACEHOLDERS: Record<
  BasicLanguageCode,
  ExamplePlaceholders
> = {
  EN: {
    word: "e.g., Hello",
    translation: "e.g., Hello",
    exampleSource: "e.g., Hello my name is Tinu.",
    exampleTarget: "e.g., Hello my name is Tinu.",
  },
  KO: {
    word: "e.g., Hello",
    translation: "e.g., 안녕하세요",
    exampleSource: "e.g., Hello my name is Tinu.",
    exampleTarget: "e.g., 안녕하세요! 제 이름은 티누예요.",
  },
  JA: {
    word: "e.g., Hello",
    translation: "e.g., こんにちは",
    exampleSource: "e.g., Hello my name is Tinu.",
    exampleTarget: "e.g., こんにちは、ティヌと申します。",
  },
  ZH: {
    word: "e.g., Hello",
    translation: "e.g., 你好",
    exampleSource: "e.g., Hello my name is Tinu.",
    exampleTarget: "e.g., 你好，我叫蒂努。",
  },
  FR: {
    word: "e.g., Hello",
    translation: "e.g., Bonjour",
    exampleSource: "e.g., Hello my name is Tinu.",
    exampleTarget: "e.g., Bonjour, je m'appelle Tinu.",
  },
};

export const getPlaceholdersForLanguages = (
  sourceLanguageCode: string,
  targetLanguageCode: string,
): {
  wordPlaceholder: string;
  translationPlaceholder: string;
  exampleSourcePlaceholder: string;
  exampleTargetPlaceholder: string;
} => {
  const sourceCode = sourceLanguageCode
    .toUpperCase()
    .split("-")[0] as BasicLanguageCode;
  const targetCode = targetLanguageCode
    .toUpperCase()
    .split("-")[0] as BasicLanguageCode;

  const sourceDefaults =
    BASIC_LANGUAGE_PLACEHOLDERS.EN ?? BASIC_LANGUAGE_PLACEHOLDERS.KO;

  const source = BASIC_LANGUAGE_PLACEHOLDERS[sourceCode] ?? sourceDefaults;
  const target = BASIC_LANGUAGE_PLACEHOLDERS[targetCode] ?? sourceDefaults;

  return {
    wordPlaceholder: source.word,
    translationPlaceholder: target.translation,
    exampleSourcePlaceholder: source.exampleSource,
    exampleTargetPlaceholder: target.exampleTarget,
  };
};
