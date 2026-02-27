import { CText } from "@/components/common/CText";
import { InfoContainer} from "@/components/features/help/InfoContainer";
import { StepContainer} from "@/components/features/help/StepContainer";
import { ListContainer } from "@/components/features/help/ListContainer";
import { FAQ } from "@/components/features/help/FAQ";
import { ScrollView } from "react-native";

type LabelProps = {
  text: string;
}

const Label = ({ text }: LabelProps) => (
  <CText
    style={{
      textAlign: "left",
      paddingHorizontal: 25,
      paddingTop: 25,
      paddingBottom: 5,
    }}
    bold
  >
    {text}
  </CText>
);

export default function Help() {
  return (
    <ScrollView
      style={{
        flex: 1,
        padding: 10,
      }}
    >
      <InfoContainer />
      <Label text="Getting Started" />
      <StepContainer />
      <StepContainer />
      <StepContainer />
      <StepContainer />
      <Label text="Frequently Asked Questions" />
      <FAQ />
      <ListContainer />
    </ScrollView>
  );
}
