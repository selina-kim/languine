import { createCard, updateCard } from "@/apis/endpoints/cards";
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
import { getImageUrl } from "@/utils/imageUtils";

interface BaseCardModalProps {
  deckId: string;
  wordLanguageCode: string;
  translationLanguageCode: string;
  isOpen: boolean;
  onClose: () => void;
}

interface CreateCardModalProps extends BaseCardModalProps {
  mode?: "create";
  onOptimisticCreate: (card: Card) => void;
  onCreateSuccess: (tempCardId: number, createdCard: Card) => void;
  onCreateFailed: (tempCardId: number) => void;
}

interface EditCardModalProps extends BaseCardModalProps {
  mode: "edit";
  card: Card;
  onUpdateSuccess: (updatedCard: Card) => void;
  onUpdateFailed: () => void;
}

type CreateNewCardModalProps = CreateCardModalProps | EditCardModalProps;

export const CreateNewCardModal = ({
  deckId,
  wordLanguageCode,
  translationLanguageCode,
  isOpen,
  mode = "create",
  onClose,
  ...modeProps
}: CreateNewCardModalProps) => {
  const isEditMode = mode === "edit";
  const editCard = isEditMode
    ? (modeProps as EditCardModalProps).card
    : undefined;
  const [sourceWord, setSourceWord] = useState("");
  const [targetWord, setTargetWord] = useState("");
  const [sourceExample, setSourceExample] = useState("");
  const [targetExample, setTargetExample] = useState("");
  const [isSavingCard, setIsSavingCard] = useState(false);
  const [isTranslatingWord, setIsTranslatingWord] = useState(false);
  const [isGeneratingExample, setIsGeneratingExample] = useState(false);
  const [image, setImage] = useState<string | null>(null);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const { getLanguageName } = useLanguageOptions();

  const [wordInputError, setWordInputError] = useState<string>();
  const [exampleError, setExampleError] = useState<string>();
  const [imageError, setImageError] = useState<string>();

  const sourceLanguageName = getLanguageName(translationLanguageCode);
  const targetLanguageName = getLanguageName(wordLanguageCode);

  const onSubmitCard = async () => {
    if (isSavingCard) {
      return;
    }

    setWordInputError(undefined);

    const isEitherWordEmpty =
      sourceWord.trim() === "" || targetWord.trim() === "";

    if (isEitherWordEmpty) {
      setWordInputError("The word(s) cannot be empty");
      return;
    }

    if (isEditMode) {
      setIsSavingCard(true);

      try {
        const { data, error } = await updateCard(
          deckId,
          (modeProps as EditCardModalProps).card.c_id,
          {
            word: targetWord,
            translation: sourceWord,
            word_example: targetExample,
            trans_example: sourceExample,
            image: image || undefined,
          },
        );

        if (!error) {
          (modeProps as EditCardModalProps).onUpdateSuccess(data.card);
          onClose();
        } else {
          (modeProps as EditCardModalProps).onUpdateFailed();
          setWordInputError(error);
        }
      } catch {
        (modeProps as EditCardModalProps).onUpdateFailed();
        setWordInputError("Failed to update card");
      } finally {
        setIsSavingCard(false);
      }

      return;
    }

    const tempCardId = -Date.now();
    const optimisticCard: Card = {
      c_id: tempCardId,
      word: targetWord,
      translation: sourceWord,
      word_example: targetExample || null,
      trans_example: sourceExample || null,
      word_roman: null,
      trans_roman: null,
      image: image || null,
      learning_state: 0,
      difficulty: 0,
      stability: 0,
      due_date: null,
    };

    (modeProps as CreateCardModalProps).onOptimisticCreate(optimisticCard);
    onClose();

    setIsSavingCard(true);

    try {
      const { data, error } = await createCard(deckId, {
        word: targetWord,
        translation: sourceWord,
        word_example: targetExample,
        trans_example: sourceExample,
        image: image || undefined,
      });

      if (!error) {
        (modeProps as CreateCardModalProps).onCreateSuccess(
          tempCardId,
          data.card,
        );
      } else {
        (modeProps as CreateCardModalProps).onCreateFailed(tempCardId);
        setWordInputError(error);
      }
    } catch {
      (modeProps as CreateCardModalProps).onCreateFailed(tempCardId);
      setWordInputError("Failed to create card");
    } finally {
      setIsSavingCard(false);
    }
  };

  const handleAutoTranslate = async () => {
    if (isTranslatingWord) {
      return;
    }

    setWordInputError(undefined);

    if (sourceWord.trim() === "" && targetWord.trim() === "") {
      setWordInputError("The word(s) cannot be empty");
      return;
    }

    setIsTranslatingWord(true);

    try {
      const hasSourceWord = sourceWord.trim() !== "";

      if (hasSourceWord) {
        const { data, error } = await getTranslation(
          sourceWord.trim(),
          wordLanguageCode.toUpperCase(),
          translationLanguageCode.toUpperCase(),
        );

        if (error) {
          setWordInputError(error);
          return;
        }

        setTargetWord(data.translatedText ?? "");
        return;
      }

      const { data, error } = await getTranslation(
        targetWord.trim(),
        translationLanguageCode.toUpperCase(),
        wordLanguageCode.toUpperCase(),
      );

      if (error) {
        setWordInputError(error);
        return;
      }

      setSourceWord(data.translatedText ?? "");
    } catch {
      setWordInputError("Failed to translate word");
    } finally {
      setIsTranslatingWord(false);
    }
  };

  const handleAutoGenerateExample = async () => {
    if (isGeneratingExample) {
      return;
    }

    setExampleError(undefined);

    setIsGeneratingExample(true);

    try {
      if (sourceExample.trim()) {
        const { data, error } = await getTranslation(
          sourceExample.trim(),
          wordLanguageCode.toUpperCase(),
          translationLanguageCode.toUpperCase(),
        );

        if (error) {
          setExampleError(error);
          return;
        }

        setTargetExample(data.translatedText ?? "");
        return;
      }

      if (targetExample.trim()) {
        const { data, error } = await getTranslation(
          targetExample.trim(),
          translationLanguageCode.toUpperCase(),
          wordLanguageCode.toUpperCase(),
        );

        if (error) {
          setExampleError(error);
          return;
        }

        setSourceExample(data.translatedText ?? "");
        return;
      }

      if (sourceWord.trim() === "") {
        setExampleError("The word(s) cannot be empty");
        return;
      }

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
    } catch {
      setExampleError("Failed to generate example");
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

    const imageQuery = targetWord.trim() || sourceWord.trim();

    if (imageQuery === "") {
      setImageError("The word(s) cannot be empty");
      return;
    }

    setIsGeneratingImage(true);

    try {
      const { data, error } = await searchImages(imageQuery);

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
    if (isOpen && isEditMode && editCard) {
      setSourceWord(editCard.translation || "");
      setTargetWord(editCard.word || "");
      setSourceExample(editCard.trans_example || "");
      setTargetExample(editCard.word_example || "");
      setImage(editCard.image || null);
      setWordInputError(undefined);
      setExampleError(undefined);
      setImageError(undefined);
      setIsSavingCard(false);
      setIsTranslatingWord(false);
      setIsGeneratingExample(false);
      setIsGeneratingImage(false);
      return;
    }

    if (!isOpen) {
      setSourceWord("");
      setTargetWord("");
      setSourceExample("");
      setTargetExample("");
      setImage(null);
      setWordInputError(undefined);
      setExampleError(undefined);
      setImageError(undefined);
      setIsSavingCard(false);
      setIsTranslatingWord(false);
      setIsGeneratingExample(false);
      setIsGeneratingImage(false);
    }
  }, [isOpen, isEditMode, editCard]);

  return (
    <Modal
      visible={isOpen}
      header={isEditMode ? "Edit Card" : "Add New Card"}
      subheader={
        isEditMode
          ? "Update this flashcard"
          : "Create a new flashcard for this deck"
      }
      onSubmit={onSubmitCard}
      submitLabel={isEditMode ? "Save Changes" : "Add Card"}
      onClose={onClose}
      closeLabel="Cancel"
      isLoading={isSavingCard}
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
          {exampleError && <CText variant="inputError">{exampleError}</CText>}
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
              width: "100%",
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
                source={{ uri: getImageUrl(image) ?? image }}
                style={{ width: "100%", height: "100%" }}
                resizeMode="cover"
              />
            ) : (
              <CText bold style={{ color: COLORS.text.tertiary }}>
                No image
              </CText>
            )}
          </View>
          {imageError && <CText variant="inputError">{imageError}</CText>}
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
