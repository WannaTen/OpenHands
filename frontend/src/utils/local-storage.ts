// Local storage keys
export const LOCAL_STORAGE_KEYS = {
  LOGIN_METHOD: "openhands_login_method",
  LAST_PAGE: "openhands_last_page",
};

// Login methods
export enum LoginMethod {
  GITHUB = "github",
  GITLAB = "gitlab",
  BITBUCKET = "bitbucket",
}

/**
 * Set the login method in local storage
 * @param method The login method (github, gitlab, or bitbucket)
 */
export const setLoginMethod = (method: LoginMethod): void => {
  localStorage.setItem(LOCAL_STORAGE_KEYS.LOGIN_METHOD, method);
};

/**
 * Get the login method from local storage
 * @returns The login method or null if not set
 */
export const getLoginMethod = (): LoginMethod | null => {
  const method = localStorage.getItem(LOCAL_STORAGE_KEYS.LOGIN_METHOD);
  return method as LoginMethod | null;
};

/**
 * Set the last visited page in local storage
 * @param page The page path to store
 */
export const setLastPage = (page: string): void => {
  localStorage.setItem(LOCAL_STORAGE_KEYS.LAST_PAGE, page);
};

/**
 * Get the last visited page from local storage
 * @returns The last visited page or null if not set
 */
export const getLastPage = (): string | null =>
  localStorage.getItem(LOCAL_STORAGE_KEYS.LAST_PAGE);

/**
 * Check if a path should be excluded from tracking
 * @param path The path to check
 * @returns true if the path should be excluded
 */
export const shouldExcludePath = (path: string): boolean => {
  // Add paths that should not be tracked
  const excludedPaths = ["/login", "/logout", "/auth", "/callback", "/error"];

  return excludedPaths.some((excludedPath) => path.startsWith(excludedPath));
};

/**
 * Clear login method and last page from local storage
 */
export const clearLoginData = (): void => {
  localStorage.removeItem(LOCAL_STORAGE_KEYS.LOGIN_METHOD);
  localStorage.removeItem(LOCAL_STORAGE_KEYS.LAST_PAGE);
};
