import { createDeck } from "@/apis/endpoints/decks";
import { CText } from "@/components/common/CText";
import { CTextInput } from "@/components/common/CTextInput";
import { Dropdown } from "@/components/common/Dropdown";
import { Modal } from "@/components/common/Modal";
import { useEffect, useState } from "react";
import { View } from "react-native";

// temporary TODO
const LANGUAGES = [
  "Korean",
  "Japanese",
  "Mandarin",
  "French",
  "lang1",
  "lang2",
  "lang3",
];

interface CreateNewDeckModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateNewDeckModal = ({
  isOpen,
  onClose,
}: CreateNewDeckModalProps) => {
  const [deckName, setDeckName] = useState("");
  const [language, setLanguage] = useState<string | null>(null);
  const [description, setDescription] = useState("");

  const [deckNameInputError, setDeckNameInputError] = useState<string>();
  const [languageInputError, setLanguageInputError] = useState<string>();

  const onCreateDeck = async () => {
    setDeckNameInputError(undefined);
    setLanguageInputError(undefined);

    const isDeckNameEmpty = deckName.trim() === "";

    if (isDeckNameEmpty || !language) {
      if (isDeckNameEmpty) {
        setDeckNameInputError("Deck name cannot be empty");
      }

      if (!language) {
        setLanguageInputError("Language must be selected");
      }

      return;
    }

    const { error } = await createDeck({
      deck_name: deckName,
      word_lang: language,
      trans_lang: "en",
      description: description,
      is_public: false,
    });

    if (!error) {
      onClose();
    } else {
      setDeckNameInputError(error);
    }
  };

  useEffect(() => {
    if (!isOpen) {
      setDeckName("");
      setLanguage(null);
      setDescription("");
      setDeckNameInputError(undefined);
      setLanguageInputError(undefined);
    }
  }, [isOpen]);

  return (
    <Modal
      visible={isOpen}
      header="Create New Deck"
      subheader="Add a new flashcard deck for language learning"
      onSubmit={onCreateDeck}
      submitLabel="Create Deck"
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
          <Dropdown
            value={language}
            options={LANGUAGES}
            onSelect={setLanguage}
            placeholder="Select a language"
          />
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
