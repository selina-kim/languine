import { COLORS } from "@/constants/colors";
import React from "react";
import { Path, Svg } from "react-native-svg";

export const TrashIcon: React.FC<{ stroke?: string }> = ({
  stroke = COLORS.accent.delete,
}) => (
  <Svg width="21" height="20" viewBox="0 0 21 20" fill="none">
    <Path
      d="M8.75 9.1665V14.1665"
      stroke={stroke}
      strokeWidth="1.25713"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <Path
      d="M12.25 9.1665V14.1665"
      stroke={stroke}
      strokeWidth="1.25713"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <Path
      d="M16.625 5V16.6667C16.625 17.1087 16.4406 17.5326 16.1124 17.8452C15.7842 18.1577 15.3391 18.3333 14.875 18.3333H6.125C5.66087 18.3333 5.21575 18.1577 4.88756 17.8452C4.55937 17.5326 4.375 17.1087 4.375 16.6667V5"
      stroke="#D41605"
      strokeWidth="1.25713"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <Path
      d="M2.625 5H18.375"
      stroke={stroke}
      strokeWidth="1.25713"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <Path
      d="M7 4.99984V3.33317C7 2.89114 7.18437 2.46722 7.51256 2.15466C7.84075 1.8421 8.28587 1.6665 8.75 1.6665H12.25C12.7141 1.6665 13.1592 1.8421 13.4874 2.15466C13.8156 2.46722 14 2.89114 14 3.33317V4.99984"
      stroke="#D41605"
      strokeWidth="1.25713"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </Svg>
);
