import { createDeck, updateDeck } from "@/apis/endpoints/decks";
import { CText } from "@/components/common/CText";
import { CTextInput } from "@/components/common/CTextInput";
import { Dropdown } from "@/components/common/Dropdown";
import { Modal } from "@/components/common/Modal";
import { COLORS } from "@/constants/colors";
import { useLanguageOptions } from "@/context/LanguageOptionsContext";
import { DeckDetails } from "@/types/decks";
import { useEffect, useState } from "react";
import { View } from "react-native";

interface CreateNewDeckModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode?: "create" | "edit";
  deckToEdit?: DeckDetails;
  onSuccess?: (updatedDeck?: Partial<DeckDetails>) => void;
}

export const CreateNewDeckModal = ({
  isOpen,
  onClose,
  mode = "create",
  deckToEdit,
  onSuccess,
}: CreateNewDeckModalProps) => {
  const [deckName, setDeckName] = useState("");
  const [language, setLanguage] = useState<string | null>(null);
  const [description, setDescription] = useState("");
  const { sourceLanguages, languageNameByCode, error: languageLoadError } =
    useLanguageOptions();

  const [deckNameInputError, setDeckNameInputError] = useState<string>();
  const [languageInputError, setLanguageInputError] = useState<string>();

  const languageOptions = sourceLanguages.map((lang) => lang.name);
  const languageCodeByName = sourceLanguages.reduce(
    (acc, lang) => ({
      ...acc,
      [lang.name]: lang.code,
    }),
    {} as Record<string, string>,
  );

  const isEditMode = mode === "edit";

  const getLanguageName = (code: string) =>
    languageNameByCode[code.toUpperCase()] ?? code.toUpperCase();

  const lockedLanguageLabel = deckToEdit
    ? getLanguageName(deckToEdit.word_lang)
    : "";

  const onCreateDeck = async () => {
    setDeckNameInputError(undefined);
    setLanguageInputError(undefined);

    const isDeckNameEmpty = deckName.trim() === "";

    const selectedLanguageCode = isEditMode
      ? deckToEdit?.word_lang ?? null
      : language
        ? languageCodeByName[language]
        : null;

    if (isDeckNameEmpty || !selectedLanguageCode) {
      if (isDeckNameEmpty) {
        setDeckNameInputError("Deck name cannot be empty");
      }

      if (!selectedLanguageCode) {
        setLanguageInputError("Language must be selected");
      }

      return;
    }

    if (isEditMode && deckToEdit) {
      const { data, error } = await updateDeck(deckToEdit.d_id, {
        deck_name: deckName,
        description,
      });

      if (!error) {
        onSuccess?.(data?.deck);
        onClose();
      } else {
        setDeckNameInputError(error);
      }

      return;
    }

    const { error } = await createDeck({
      deck_name: deckName,
      word_lang: selectedLanguageCode.toLowerCase(),
      trans_lang: "en",
      description: description,
      is_public: false,
    });

    if (!error) {
      onSuccess?.();
      onClose();
    } else {
      setDeckNameInputError(error);
    }
  };

  useEffect(() => {
    if (isOpen && isEditMode && deckToEdit) {
      setDeckName(deckToEdit.deck_name ?? "");
      setDescription(deckToEdit.description ?? "");
      setLanguage(getLanguageName(deckToEdit.word_lang));
      setDeckNameInputError(undefined);
      setLanguageInputError(undefined);
      return;
    }

    if (isOpen && languageLoadError) {
      setLanguageInputError("Failed to load languages");
    }

    if (!isOpen) {
      setDeckName("");
      setLanguage(null);
      setDescription("");
      setDeckNameInputError(undefined);
      setLanguageInputError(undefined);
    }
  }, [isOpen, languageLoadError, isEditMode, deckToEdit, languageNameByCode]);

  return (
    <Modal
      visible={isOpen}
      header={isEditMode ? "Edit Deck" : "Create New Deck"}
      subheader={
        isEditMode
          ? "Update this flashcard deck"
          : "Add a new flashcard deck for language learning"
      }
      onSubmit={onCreateDeck}
      submitLabel={isEditMode ? "Save Changes" : "Create Deck"}
      onClose={onClose}
      closeLabel="Cancel"
    >
      <View style={{ gap: 14, marginBottom: 16 }}>
        <CTextInput
          label="Deck Name *"
          value={deckName}
          onChangeText={setDeckName}
          placeholder="e.g., Spanish Basics"
        />
        {deckNameInputError && (
          <CText variant="inputError">{deckNameInputError}</CText>
        )}
        <View>
          <CText variant="inputLabel">Language *</CText>
          {isEditMode ? (
            <CTextInput
              value={lockedLanguageLabel}
              style={{color: COLORS.text.tertiary}}
              onChangeText={() => {}}
              editable={false}
            />
          ) : (
            <Dropdown
              value={language}
              options={languageOptions}
              onSelect={setLanguage}
              placeholder="Select a language"
            />
          )}
        </View>
        {languageInputError && (
          <CText variant="inputError" style={{ zIndex: -1 }}>
            {languageInputError}
          </CText>
        )}
        <View style={{ zIndex: -1 }}>
          <CTextInput
            label="Description"
            value={description}
            onChangeText={setDescription}
            placeholder="What will you learn in this deck?"
            multiline
            numberOfLines={3}
          />
        </View>
      </View>
    </Modal>
  );
};
