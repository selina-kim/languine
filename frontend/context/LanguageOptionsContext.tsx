import {
  SupportedTranslationLanguagesResponseData,
  getSupportedLanguages,
} from "@/apis/endpoints/translation";
import React, { createContext, useContext, useEffect, useState } from "react";

interface LanguageOptionsContextType {
  sourceLanguages: SupportedTranslationLanguagesResponseData["source"];
  targetLanguages: SupportedTranslationLanguagesResponseData["target"];
  languageNameByCode: Record<string, string>;
  isLoading: boolean;
  error: string | null;
  refreshLanguages: () => Promise<void>;
}

const LanguageOptionsContext = createContext<LanguageOptionsContextType>({
  sourceLanguages: [],
  targetLanguages: [],
  languageNameByCode: {},
  isLoading: true,
  error: null,
  refreshLanguages: async () => {},
});

export const useLanguageOptions = () => useContext(LanguageOptionsContext);

export const LanguageOptionsProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [sourceLanguages, setSourceLanguages] = useState<
    SupportedTranslationLanguagesResponseData["source"]
  >([]);
  const [targetLanguages, setTargetLanguages] = useState<
    SupportedTranslationLanguagesResponseData["target"]
  >([]);
  const [languageNameByCode, setLanguageNameByCode] = useState<
    Record<string, string>
  >({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshLanguages = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const { data, error: apiError } = await getSupportedLanguages();

      if (apiError) {
        setError(apiError);
        return;
      }

      const source = data?.source ?? [];
      const target = data?.target ?? [];
      const allLanguages = [...source, ...target];

      const languageMap = allLanguages.reduce(
        (acc, language) => ({
          ...acc,
          [language.code.toUpperCase()]: language.name,
        }),
        {} as Record<string, string>,
      );

      setSourceLanguages(source);
      setTargetLanguages(target);
      setLanguageNameByCode(languageMap);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshLanguages();
  }, []);

  return (
    <LanguageOptionsContext.Provider
      value={{
        sourceLanguages,
        targetLanguages,
        languageNameByCode,
        isLoading,
        error,
        refreshLanguages,
      }}
    >
      {children}
    </LanguageOptionsContext.Provider>
  );
};
