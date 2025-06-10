/**
 * Helper function to transform NoVNC URLs
 *
 * This function checks if a NoVNC URL points to localhost and replaces it with
 * the current window's hostname if they don't match.
 *
 * @param novncUrl The original NoVNC URL from the backend
 * @returns The transformed URL with the correct hostname
 */
export function transformNovncUrl(novncUrl: string | null): string | null {
  if (!novncUrl) return null;

  try {
    const url = new URL(novncUrl);

    // Check if the URL points to localhost
    if (
      url.hostname === "localhost" &&
      window.location.hostname !== "localhost"
    ) {
      // Replace localhost with the current hostname
      url.hostname = window.location.hostname;
      return url.toString();
    }

    return novncUrl;
  } catch (error) {
    // Silently handle the error and return the original URL
    return novncUrl;
  }
}
