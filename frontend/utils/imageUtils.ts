/**
 * Convert a card image object ID to a full backend presigned URL
 * @param objectId - The MinIO object ID (e.g., "images/card_13.jpg")
 * @returns The full presigned URL to access the image, or null if no object ID
 */
export const getImageUrl = (objectId: string | null): string | null => {
  if (!objectId) {
    return null;
  }

  const baseUrl = process.env.EXPO_PUBLIC_API_URL;

  // If already a full backend URL, use it directly.
  if (baseUrl && objectId.startsWith(baseUrl)) {
    return objectId;
  }

  // If already an absolute URL (e.g., Unsplash), use it directly.
  if (/^https?:\/\//i.test(objectId)) {
    return objectId;
  }

  // Some legacy rows may contain URL-encoded absolute URLs.
  // Example: "https:%2F%2Fimages.unsplash.com%2F..."
  try {
    const decoded = decodeURIComponent(objectId);
    if (/^https?:\/\//i.test(decoded)) {
      return decoded;
    }
  } catch {
    // Keep original value if decoding fails.
  }

  // Encode the object ID for URL safety
  const encodedId = encodeURIComponent(objectId);
  if (!baseUrl) {
    return objectId;
  }
  return `${baseUrl}/cards/image/${encodedId}`;
};

/**
 * Check if an image URL is a backend URL or an external URL
 * @param url - The image URL to check
 * @returns true if it's a backend presigned URL
 */
export const isBackendImageUrl = (url: string): boolean => {
  const baseUrl = process.env.EXPO_PUBLIC_API_URL;
  if (!baseUrl) {
    return false;
  }
  return url.startsWith(baseUrl);
};
