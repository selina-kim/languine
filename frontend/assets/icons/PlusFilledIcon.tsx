import { COLORS } from "@/constants/colors";
import React from "react";
import { Path, Svg } from "react-native-svg";

export const PlusFilledIcon: React.FC<{
  stroke?: string;
  fill?: string;
}> = ({
  stroke = COLORS.icon.outlinePrimary,
  fill = COLORS.icon.fillPrimary,
}) => (
  <Svg width="100%" height="100%" viewBox="0 0 28 28" fill="none">
    <Path 
      d="M3.75006 9H14.2501" 
      stroke={stroke}
      strokeWidth="7.2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
    />
    <Path 
      d="M9.00003 3.75V14.25" 
      stroke={stroke} 
      strokeWidth="7.2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
    />
    <Path
      d="M3.75008 9H14.2501" 
      stroke={fill} 
      strokeWidth="2.89969" 
      strokeLinecap="round" 
      strokeLinejoin="round"  
    />s
    <Path
      d="M9 3.75V14.25" 
      stroke={fill} 
      strokeWidth="2.89969" 
      strokeLinecap="round" 
      strokeLinejoin="round"
    />
  </Svg>
);