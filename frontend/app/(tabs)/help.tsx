import { DecksIcon } from "@/assets/icons/DecksIcon";
import { OpenBookIcon } from "@/assets/icons/OpenBookIcon";
import { PlayIcon } from "@/assets/icons/PlayIcon";
import { PlusFilledIcon } from "@/assets/icons/PlusFilledIcon";
import { CText } from "@/components/common/CText";
import { FAQ } from "@/components/features/help/FAQ";
import { InfoContainer } from "@/components/features/help/InfoContainer";
import { StepContainer } from "@/components/features/help/StepContainer";
import { TipsContainer } from "@/components/features/help/TipsContainer";
import { DATA_FAQ, DATA_TIP } from "@/constants/helpData";
import { ScrollView } from "react-native";

type LabelProps = {
  text: string;
};

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
      <StepContainer
        title="Create a Deck"
        step="Step 1"
        description="Start by creating a new deck for the language you want to learn. Choose a name, select your target language, and add a description."
        Icon={<DecksIcon />}
      />
      <StepContainer
        title="Add Cards"
        step="Step 2"
        description="Add flashcards to your deck. The front will hold the word in your target language, and the back will hold the translation."
        Icon={<PlusFilledIcon />}
        iconStyle={{ padding: 2 }}
      />
      <StepContainer
        title="Start Reviewing"
        step="Step 3"
        description="Begin your review session. Look at each card's content, try to remember the translation, then flip the card to check."
        Icon={<PlayIcon />}
      />
      <StepContainer
        title="Rate Your Memory"
        step="Step 4"
        description="After checking the translation, rate how easily you remembered it. This helps the algorithm schedule the card's next appearance."
        Icon={<OpenBookIcon />}
      />
      <Label text="Frequently Asked Questions" />
      <FAQ faqs={DATA_FAQ} />
      <TipsContainer tips={DATA_TIP} />
    </ScrollView>
  );
}
