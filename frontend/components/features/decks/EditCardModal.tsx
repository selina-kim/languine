import { updateCard } from "@/apis/endpoints/cards";
import { getWordDefinition } from "@/apis/endpoints/example";
import { searchImages } from "@/apis/endpoints/image";
import { getTranslation } from "@/apis/endpoints/translation";
import { MagicWandIcon } from "@/assets/icons/MagicWandIcon";
import { CButton } from "@/components/common/CButton";
import { CText } from "@/components/common/CText";
import { CTextInput } from "@/components/common/CTextInput";
import { Modal } from "@/components/common/Modal";
import { COLORS } from "@/constants/colors";
import { useLanguageOptions } from "@/context/LanguageOptionsContext";
import { Card } from "@/types/decks";
import { useEffect, useState } from "react";
import { Image, ScrollView, View } from "react-native";

interface EditCardModalProps {
  deckId: string;
  card: Card;
  wordLanguageCode: string;
  translationLanguageCode: string;
  isOpen: boolean;
  onUpdateSuccess: (updatedCard: Card) => void;
  onUpdateFailed: () => void;
  onClose: () => void;
}

export const EditCardModal = ({
  deckId,
  card,
  wordLanguageCode,
  translationLanguageCode,
  isOpen,
  onUpdateSuccess,
  onUpdateFailed,
  onClose,
}: EditCardModalProps) => {
  const [sourceWord, setSourceWord] = useState("");
  const [targetWord, setTargetWord] = useState("");
  const [sourceExample, setSourceExample] = useState("");
  const [targetExample, setTargetExample] = useState("");
  const [isUpdatingCard, setIsUpdatingCard] = useState(false);
  const [isTranslatingWord, setIsTranslatingWord] = useState(false);
  const [isGeneratingExample, setIsGeneratingExample] = useState(false);
  const [image, setImage] = useState<string | null>(null);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const { languageNameByCode } = useLanguageOptions();

  const [wordInputError, setWordInputError] = useState<string>();
  const [exampleError, setExampleError] = useState<string>();
  const [imageError, setImageError] = useState<string>();

  const getLanguageName = (code: string) =>
    languageNameByCode[code.toUpperCase()] ?? code.toUpperCase();

  const sourceLanguageName = getLanguageName(translationLanguageCode);
  const targetLanguageName = getLanguageName(wordLanguageCode);

  const onEditCard = async () => {
    if (isUpdatingCard) {
      return;
    }

    setWordInputError(undefined);

    const isEitherWordEmpty =
      sourceWord.trim() === "" || targetWord.trim() === "";

    if (isEitherWordEmpty) {
      setWordInputError("The word(s) cannot be empty");
      return;
    }

    setIsUpdatingCard(true);

    try {
      const { data, error } = await updateCard(deckId, card.c_id, {
        word: targetWord,
        translation: sourceWord,
        word_example: targetExample,
        trans_example: sourceExample,
        image: image || undefined,
      });

      if (!error) {
        onUpdateSuccess(data.card);
        onClose();
      } else {
        onUpdateFailed();
        setWordInputError(error);
      }
    } catch {
      onUpdateFailed();
      setWordInputError("Failed to update card");
    } finally {
      setIsUpdatingCard(false);
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

  const handleAutoGenerateExample = async () => {
    if (isGeneratingExample) {
      return;
    }

    setExampleError(undefined);

    if (sourceWord.trim() === "") {
      setExampleError("The word(s) cannot be empty");
      return;
    }

    setIsGeneratingExample(true);

    try {
      let nextSourceExample = sourceExample.trim();

      // If source example is empty, fetch one from dictionary.
      if (!nextSourceExample) {
        const { data: dictData, error: dictError } = await getWordDefinition(
          sourceWord.trim(),
        );

        if (dictError) {
          setExampleError(dictError);
          return;
        }

        const firstExample =
          dictData.definitions
            ?.flatMap((definition) => definition.example_sentences ?? [])
            .find((sentence) => sentence?.trim()) ?? "";

        if (!firstExample) {
          setExampleError("No example sentence found for this word");
          return;
        }

        nextSourceExample = firstExample.trim();
        setSourceExample(nextSourceExample);
      }

      const sourceCode = translationLanguageCode.toUpperCase();
      const targetCode = wordLanguageCode.toUpperCase();

      const { data, error } = await getTranslation(
        nextSourceExample,
        targetCode,
        sourceCode,
      );

      if (error) {
        setExampleError(error);
        return;
      }

      setTargetExample(data.translatedText ?? "");
    } finally {
      setIsGeneratingExample(false);
    }
  };

  // Generate image using word as search query
  const handleAutoGenerateImage = async () => {
    if (isGeneratingImage) {
      return;
    }

    setImageError(undefined);

    if (targetWord.trim() === "") {
      setImageError("The word cannot be empty");
      return;
    }

    setIsGeneratingImage(true);

    try {
      const { data, error } = await searchImages(targetWord.trim());

      if (error) {
        setImageError(error);
        return;
      }

      if (data.results && data.results.length > 0) {
        const imageUrl = data.results[0].urls.regular;
        setImage(imageUrl);
      } else {
        setImageError("No images found for this word");
      }
    } finally {
      setIsGeneratingImage(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      // Populate fields with existing card data
      setSourceWord(card.translation || "");
      setTargetWord(card.word || "");
      setSourceExample(card.trans_example || "");
      setTargetExample(card.word_example || "");
      setImage(card.image || null);
      setWordInputError(undefined);
      setExampleError(undefined);
      setImageError(undefined);
      setIsUpdatingCard(false);
      setIsTranslatingWord(false);
      setIsGeneratingExample(false);
      setIsGeneratingImage(false);
    }
  }, [isOpen, card]);

  return (
    <Modal
      visible={isOpen}
      header="Edit Card"
      subheader="Update this flashcard"
      onSubmit={onEditCard}
      submitLabel="Save Changes"
      onClose={onClose}
      closeLabel="Cancel"
      isLoading={isUpdatingCard}
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
          {exampleError && (
            <CText variant="inputError">{exampleError}</CText>
          )}
          <CButton
            variant="primary"
            label={isGeneratingExample ? "Generating..." : "Auto-generate"}
            Icon={<MagicWandIcon />}
            disabled={isGeneratingExample}
            onPress={handleAutoGenerateExample}
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
              overflow: "hidden",
            }}
          >
            {image ? (
              <Image
                key={image}
                source={{ uri: image }}
                style={{ width: "100%", height: "100%" }}
                resizeMode="cover"
              />
            ) : (
              <CText bold style={{ color: COLORS.text.tertiary }}>
                No image
              </CText>
            )}
          </View>
          {imageError && (
            <CText variant="inputError">{imageError}</CText>
          )}
          <CButton
            variant="primary"
            label={isGeneratingImage ? "Generating..." : "Auto-generate"}
            Icon={<MagicWandIcon />}
            disabled={isGeneratingImage}
            onPress={handleAutoGenerateImage}
          />
        </ScrollView>
      </View>
    </Modal>
  );
};
