import {
  CopilotRuntime,
  AnthropicAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";

/**
 * CopilotKit backend runtime route.
 * Uses Anthropic (Claude) as the LLM for the CopilotKit chat panel.
 *
 * The CopilotKit sidebar chat will use this runtime.
 * Market analysis (from "Run Analysis" button) goes directly to the backend
 * via POST /analysis/run → Bedrock.
 */

const runtime = new CopilotRuntime({
  // Actions are registered on the frontend via useCopilotAction in page.tsx
  // This runtime handles the LLM inference for the sidebar chat
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new AnthropicAdapter({
      model: "claude-3-5-sonnet-20241022",
    }),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
