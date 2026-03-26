import { CButton } from "@/components/common/CButton";
import { Modal } from "@/components/common/Modal";

interface CreateOrImportDeckModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateDeck: () => void;
  onImportDeck: () => void;
}

export const CreateOrImportDeckModal = ({
  isOpen,
  onClose,
  onCreateDeck,
  onImportDeck,
}: CreateOrImportDeckModalProps) => {
  return (
    <Modal
      visible={isOpen}
      header="Create or Import New Deck"
      subheader="Add a new flashcard deck for language learning"
      onClose={onClose}
      closeLabel="Cancel"
    >
      <CButton
        variant="primary"
        label="Create New Deck"
        onPress={onCreateDeck}
        style={{ marginBottom: 10, marginTop: 10 }}
      />
      <CButton
        variant="primary"
        label="Import Existing Deck"
        onPress={onImportDeck}
        style={{ marginBottom: 10 }}
      />
    </Modal>
  );
};
