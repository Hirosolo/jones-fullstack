import type { NextApiHandler } from "next";

export const withSessionRoute = (handler: NextApiHandler): NextApiHandler => {
  return handler;
};
