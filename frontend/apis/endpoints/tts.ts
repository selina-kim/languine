import { storage } from "@/utils/storage";

export interface GenerateTtsRequestPayload {
  text: string;
  language: string;
  speaker?: string;
}

const getAuthToken = async (): Promise<string | null> => {
  try {
    const userData = await storage.getItem("user");
    if (!userData) {
      return null;
    }

    const user = JSON.parse(userData) as { token?: string };
    return user.token ?? null;
  } catch (error) {
    console.error("Error retrieving auth token:", error);
    return null;
  }
};

export const generateSpeechAudio = async (
  payload: GenerateTtsRequestPayload,
): Promise<{ data: Response | null; error: string | null }> => {
  try {
    const token = await getAuthToken();

    if (!token) {
      return { data: null, error: "Invalid token" };
    }

    const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL}/tts`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const responseText = await response.text();
      let errorMessage = response.statusText || "Request failed";

      if (responseText) {
        try {
          const parsed = JSON.parse(responseText) as { error?: string };
          errorMessage = parsed.error ?? errorMessage;
        } catch {
          errorMessage = responseText;
        }
      }

      throw new Error(`HTTP ${response.status} - ${errorMessage}`);
    }

    return { data: response, error: null };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Failed to generate speech";
    const errorParts = errorMessage.split(" - ");

    return {
      data: null,
      error: errorParts[errorParts.length - 1],
    };
  }
};

export default { generateSpeechAudio };
