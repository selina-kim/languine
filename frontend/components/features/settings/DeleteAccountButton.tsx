import { CButton } from "@/components/common/CButton";
import { Modal } from "@/components/common/Modal";
import { useState } from "react";
import { deleteCurrentUser } from "@/apis/endpoints/users";
import { Alert } from "react-native";
import { useAuth } from "@/context/AuthContext";

export const DeleteAccountButton = () => {
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);
  const { signOut } = useAuth();

  const handleConfirm = () => {
    void deleteCurrentUser().then(({ error }) => {
      if (error) {
        Alert.alert("Delete failed", error);
        return;
      }

      Alert.alert("Account deleted", "Your account has been removed.");
      setIsDeleteModalVisible(false);
      void signOut();
    });
  };

  return (
    <>
      <CButton
        variant="criticalPrimary"
        label="Delete Account"
        onPress={() => setIsDeleteModalVisible(true)}
        style={{
          marginTop: 40,
          marginBottom: 20,
        }}
      />
      <Modal
        visible={isDeleteModalVisible}
        header="Are you sure?"
        submitLabel="Delete Account"
        subheader="This action will permanently delete your account and all associated data"
        submitVariant="criticalPrimary"
        closeLabel="Cancel"
        onClose={() => setIsDeleteModalVisible(false)}
        onSubmit={handleConfirm}
      />
    </>
  );
};
