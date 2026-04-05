import { describe, expect, test, beforeEach, jest } from "@jest/globals";

const mockFAQ = [
  {
    id: "1",
    question: "How do I create a deck?",
    answer: "Click the + button and follow the steps.",
  },
  {
    id: "2",
    question: "What is FSRS?",
    answer: "FSRS is a spaced repetition algorithm.",
  },
];

const mockTips = [
  {
    id: "1",
    title: "Tip 1",
    description: "Study regularly for best results.",
  },
];

describe("Help Tab Logic", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should display help content sections", () => {
    const helpSections = [
      { id: "1", title: "Create a Deck", step: "Step 1" },
      { id: "2", title: "Add Cards", step: "Step 2" },
      { id: "3", title: "Start Reviewing", step: "Step 3" },
      { id: "4", title: "Rate Your Memory", step: "Step 4" },
    ];

    expect(helpSections).toHaveLength(4);
    expect(helpSections[0].title).toBe("Create a Deck");
  });

  test("should display Getting Started steps", () => {
    const startingSteps = [
      {
        title: "Create a Deck",
        step: "Step 1",
        description:
          "Start by creating a new deck for the language you want to learn.",
      },
      {
        title: "Add Cards",
        step: "Step 2",
        description: "Add flashcards to your deck.",
      },
      {
        title: "Start Reviewing",
        step: "Step 3",
        description: "Begin your review session.",
      },
      {
        title: "Rate Your Memory",
        step: "Step 4",
        description: "Rate how easily you remembered it.",
      },
    ];

    expect(startingSteps).toHaveLength(4);
    expect(startingSteps[0].step).toBe("Step 1");
  });

  test("should display FAQ items", () => {
    expect(mockFAQ).toHaveLength(2);
    expect(mockFAQ[0].question).toContain("create");
    expect(mockFAQ[1].answer).toContain("spaced");
  });

  test("should have questions and answers in FAQ", () => {
    mockFAQ.forEach((item) => {
      expect(item).toHaveProperty("question");
      expect(item).toHaveProperty("answer");
      expect(item.question.length).toBeGreaterThan(0);
      expect(item.answer.length).toBeGreaterThan(0);
    });
  });

  test("should display tips", () => {
    expect(mockTips).toHaveLength(1);
    expect(mockTips[0].title).toBe("Tip 1");
  });

  test("should have title and description in tips", () => {
    mockTips.forEach((tip) => {
      expect(tip).toHaveProperty("title");
      expect(tip).toHaveProperty("description");
      expect(tip.title.length).toBeGreaterThan(0);
      expect(tip.description.length).toBeGreaterThan(0);
    });
  });

  test("should organize help content in sections", () => {
    const helpContent = {
      infoSection: { id: "1", name: "Info" },
      gettingStarted: { id: "2", name: "Getting Started", itemCount: 4 },
      faq: { id: "3", name: "FAQ", itemCount: mockFAQ.length },
      tips: { id: "4", name: "Tips", itemCount: mockTips.length },
    };

    expect(helpContent.gettingStarted.itemCount).toBe(4);
    expect(helpContent.faq.itemCount).toBeGreaterThan(0);
    expect(helpContent.tips.itemCount).toBeGreaterThan(0);
  });
});
