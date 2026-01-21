import { Dropdown } from "@/components/common/Dropdown";
import { InputLabel } from "@/components/common/InputLabel";
import { Modal } from "@/components/common/Modal";
import { TextInput } from "@/components/common/TextInput";
import { useState } from "react";
import { View } from "react-native";

// temporary TODO
const LANGUAGES = [
  "Korean",
  "Japanese",
  "Mandarin",
  "text",
  "text",
  "text",
  "text",
  "text",
  "text",
  "text",
];

interface CreateNewDeckModalProps {
  visible: boolean;
  onClose: () => void;
}

export const CreateNewDeckModal = ({
  visible,
  onClose,
}: CreateNewDeckModalProps) => {
  const [deckName, setDeckName] = useState("");
  const [language, setLanguage] = useState("");
  const [description, setDescription] = useState("");

  const onCreateDeck = () => {
    console.log({ deckName, language, description });
    // TODO: Handle deck creation
    onClose();
  };

  return (
    <Modal
      visible={visible}
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
        <View style={{ zIndex: 10 }}>
          <InputLabel>Language *</InputLabel>
          <Dropdown
            value={language}
            options={LANGUAGES}
            onSelect={setLanguage}
            placeholder="Select a language"
          />
        </View>
        <TextInput
          label="Description"
          value={description}
          onChangeText={setDescription}
          placeholder="What will you learn in this deck?"
          multiline
          numberOfLines={3}
        />
      </View>
    </Modal>
  );
};
