import client from "../client";

export interface PhotoResult {
  id: string;
  alt_description: string;
  urls: {
    raw: string;
    full: string;
    regular: string;
    small: string;
    thumb: string;
  };
  user: {
    name: string;
    username: string;
  };
  links: {
    download: string;
  };
}

export interface ImageSearchResponse {
  total: number;
  total_pages: number;
  results: PhotoResult[];
}

export const searchImages = (
  query: string,
  page: number = 1,
  perPage: number = 5,
): Promise<{ data: ImageSearchResponse; error: string | null }> =>
  client.get(`/images/search?query=${encodeURIComponent(query)}&page=${page}&per_page=${perPage}`);

export default { searchImages };
