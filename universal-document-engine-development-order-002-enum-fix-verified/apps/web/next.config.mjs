/** @type {import('next').NextConfig} */
const nextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  transpilePackages: ['@ude/ui', '@ude/api-client'],
};

export default nextConfig;
