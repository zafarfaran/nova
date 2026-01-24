import Anthropic from "@anthropic-ai/sdk";
import { NextRequest } from "next/server";
import { db } from "~/server/db";
import { clientsApi, vatPeriodsApi } from "~/lib/api/client";

const anthropic = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
});

// Define tools for the AI agent
const tools: Anthropic.Tool[] = [
    {
        name: "calculate",
        description: "Perform mathematical calculations. Supports basic arithmetic operations.",
        input_schema: {
            type: "object",
            properties: {
                expression: {
                    type: "string",
                    description: "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5 - 3')",
                },
            },
            required: ["expression"],
        },
    },
    {
        name: "get_current_date",
        description: "Get the current date and time information",
        input_schema: {
            type: "object",
            properties: {},
        },
    },
    {
        name: "search_clients",
        description: "Search for clients in the database by name or email. Returns clients from both the local database (ClientSetup) and the backend VAT system.",
        input_schema: {
            type: "object",
            properties: {
                query: {
                    type: "string",
                    description: "Search term (client name or email)",
                },
            },
            required: ["query"],
        },
    },
    {
        name: "get_vat_info",
        description: "Get VAT period information for a specific client. Uses the backend VAT system for detailed VAT period data.",
        input_schema: {
            type: "object",
            properties: {
                clientId: {
                    type: "string",
                    description: "The client ID (can be local ClientSetup ID or backend client ID)",
                },
                useBackend: {
                    type: "boolean",
                    description: "If true, use backend client ID directly. If false/omitted, look up by local ClientSetup ID.",
                },
            },
            required: ["clientId"],
        },
    },
];

// Tool execution functions
async function executeTool(toolName: string, toolInput: any): Promise<string> {
    switch (toolName) {
        case "calculate":
            try {
                // Safe evaluation of mathematical expressions
                const result = Function(`"use strict"; return (${toolInput.expression})`)();
                return `The result of ${toolInput.expression} is ${result}`;
            } catch (error) {
                return `Error calculating expression: ${error}`;
            }

        case "get_current_date":
            const now = new Date();
            return `Current date and time: ${now.toLocaleString("en-GB", {
                dateStyle: "full",
                timeStyle: "long",
            })}`;

        case "search_clients":
            try {
                // Search local ClientSetup database
                const localClients = await db.clientSetup.findMany({
                    where: {
                        OR: [
                            { clientName: { contains: toolInput.query, mode: "insensitive" } },
                            { email: { contains: toolInput.query, mode: "insensitive" } },
                        ],
                    },
                    take: 5,
                    select: {
                        id: true,
                        clientName: true,
                        email: true,
                        entityType: true,
                        vatScheme: true,
                        backendClientId: true,
                    },
                });

                // Also search backend clients
                let backendClients: Array<{
                    id: number;
                    name: string;
                    contact_email: string | null;
                    entity_type: string;
                }> = [];
                try {
                    backendClients = await clientsApi.search(toolInput.query);
                } catch (backendError) {
                    console.error("Backend client search error:", backendError);
                    // Continue with local results only
                }

                if (localClients.length === 0 && backendClients.length === 0) {
                    return `No clients found matching "${toolInput.query}"`;
                }

                let result = "";

                if (localClients.length > 0) {
                    result += `Found ${localClients.length} local client(s):\n${localClients
                        .map(
                            (c) =>
                                `- ${c.clientName} (${c.email}) - ${c.entityType}, ${c.vatScheme} [Local ID: ${c.id}]${c.backendClientId ? ` [Backend ID: ${c.backendClientId}]` : ""}`
                        )
                        .join("\n")}`;
                }

                if (backendClients.length > 0) {
                    if (result) result += "\n\n";
                    result += `Found ${backendClients.length} backend client(s):\n${backendClients
                        .map(
                            (c) =>
                                `- ${c.name} (${c.contact_email || "no email"}) - ${c.entity_type} [Backend ID: ${c.id}]`
                        )
                        .join("\n")}`;
                }

                return result;
            } catch (error) {
                return `Error searching clients: ${error}`;
            }

        case "get_vat_info":
            try {
                // If useBackend is true, use backend client ID directly
                if (toolInput.useBackend) {
                    const backendClientId = parseInt(toolInput.clientId, 10);
                    if (isNaN(backendClientId)) {
                        return `Invalid backend client ID: ${toolInput.clientId}`;
                    }

                    const vatPeriods = await vatPeriodsApi.getByClient(backendClientId);
                    if (vatPeriods.length === 0) {
                        return `No VAT periods found for backend client ID: ${backendClientId}`;
                    }

                    return `VAT Periods for Backend Client ${backendClientId}:\n${vatPeriods
                        .map(
                            (p) =>
                                `- Period: ${new Date(p.period_start).toLocaleDateString()} - ${new Date(p.period_end).toLocaleDateString()}\n  Status: ${p.status}${p.due_date ? `\n  Due: ${new Date(p.due_date).toLocaleDateString()}` : ""}`
                        )
                        .join("\n")}`;
                }

                // Look up local ClientSetup first
                const client = await db.clientSetup.findUnique({
                    where: { id: toolInput.clientId },
                    select: {
                        clientName: true,
                        vatScheme: true,
                        vatPeriodLabel: true,
                        vatPeriodStart: true,
                        vatPeriodEnd: true,
                        backendClientId: true,
                    },
                });

                if (!client) {
                    return `Client not found with ID: ${toolInput.clientId}`;
                }

                let result = `VAT Information for ${client.clientName}:
- VAT Scheme: ${client.vatScheme}
- VAT Period: ${client.vatPeriodLabel}
- Period Start: ${new Date(client.vatPeriodStart).toLocaleDateString()}
- Period End: ${new Date(client.vatPeriodEnd).toLocaleDateString()}`;

                // If linked to backend, fetch additional VAT period data
                if (client.backendClientId) {
                    try {
                        const vatPeriods = await vatPeriodsApi.getByClient(client.backendClientId);
                        if (vatPeriods.length > 0) {
                            result += `\n\nBackend VAT Periods (${vatPeriods.length} total):\n${vatPeriods
                                .map(
                                    (p) =>
                                        `- ${new Date(p.period_start).toLocaleDateString()} - ${new Date(p.period_end).toLocaleDateString()}: ${p.status}`
                                )
                                .join("\n")}`;
                        }
                    } catch (backendError) {
                        console.error("Backend VAT periods error:", backendError);
                        // Continue with local data only
                    }
                }

                return result;
            } catch (error) {
                return `Error fetching VAT info: ${error}`;
            }

        default:
            return `Unknown tool: ${toolName}`;
    }
}

