import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { View } from "react-native";

interface TipItem {
  title: string;
  description: string;
}

interface TipsContainerProps {
  heading?: string;
  tips: TipItem[];
}

export const TipsContainer = ({
  heading = "Tips for Effective Learning",
  tips,
}: TipsContainerProps) => {
  return (
    <View style={{ width: "100%" }}>
      <View
        style={{
          rowGap: 10,
          paddingBottom: 30,
          paddingVertical: 10,
          paddingHorizontal: 25,
        }}
      >
        <View
          style={{
            padding: 25,
            borderWidth: 2,
            borderColor: COLORS.icon.outlinePrimary,
            borderRadius: 16,
          }}
        >
          <CText variant="containerLabel" style={{ paddingBottom: 16 }} bold>
            {heading}
          </CText>

          <View style={{ rowGap: 14 }}>
            {tips.map((tip, index) => (
              <View
                key={index}
                style={{
                  flexDirection: "row",
                  alignItems: "flex-start",
                }}
              >
                {/* Bullet Circle */}
                <View
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: COLORS.text.secondary,
                    marginTop: 7,
                    marginRight: 10,
                  }}
                />
                {/* Text */}
                <View style={{ flex: 1 }}>
                  <CText style={{ color: COLORS.text.secondary }}>
                    <CText
                      style={{
                        color: COLORS.text.secondary,
                      }}
                      bold
                    >
                      {tip.title}
                    </CText>{" "}
                    {tip.description}
                  </CText>
                </View>
              </View>
            ))}
          </View>
        </View>
      </View>
    </View>
  );
};
