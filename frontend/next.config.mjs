// Owner: Person B
/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: process.env.NEXT_BUILD_DIR || '.next',
  reactStrictMode: true,
  poweredByHeader: false,
};

export default nextConfig;