export async function POST(request: NextRequest) {
    const encoder = new TextEncoder();

    try {
        const { messages } = await request.json();

        const stream = new ReadableStream({
            async start(controller) {
                try {
                    let fullResponse = "";
                    const conversationMessages: Anthropic.MessageParam[] = messages;
                    // Track content blocks by their index
                    const contentBlocks = new Map<number, Anthropic.ContentBlock>();

                    // Create streaming message
                    const messageStream = await anthropic.messages.create({
                        model: "claude-3-opus-20240229",
                        max_tokens: 4096,
                        messages: conversationMessages,
                        tools: tools,
                        stream: true,
                    });

                    for await (const event of messageStream) {
                        // Handle different event types
                        if (event.type === "content_block_start") {
                            // Store the content block for later reference
                            contentBlocks.set(event.index, event.content_block);
                            continue;
                        }

                        if (event.type === "content_block_delta") {
                            if (event.delta.type === "text_delta") {
                                const text = event.delta.text;
                                fullResponse += text;

                                // Send text chunk to client
                                controller.enqueue(
                                    encoder.encode(`data: ${JSON.stringify({ type: "text", content: text })}\n\n`)
                                );
                            }
                        }

                        if (event.type === "message_delta") {
                            if (event.delta.stop_reason === "tool_use") {
                                // Tool use detected
                                controller.enqueue(
                                    encoder.encode(`data: ${JSON.stringify({ type: "tool_start" })}\n\n`)
                                );
                            }
                        }

                        if (event.type === "content_block_stop") {
                            // Content block finished - retrieve it from our tracking map
                            const content = contentBlocks.get(event.index);

                            if (content && content.type === "tool_use") {
                                // Execute tool
                                controller.enqueue(
                                    encoder.encode(
                                        `data: ${JSON.stringify({
                                            type: "tool_executing",
                                            tool: content.name
                                        })}\n\n`
                                    )
                                );

                                const toolResult = await executeTool(content.name, content.input);

                                controller.enqueue(
                                    encoder.encode(
                                        `data: ${JSON.stringify({
                                            type: "tool_result",
                                            tool: content.name,
                                            result: toolResult
                                        })}\n\n`
                                    )
                                );

                                // Continue conversation with tool result
                                conversationMessages.push({
                                    role: "assistant",
                                    content: [content],
                                });

                                conversationMessages.push({
                                    role: "user",
                                    content: [
                                        {
                                            type: "tool_result",
                                            tool_use_id: content.id,
                                            content: toolResult,
                                        },
                                    ],
                                });

                                // Get follow-up response
                                const followUpStream = await anthropic.messages.create({
                                    model: "claude-3-opus-20240229",
                                    max_tokens: 4096,
                                    messages: conversationMessages,
                                    tools: tools,
                                    stream: true,
                                });

                                for await (const followUpEvent of followUpStream) {
                                    if (
                                        followUpEvent.type === "content_block_delta" &&
                                        followUpEvent.delta.type === "text_delta"
                                    ) {
                                        const text = followUpEvent.delta.text;
                                        fullResponse += text;
                                        controller.enqueue(
                                            encoder.encode(`data: ${JSON.stringify({ type: "text", content: text })}\n\n`)
                                        );
                                    }
                                }
                            }
                        }
                    }

                    // Send completion signal
                    controller.enqueue(
                        encoder.encode(`data: ${JSON.stringify({ type: "done" })}\n\n`)
                    );
                    controller.close();
                } catch (error) {
                    console.error("Streaming error:", error);
                    controller.enqueue(
                        encoder.encode(
                            `data: ${JSON.stringify({ type: "error", message: String(error) })}\n\n`
                        )
                    );
                    controller.close();
                }
            },
        });

        return new Response(stream, {
            headers: {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                Connection: "keep-alive",
            },
        });
    } catch (error) {
        console.error("API error:", error);
        return new Response(JSON.stringify({ error: String(error) }), {
            status: 500,
            headers: { "Content-Type": "application/json" },
        });
    }
}
