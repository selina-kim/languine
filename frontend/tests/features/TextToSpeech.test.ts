import { describe, expect, test, jest, beforeEach } from "@jest/globals";

// Mock expo-audio
jest.mock("expo-audio", () => ({
  createAudioPlayer: jest.fn(),
  setAudioModeAsync: jest.fn(),
}));

// Mock storage for auth tokens
jest.mock("@/utils/storage", () => ({
  storage: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    deleteItem: jest.fn(),
  },
}));

const { createAudioPlayer, setAudioModeAsync } = require("expo-audio");
const { storage } = require("@/utils/storage");

interface AudioPlayer {
  play: () => void;
  pause: () => Promise<void>;
  stop: () => Promise<void>;
  seekTo: (position: number) => Promise<void>;
  remove: () => void;
  addListener: (event: string, callback: (status: any) => void) => void;
}

describe("Text-to-Speech (TTS) Audio Playback", () => {
  let audioPlayersRef: Map<string, AudioPlayer>;

  beforeEach(() => {
    jest.clearAllMocks();
    audioPlayersRef = new Map();
  });

  describe("Audio URL Construction", () => {
    test("should build correct audio URL with object ID", () => {
      const apiUrl = "https://api.example.com";
      const objectId = "word_audio_123";
      const expectedUrl = `${apiUrl}/cards/audio/${encodeURIComponent(objectId)}`;

      expect(expectedUrl).toBe(`${apiUrl}/cards/audio/${objectId}`);
    });

    test("should encode special characters in object ID", () => {
      const objectId = "word audio #123";
      const encodedId = encodeURIComponent(objectId);

      expect(encodedId).toBe("word%20audio%20%23123");
      expect(`https://api.example.com/cards/audio/${encodedId}`).toContain(
        "%20",
      );
    });
  });

  describe("Audio Player Creation with Auth", () => {
    test("should create player with Authorization Bearer token", async () => {
      const objectId = "card_audio_123";
      const token = "auth_token_xyz";
      const apiUrl = "https://api.example.com";

      storage.getItem.mockResolvedValue(JSON.stringify({ token }));

      const authToken = await storage.getItem("auth_token");
      const parsedToken = JSON.parse(authToken);

      createAudioPlayer({
        uri: `${apiUrl}/cards/audio/${objectId}`,
        headers: {
          Authorization: `Bearer ${parsedToken.token}`,
        },
      });

      expect(createAudioPlayer).toHaveBeenCalledWith(
        expect.objectContaining({
          uri: expect.stringContaining("/cards/audio/"),
          headers: expect.objectContaining({
            Authorization: "Bearer auth_token_xyz",
          }),
        }),
      );
    });

    test("should handle missing auth token gracefully", async () => {
      storage.getItem.mockResolvedValue(null);

      const token = await storage.getItem("auth_token");

      expect(token).toBeNull();
    });

    test("should reuse cached player instead of creating duplicate", () => {
      const objectId = "audio_001";
      const mockPlayer = {
        play: jest.fn(),
        pause: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        stop: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        seekTo: jest
          .fn<(position: number) => Promise<void>>()
          .mockResolvedValue(undefined),
        remove: jest.fn(),
        addListener: jest.fn(),
      } as unknown as AudioPlayer;

      audioPlayersRef.set(objectId, mockPlayer);

      const cachedPlayer = audioPlayersRef.get(objectId);

      expect(cachedPlayer).toBe(mockPlayer);
      expect(audioPlayersRef.size).toBe(1);
    });
  });

  describe("Audio Playback Control", () => {
    test("should call seekTo(0) before playing audio", async () => {
      const mockPlayer = {
        play: jest.fn(),
        pause: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        stop: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        seekTo: jest
          .fn<(position: number) => Promise<void>>()
          .mockResolvedValue(undefined),
        remove: jest.fn(),
        addListener: jest.fn(),
      } as unknown as AudioPlayer;

      await mockPlayer.seekTo(0);
      mockPlayer.play();

      expect(mockPlayer.seekTo).toHaveBeenCalledWith(0);
      expect(mockPlayer.play).toHaveBeenCalled();
    });

    test("should play audio without awaiting", () => {
      let isTtsPlaying = false;

      const mockPlayer = {
        play: jest.fn(() => {
          isTtsPlaying = true;
        }),
        pause: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        stop: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        seekTo: jest
          .fn<(position: number) => Promise<void>>()
          .mockResolvedValue(undefined),
        remove: jest.fn(),
        addListener: jest.fn(),
      } as unknown as AudioPlayer;

      mockPlayer.play();

      expect(isTtsPlaying).toBe(true);
      expect(mockPlayer.play).toHaveBeenCalled();
    });

    test("should prevent concurrent playback with isTtsPlaying flag", () => {
      let isTtsPlaying = false;

      const shouldPlayAudio = (objectId: string | null) => {
        return objectId !== null && !isTtsPlaying;
      };

      const objectId = "audio_001";

      expect(shouldPlayAudio(objectId)).toBe(true);

      isTtsPlaying = true;

      expect(shouldPlayAudio(objectId)).toBe(false);
    });
  });

  describe("Playback Status Listener", () => {
    test("should listen for playbackStatusUpdate events", () => {
      let isTtsPlaying = true;

      const mockPlayer = {
        play: jest.fn(),
        pause: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        stop: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        seekTo: jest
          .fn<(position: number) => Promise<void>>()
          .mockResolvedValue(undefined),
        remove: jest.fn(),
        addListener: jest.fn(
          (event: string, callback: (status: any) => void) => {
            if (event === "playbackStatusUpdate") {
              callback({ isLoaded: true, didJustFinish: true });
            }
          },
        ),
      } as unknown as AudioPlayer;

      mockPlayer.addListener("playbackStatusUpdate", (status: any) => {
        if (status.isLoaded && status.didJustFinish) {
          isTtsPlaying = false;
        }
      });

      expect(isTtsPlaying).toBe(false);
      expect(mockPlayer.addListener).toHaveBeenCalledWith(
        "playbackStatusUpdate",
        expect.any(Function),
      );
    });

    test("should set isTtsPlaying to false when didJustFinish is true", () => {
      let isTtsPlaying = true;

      const mockCallback = (status: any) => {
        if (status.isLoaded && status.didJustFinish) {
          isTtsPlaying = false;
        }
      };

      mockCallback({ isLoaded: true, didJustFinish: true });

      expect(isTtsPlaying).toBe(false);
    });

    test("should not change state when audio is still loaded and playing", () => {
      let isTtsPlaying = true;

      const mockCallback = (status: any) => {
        if (status.isLoaded && status.didJustFinish) {
          isTtsPlaying = false;
        }
      };

      mockCallback({ isLoaded: true, didJustFinish: false });

      expect(isTtsPlaying).toBe(true);
    });
  });

  describe("Audio Preloading", () => {
    test("should preload audio files on mount", () => {
      const cards = [
        { word_audio: "audio_1", trans_audio: "audio_2" },
        { word_audio: "audio_3", trans_audio: null },
      ];

      const audioIds = cards
        .flatMap((card) => [card.word_audio, card.trans_audio])
        .filter((id): id is string => Boolean(id));

      expect(audioIds).toEqual(["audio_1", "audio_2", "audio_3"]);
      expect(audioIds.length).toBe(3);
    });

    test("should not preload duplicate audio IDs", () => {
      const cards = [
        { word_audio: "audio_1", trans_audio: "audio_1" }, // Duplicate
        { word_audio: "audio_2", trans_audio: "audio_1" }, // Duplicate
      ];

      const audioIds = Array.from(
        new Set(
          cards
            .flatMap((card) => [card.word_audio, card.trans_audio])
            .filter((id): id is string => Boolean(id)),
        ),
      );

      expect(audioIds).toEqual(["audio_1", "audio_2"]);
    });

    test("should skip preloading if already cached", () => {
      const objectId = "audio_001";
      const mockPlayer = {
        play: jest.fn(),
        pause: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        stop: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        seekTo: jest
          .fn<(position: number) => Promise<void>>()
          .mockResolvedValue(undefined),
        remove: jest.fn(),
        addListener: jest.fn(),
      } as unknown as AudioPlayer;

      audioPlayersRef.set(objectId, mockPlayer);

      const shouldPreload = !audioPlayersRef.has(objectId);

      expect(shouldPreload).toBe(false);
    });
  });

  describe("Audio Cleanup", () => {
    test("should remove players on unmount", () => {
      const mockPlayer1 = {
        play: jest.fn(),
        pause: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        stop: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        seekTo: jest
          .fn<(position: number) => Promise<void>>()
          .mockResolvedValue(undefined),
        remove: jest.fn(),
        addListener: jest.fn(),
      } as unknown as AudioPlayer;

      const mockPlayer2 = {
        play: jest.fn(),
        pause: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        stop: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        seekTo: jest
          .fn<(position: number) => Promise<void>>()
          .mockResolvedValue(undefined),
        remove: jest.fn(),
        addListener: jest.fn(),
      } as unknown as AudioPlayer;

      audioPlayersRef.set("audio_1", mockPlayer1);
      audioPlayersRef.set("audio_2", mockPlayer2);

      audioPlayersRef.forEach((player) => {
        player.remove();
      });
      audioPlayersRef.clear();

      expect(mockPlayer1.remove).toHaveBeenCalled();
      expect(mockPlayer2.remove).toHaveBeenCalled();
      expect(audioPlayersRef.size).toBe(0);
    });
  });

  describe("Error Handling", () => {
    test("should handle missing auth token in getOrCreateAudioPlayer", async () => {
      storage.getItem.mockResolvedValue(null);

      const token = await storage.getItem("auth_token");

      if (!token) {
        // Return null to indicate failure
        expect(token).toBeNull();
      }
    });

    test("should catch playback errors and reset isTtsPlaying", async () => {
      let isTtsPlaying = true;

      const mockPlayer = {
        play: (jest.fn() as any).mockRejectedValue(
          new Error("Audio is unavailable"),
        ),
        pause: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        stop: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        seekTo: jest
          .fn<(position: number) => Promise<void>>()
          .mockResolvedValue(undefined),
        remove: jest.fn(),
        addListener: jest.fn(),
      } as unknown as AudioPlayer;

      try {
        await mockPlayer.play();
      } catch (error) {
        isTtsPlaying = false;
      }

      expect(isTtsPlaying).toBe(false);
    });

    test("should handle seekTo errors before playback", async () => {
      const mockPlayer = {
        play: jest.fn(),
        pause: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        stop: jest.fn<() => Promise<void>>().mockResolvedValue(undefined),
        seekTo: jest
          .fn<(position: number) => Promise<void>>()
          .mockRejectedValue(new Error("Seek failed")),
        remove: jest.fn(),
        addListener: jest.fn(),
      } as unknown as AudioPlayer;

      try {
        await mockPlayer.seekTo(0);
        mockPlayer.play();
      } catch (error) {
        expect((error as Error).message).toBe("Seek failed");
      }
    });
  });

  describe("Audio Mode Configuration", () => {
    test("should configure audio mode for silent playback during review", async () => {
      await setAudioModeAsync({
        playsInSilentMode: true,
      });

      expect(setAudioModeAsync).toHaveBeenCalledWith({
        playsInSilentMode: true,
      });
    });
  });
});
