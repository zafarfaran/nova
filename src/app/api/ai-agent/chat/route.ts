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
                // Search clients database
                const clients = await db.client.findMany({
                    where: {
                        OR: [
                            { name: { contains: toolInput.query, mode: "insensitive" } },
                            { contactEmail: { contains: toolInput.query, mode: "insensitive" } },
                        ],
                    },
                    take: 10,
                    select: {
                        id: true,
                        name: true,
                        contactEmail: true,
                        entityType: true,
                        vatScheme: true,
                    },
                });

                if (clients.length === 0) {
                    return `No clients found matching "${toolInput.query}"`;
                }

                return `Found ${clients.length} client(s):\n${clients
                    .map(
                        (c: { id: number; name: string; contactEmail: string | null; entityType: string; vatScheme: string | null }) =>
                            `- ${c.name} (${c.contactEmail || "no email"}) - ${c.entityType}, ${c.vatScheme || "N/A"} [ID: ${c.id}]`
                    )
                    .join("\n")}`;
            } catch (error) {
                return `Error searching clients: ${error}`;
            }

        case "get_vat_info":
            try {
                const clientId = parseInt(toolInput.clientId, 10);
                if (isNaN(clientId)) {
                    return `Invalid client ID: ${toolInput.clientId}`;
                }

                // Look up client with VAT periods
                const client = await db.client.findUnique({
                    where: { id: clientId },
                    include: {
                        vatPeriods: {
                            orderBy: { periodEnd: "desc" },
                            take: 5,
                        },
                    },
                });

                if (!client) {
                    return `Client not found with ID: ${clientId}`;
                }

                let result = `VAT Information for ${client.name}:
- VAT Scheme: ${client.vatScheme || "Not set"}
- VAT Number: ${client.vatNumber || "Not set"}`;

                if (client.vatPeriods.length > 0) {
                    result += `\n\nVAT Periods (${client.vatPeriods.length} shown):\n${client.vatPeriods
                        .map(
                            (p: { periodStart: Date; periodEnd: Date; status: string; dueDate: Date | null }) =>
                                `- ${new Date(p.periodStart).toLocaleDateString()} - ${new Date(p.periodEnd).toLocaleDateString()}: ${p.status}${p.dueDate ? ` (Due: ${new Date(p.dueDate).toLocaleDateString()})` : ""}`
                        )
                        .join("\n")}`;
                } else {
                    result += "\n\nNo VAT periods found for this client.";
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
