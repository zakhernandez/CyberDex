import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { encode } from "next-auth/jwt";

const secret = process.env.AUTH_SECRET;

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID,
      clientSecret: process.env.AUTH_GOOGLE_SECRET,
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account && profile) {
        token.googleId = profile.sub ?? undefined;
        token.email = profile.email ?? undefined;
        token.name = profile.name ?? undefined;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.googleId = token.googleId as string;
      }
      return session;
    },
  },
  session: {
    strategy: "jwt",
  },
  jwt: {
    // Use HS256-signed JWTs (not JWE-encrypted) for easy verification in FastAPI
    async encode({ token, secret }) {
      const secretKey = typeof secret === "string" ? secret : secret[0];
      const { SignJWT } = await import("jose");
      const encoder = new TextEncoder();
      const key = encoder.encode(secretKey);
      return await new SignJWT({ ...token })
        .setProtectedHeader({ alg: "HS256" })
        .setIssuedAt()
        .setExpirationTime("30d")
        .sign(key);
    },
    async decode({ token, secret }) {
      if (!token) return null;
      const secretKey = typeof secret === "string" ? secret : secret[0];
      const { jwtVerify } = await import("jose");
      const encoder = new TextEncoder();
      const key = encoder.encode(secretKey);
      try {
        const { payload } = await jwtVerify(token, key);
        return payload as any;
      } catch {
        return null;
      }
    },
  },
});