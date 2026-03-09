import { createDeck } from "@/apis/endpoints/decks";
import { CText } from "@/components/common/CText";
import { Dropdown } from "@/components/common/Dropdown";
import { Modal } from "@/components/common/Modal";
import { TextInput } from "@/components/common/TextInput";
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

  const onCreateDeck = () => {
    createDeck({
      deck_name: "Frontend test deck",
      word_lang: "ja",
      trans_lang: "en",
      description: "Basic phrases",
      is_public: false,
    });
    // TODO: Handle deck creation
    onClose();
  };

  useEffect(() => {
    if (!isOpen) {
      setDeckName("");
      setLanguage(null);
      setDescription("");
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
        <TextInput
          label="Deck Name *"
          value={deckName}
          onChangeText={setDeckName}
          placeholder="e.g., Spanish Basics"
        />
        <View>
          <CText variant="inputLabel">Language *</CText>
          <Dropdown
            value={language}
            options={LANGUAGES}
            onSelect={setLanguage}
            placeholder="Select a language"
          />
        </View>
        <View style={{ zIndex: -1 }}>
          <TextInput
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
