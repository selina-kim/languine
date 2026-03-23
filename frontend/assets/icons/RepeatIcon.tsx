import { COLORS } from "@/constants/colors";
import React from "react";
import { Path, Svg } from "react-native-svg";

export const RepeatIcon: React.FC = ({ stroke = COLORS.text.primary }: { stroke?: string }) => (
  <Svg width="100%" height="100%" viewBox="0 0 16 16" fill="none">
    <Path
      d="M1.99951 7.99776C1.99951 9.18412 2.35131 10.3438 3.01041 11.3302C3.66951 12.3167 4.60632 13.0855 5.70237 13.5395C6.79842 13.9935 8.00448 14.1123 9.16804 13.8808C10.3316 13.6494 11.4004 13.0781 12.2393 12.2392C13.0781 11.4003 13.6494 10.3315 13.8809 9.16798C14.1123 8.00442 13.9935 6.79836 13.5395 5.70231C13.0855 4.60626 12.3167 3.66945 11.3303 3.01035C10.3439 2.35125 9.18418 1.99945 7.99782 1.99945C6.32093 2.00576 4.71139 2.66008 3.50575 3.8256L1.99951 5.33185"
      stroke={stroke}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <Path
      d="M1.99951 1.99945V5.33185H5.33191"
      stroke={stroke}
      strokeWidth="1.33296"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </Svg>
);
