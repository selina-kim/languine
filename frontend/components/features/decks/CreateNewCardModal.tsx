import { createCard } from "@/apis/endpoints/cards";
import {
  getSupportedLanguages,
  getTranslation,
} from "@/apis/endpoints/translation";
import { MagicWandIcon } from "@/assets/icons/MagicWandIcon";
import { CButton } from "@/components/common/CButton";
import { CText } from "@/components/common/CText";
import { CTextInput } from "@/components/common/CTextInput";
import { Modal } from "@/components/common/Modal";
import { COLORS } from "@/constants/colors";
import { useEffect, useState } from "react";
import { ScrollView, View } from "react-native";

interface CreateNewCardModalProps {
  deckId: string;
  wordLanguageCode: string;
  translationLanguageCode: string;
  isOpen: boolean;
  onClose: () => void;
}

export const CreateNewCardModal = ({
  deckId,
  wordLanguageCode,
  translationLanguageCode,
  isOpen,
  onClose,
}: CreateNewCardModalProps) => {
  const [sourceWord, setSourceWord] = useState("");
  const [targetWord, setTargetWord] = useState("");
  const [languageNameByCode, setLanguageNameByCode] = useState<
    Record<string, string>
  >({});
  const [sourceExample, setSourceExample] = useState("");
  const [targetExample, setTargetExample] = useState("");
  const [wordInputError, setWordInputError] = useState<string>();
  const [isCreatingCard, setIsCreatingCard] = useState(false);
  const [isTranslatingWord, setIsTranslatingWord] = useState(false);

  const getLanguageName = (code: string) =>
    languageNameByCode[code.toUpperCase()] ?? code.toUpperCase();

  const sourceLanguageName = getLanguageName(translationLanguageCode);
  const targetLanguageName = getLanguageName(wordLanguageCode);

  const onCreateDeck = async () => {
    if (isCreatingCard) {
      return;
    }

    setWordInputError(undefined);

    const isEitherWordEmpty =
      sourceWord.trim() === "" || targetWord.trim() === "";

    if (isEitherWordEmpty) {
      setWordInputError("The word(s) cannot be empty");
      return;
    }

    setIsCreatingCard(true);

    // const start = performance.now();

    try {
      const { error } = await createCard(deckId, {
        word: targetWord,
        translation: sourceWord,
        word_example: targetExample,
        trans_example: sourceExample,
      });

      if (!error) {
        onClose();
      } else {
        setWordInputError(error);
      }
    } finally {
      // const end = performance.now();
      // const elapsedMs = end - start;
      // const elapsedSec = elapsedMs / 1000;
      // console.log(`took ${elapsedSec.toFixed(3)}s (${elapsedMs.toFixed(1)}ms)`);

      setIsCreatingCard(false);
    }
  };

  const handleAutoTranslate = async () => {
    if (isTranslatingWord) {
      return;
    }

    setWordInputError(undefined);

    if (sourceWord.trim() === "") {
      setWordInputError("The word(s) cannot be empty");
      return;
    }

    // DeepL expects uppercase language codes (e.g., EN, KO, JA, ZH).
    const sourceCode = translationLanguageCode.toUpperCase();
    const targetCode = wordLanguageCode.toUpperCase();

    setIsTranslatingWord(true);

    try {
      const { data, error } = await getTranslation(
        sourceWord.trim(),
        targetCode,
        sourceCode,
      );

      if (error) {
        setWordInputError(error);
        return;
      }

      setTargetWord(data.translatedText ?? "");
    } finally {
      setIsTranslatingWord(false);
    }
  };

  // TODO: replace with actual example generation api logic
  const handleAutoGenerateExample = () => {
    console.log("auto-generate example translation");
    if (sourceWord.trim() === "") {
      setWordInputError("The word(s) cannot be empty");
      return;
    }
    setTargetExample("테스트");
  };

  // TODO: replace with actual image generation api logic
  const handleAutoGenerateImage = () => {
    console.log("auto-generate image");
    if (targetWord.trim() === "") {
      setWordInputError("The word(s) cannot be empty");
      return;
    }
  };

  useEffect(() => {
    const loadSupportedLanguages = async () => {
      const { data, error } = await getSupportedLanguages();

      if (error) {
        console.log("error", error);
        return;
      }

      const sourceLanguages = data?.source ?? [];
      const targetLanguages = data?.target ?? [];
      const allLanguages = [...sourceLanguages, ...targetLanguages];

      const languageMap = allLanguages.reduce(
        (acc, language) => ({
          ...acc,
          [language.code.toUpperCase()]: language.name,
        }),
        {} as Record<string, string>,
      );

      setLanguageNameByCode(languageMap);
    };

    if (isOpen && Object.keys(languageNameByCode).length === 0) {
      loadSupportedLanguages();
    }

    if (!isOpen) {
      setSourceWord("");
      setTargetWord("");
      setSourceExample("");
      setTargetExample("");
      setWordInputError(undefined);
      setIsCreatingCard(false);
      setIsTranslatingWord(false);
    }
  }, [isOpen, languageNameByCode]);

  return (
    <Modal
      visible={isOpen}
      header="Add New Card"
      subheader="Create a new flashcard for this deck"
      onSubmit={onCreateDeck}
      submitLabel="Add Card"
      onClose={onClose}
      closeLabel="Cancel"
      isLoading={isCreatingCard}
    >
      <View style={{ height: 600 }}>
        <ScrollView contentContainerStyle={{ gap: 14, paddingBottom: 50 }}>
          <CTextInput
            label="Word"
            sublabel={sourceLanguageName.toUpperCase()}
            value={sourceWord}
            onChangeText={setSourceWord}
            placeholder="e.g., Hello"
          />
          <CTextInput
            sublabel={targetLanguageName.toUpperCase()}
            value={targetWord}
            onChangeText={setTargetWord}
            placeholder="e.g., 안녕하세요"
          />
          {wordInputError && (
            <CText variant="inputError">{wordInputError}</CText>
          )}
          <CButton
            variant="primary"
            label={isTranslatingWord ? "Translating..." : "Auto-translate"}
            Icon={<MagicWandIcon />}
            disabled={isTranslatingWord}
            onPress={handleAutoTranslate}
          />
          <CTextInput
            label="Example"
            sublabel={sourceLanguageName.toUpperCase()}
            value={sourceExample}
            onChangeText={setSourceExample}
            placeholder="e.g., Hello my name is Tinu."
          />
          <CTextInput
            sublabel={targetLanguageName.toUpperCase()}
            value={targetExample}
            onChangeText={setTargetExample}
            placeholder="e.g., 안녕하세요! 제 이름은 티누예요."
          />
          <CButton
            variant="primary"
            label="Auto-generate"
            Icon={<MagicWandIcon />}
            onPress={handleAutoGenerateExample} // TODO
          />
          <CText bold>Image</CText>
          <View
            style={{
              height: 200,
              backgroundColor: COLORS.background.secondary,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              borderRadius: 10,
            }}
          >
            <CText bold style={{ color: COLORS.text.tertiary }}>
              No image generated
            </CText>
          </View>
          <CButton
            variant="primary"
            label="Auto-generate"
            Icon={<MagicWandIcon />}
            onPress={handleAutoGenerateImage} // TODO
          />
        </ScrollView>
      </View>
    </Modal>
  );
};
