import { createContext, ReactNode, useContext, useMemo, useState } from "react";

interface ReviewSessionContextValue {
  isReviewSessionActive: boolean;
  setIsReviewSessionActive: (isActive: boolean) => void;
  exitReviewSessionSignal: number;
  requestExitReviewSession: () => void;
}

const ReviewSessionContext = createContext<ReviewSessionContextValue | undefined>(
  undefined,
);

interface ReviewSessionProviderProps {
  children: ReactNode;
}

export const ReviewSessionProvider = ({
  children,
}: ReviewSessionProviderProps) => {
  const [isReviewSessionActive, setIsReviewSessionActive] = useState(false);
  const [exitReviewSessionSignal, setExitReviewSessionSignal] = useState(0);

  const requestExitReviewSession = () => {
    setExitReviewSessionSignal((prev) => prev + 1);
  };

  const value = useMemo(
    () => ({
      isReviewSessionActive,
      setIsReviewSessionActive,
      exitReviewSessionSignal,
      requestExitReviewSession,
    }),
    [isReviewSessionActive, exitReviewSessionSignal],
  );

  return (
    <ReviewSessionContext.Provider value={value}>
      {children}
    </ReviewSessionContext.Provider>
  );
};

export const useReviewSession = () => {
  const context = useContext(ReviewSessionContext);

  if (!context) {
    throw new Error("useReviewSession must be used within ReviewSessionProvider");
  }

  return context;
};
