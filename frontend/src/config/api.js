/**
 * API Configuration based on environment
 * VITE_FRONTEND_ENV: 'dev' or 'prod'
 */

const getApiBaseUrl = () => {
  const env = import.meta.env.VITE_FRONTEND_ENV || 'dev';

  if (env === 'prod') {
    return 'https://reflectly.myroslavrepin.com/api/v1';
  }
  return 'http://localhost:8080/api/v1';
};

export const FRONTEND_ENV = import.meta.env.VITE_FRONTEND_ENV || 'dev';
export const API_BASE_URL = getApiBaseUrl();
export const IS_DEV = FRONTEND_ENV === 'dev';
export const IS_PROD = FRONTEND_ENV === 'prod';

if (typeof window !== 'undefined') {
  console.log('API Configuration:', {
    FRONTEND_ENV,
    API_BASE_URL,
    IS_DEV,
    IS_PROD,
  });
}
