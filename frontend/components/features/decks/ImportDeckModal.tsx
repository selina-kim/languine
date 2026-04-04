import { importDeck } from "@/apis/endpoints/decks";
import { UploadIcon } from "@/assets/icons/UploadIcon";
import { CText } from "@/components/common/CText";
import { Modal } from "@/components/common/Modal";
import { COLORS } from "@/constants/colors";
import * as DocumentPicker from "expo-document-picker";
import { useEffect, useState } from "react";
import { Pressable, View } from "react-native";

type ImportFormat = "json" | "csv" | "anki";

interface ImportDeckModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ImportDeckModal = ({
  isOpen,
  onClose,
  onSuccess,
}: ImportDeckModalProps) => {
  const [format, setFormat] = useState<ImportFormat | null>(null);
  const [file, setFile] = useState<DocumentPicker.DocumentPickerAsset | null>(
    null,
  );
  const [isImporting, setIsImporting] = useState(false);

  const [fileError, setFileError] = useState<string>();

  const resetState = () => {
    setFormat(null);
    setFile(null);
    setFileError(undefined);
  };

  const autoDetectFormat = (
    filename: string | null | undefined,
  ): ImportFormat | null => {
    if (!filename) {
      return null;
    }

    const lower = filename.toLowerCase();

    if (lower.endsWith(".json")) return "json";
    if (lower.endsWith(".csv")) return "csv";
    if (lower.endsWith(".txt")) return "anki";

    return null;
  };

  const handlePickFile = async () => {
    setFileError(undefined);

    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["application/json", "text/csv", "text/plain", "*/*"],
        copyToCacheDirectory: true,
      });

      // Support both new ({ canceled, assets }) and legacy
      // ({ type: 'success' | 'cancel', uri, name, mimeType })
      let asset: DocumentPicker.DocumentPickerAsset | null = null;

      const anyResult = result as any;

      if ("canceled" in anyResult) {
        if (
          anyResult.canceled ||
          !anyResult.assets ||
          anyResult.assets.length === 0
        ) {
          return;
        }
        asset = anyResult.assets[0];
      } else if ("type" in anyResult) {
        if (anyResult.type !== "success") {
          return;
        }

        asset = {
          uri: anyResult.uri,
          name: anyResult.name,
          mimeType: anyResult.mimeType,
          size: anyResult.size,
        } as DocumentPicker.DocumentPickerAsset;
      }

      if (!asset) {
        return;
      }

      const detectedFormat = autoDetectFormat(asset.name);

      if (!detectedFormat) {
        setFormat(null);
        setFile(null);
        setFileError(
          "Unsupported file type. Please upload a JSON, CSV, or Anki (.txt) file.",
        );
        return;
      }

      setFile(asset);
      setFormat(detectedFormat);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to pick file. Please try again.";
      setFileError(message);
    }
  };

  const validateInputs = () => {
    setFileError(undefined);

    let hasError = false;

    if (!file) {
      setFileError("Please select a file to import");
      hasError = true;
    }

    const effectiveFormat = format ?? autoDetectFormat(file?.name) ?? null;

    if (!effectiveFormat) {
      setFileError(
        "Unsupported file type. Please upload a JSON, CSV, or Anki (.txt) file.",
      );
      hasError = true;
    }

    return { hasError, effectiveFormat };
  };

  const buildFormData = (effectiveFormat: ImportFormat): FormData | null => {
    if (!file) {
      return null;
    }

    const formData = new FormData();

    formData.append("file", {
      uri: file.uri,
      name: file.name ?? "deck",
      type: file.mimeType ?? "application/octet-stream",
    } as any);

    formData.append("format", effectiveFormat);

    return formData;
  };

  const handleImportDeck = async () => {
    const { hasError, effectiveFormat } = validateInputs();

    if (hasError || !effectiveFormat) {
      return;
    }

    const formData = buildFormData(effectiveFormat);

    if (!formData) {
      setFileError("Failed to prepare file for upload");
      return;
    }

    setIsImporting(true);

    try {
      const { error } = await importDeck(formData);

      if (error) {
        setFileError(error);
        return;
      }

      onSuccess?.();
      resetState();
      onClose();
    } finally {
      setIsImporting(false);
    }
  };

  useEffect(() => {
    if (!isOpen) {
      resetState();
    }
  }, [isOpen]);

  return (
    <Modal
      visible={isOpen}
      header="Import Existing Deck"
      subheader="Import a flashcard deck for language learning"
      onSubmit={handleImportDeck}
      submitLabel="Import Deck"
      onClose={() => {
        resetState();
        onClose();
      }}
      closeLabel="Cancel"
      isLoading={isImporting}
    >
      <View style={{ marginBottom: 16 }}>
        <CText bold>Upload File *</CText>
        <Pressable
          onPress={handlePickFile}
          style={{
            display: "flex",
            flexDirection: "column",
            backgroundColor: COLORS.background.secondary,
            borderRadius: 12,
            justifyContent: "center",
            alignItems: "center",
            paddingVertical: 24,
            marginVertical: 12,
          }}
        >
          {file ? (
            <CText
              bold
              numberOfLines={1}
              ellipsizeMode="tail"
              style={{ color: COLORS.text.primary, maxWidth: "90%" }}
            >
              {file.name}
            </CText>
          ) : (
            <>
              <View
                style={{
                  height: 64,
                  width: 64,
                }}
              >
                <UploadIcon />
              </View>
              <CText bold style={{ color: COLORS.text.secondary }}>
                Browse Files
              </CText>
            </>
          )}
        </Pressable>
        {fileError && <CText variant="inputError">{fileError}</CText>}
      </View>
    </Modal>
  );
};
