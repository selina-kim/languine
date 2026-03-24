import { EditIcon } from "@/assets/icons/EditIcon";
import { CSwitch } from "@/components/common/CSwitch";
import { CText } from "@/components/common/CText";
import { CTextInput } from "@/components/common/CTextInput";
import { Modal } from "@/components/common/Modal";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { ReactNode, useState } from "react";
import { Pressable, View } from "react-native";

interface SettingGroupItemProps {
  label: string;
  value: string | boolean;
  description?: string;
  visible?: boolean;
  inputError?: string;
  onSave?: (value: string) => boolean;
  onToggle?: (value: boolean) => void;
  isLast?: boolean;
}

const SettingGroupItem = ({
  label,
  value,
  description,
  visible = true,
  onSave,
  onToggle,
  inputError,
  isLast = false,
}: SettingGroupItemProps) => {
  const currentValue = typeof value === "string" ? value : "";
  const [newValue, setNewValue] = useState(currentValue);
  const [isEditing, setIsEditing] = useState(false);

  const isEditable = typeof value !== "boolean";

  const onEdit = () => {
    setIsEditing(true);
  };

  const handleSubmit = () => {
    const saved = onSave?.(newValue);
    if (saved) {
      setIsEditing(false);
    }
  };

  const handleClose = () => {
    setNewValue(currentValue);
    setIsEditing(false);
  };

  if (visible) {
    return (
      <>
        <View
          style={{
            display: "flex",
            borderBottomWidth: isLast ? 0 : 2,
            borderBottomColor: COLORS.accent.primary,
            flexDirection: "row",
            justifyContent: "space-between",
            alignItems: "center",
            paddingVertical: 15,
          }}
        >
          <View>
            <CText bold>{label}</CText>
            {isEditable && (
              <CText style={{ color: COLORS.text.secondary }}>{value}</CText>
            )}
          </View>
          {onSave && (
            <Pressable
              onPress={onEdit}
              style={{ width: 25, height: 25, alignItems: "center" }}
            >
              <EditIcon />
            </Pressable>
          )}
          {!isEditable && onToggle && (
            <CSwitch value={value} onChange={onToggle} />
          )}
        </View>
        {isEditable && (
          <Modal
            visible={isEditing}
            header={label}
            subheader={description}
            submitLabel="Save"
            onSubmit={handleSubmit}
            onClose={handleClose}
          >
            <CTextInput
              value={newValue}
              onChangeText={(value) => {
                setNewValue(value);
              }}
              variant="editModal"
              style={{ marginTop: 10, marginBottom: 20 }}
            />
            {inputError && (
              <CText variant="inputError" style={{ marginBottom: 20 }}>
                {inputError}
              </CText>
            )}
          </Modal>
        )}
      </>
    );
  } else {
    return <></>;
  }
};

interface SettingGroupComponent {
  ({ children }: { children?: ReactNode }): React.JSX.Element;
  Item: ({
    label,
    value,
    onSave,
    isLast,
  }: SettingGroupItemProps) => React.JSX.Element;
}

export const SettingGroup: SettingGroupComponent = ({ children }) => {
  return (
    <View
      style={{
        width: "100%",
        borderWidth: 3,
        borderColor: COLORS.icon.outlineSecondary,
        borderRadius: 16,
        backgroundColor: COLORS.background.primary,
        paddingHorizontal: 25,
        ...SHADOWS.default,
      }}
    >
      {children}
    </View>
  );
};

SettingGroup.Item = SettingGroupItem;
