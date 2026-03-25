import { COLORS } from "@/constants/colors";
import React from "react";
import Svg, { Path } from "react-native-svg";

export const ChevronDownIcon: React.FC<{ stroke?: string }> = ({
  stroke = COLORS.text.primary,
}) => (
  <Svg width="100%" height="100%" viewBox="0 0 16 16" fill="none">
    <Path
      d="M3.99884 5.99854L7.99771 9.99741L11.9966 5.99854"
      stroke={stroke}
      strokeWidth="1.33296"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </Svg>
);
