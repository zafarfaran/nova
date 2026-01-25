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
        description: "Search for clients in the database by name or email. Returns clients from both the local database (ClientSetup) and the backend tax system.",
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
        description: "Get tax period information for a specific client. Uses the backend tax system for detailed period data.",
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
    {
        name: "search_documents",
        description: "Search for documents uploaded by clients. Can search by client ID, document type, filename, or status.",
        input_schema: {
            type: "object",
            properties: {
                clientId: {
                    type: "string",
                    description: "Filter by specific client ID",
                },
                query: {
                    type: "string",
                    description: "Search term for document filename",
                },
                documentType: {
                    type: "string",
                    description: "Filter by document type (e.g., INVOICE, RECEIPT, BANK_STATEMENT)",
                },
                status: {
                    type: "string",
                    description: "Filter by document status (pending, processing, extracted, validated, failed)",
                },
            },
        },
    },
    {
        name: "get_document_details",
        description: "Get detailed information about a specific document including its validation results.",
        input_schema: {
            type: "object",
            properties: {
                documentId: {
                    type: "string",
                    description: "The document ID to look up",
                },
            },
            required: ["documentId"],
        },
    },
    {
        name: "get_client_documents",
        description: "Get all documents for a specific client, including their validation status.",
        input_schema: {
            type: "object",
            properties: {
                clientId: {
                    type: "string",
                    description: "The client ID to get documents for",
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

                // Look up client with tax periods
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

                let result = `Tax Information for ${client.name}:
- Tax Scheme: ${client.vatScheme || "Not set"}
- Tax Number: ${client.vatNumber || "Not set"}`;

                if (client.vatPeriods.length > 0) {
                    result += `\n\nTax Periods (${client.vatPeriods.length} shown):\n${client.vatPeriods
                        .map(
                            (p: { periodStart: Date; periodEnd: Date; status: string; dueDate: Date | null }) =>
                                `- ${new Date(p.periodStart).toLocaleDateString()} - ${new Date(p.periodEnd).toLocaleDateString()}: ${p.status}${p.dueDate ? ` (Due: ${new Date(p.dueDate).toLocaleDateString()})` : ""}`
                        )
                        .join("\n")}`;
                } else {
                    result += "\n\nNo tax periods found for this client.";
                }

                return result;
            } catch (error) {
                return `Error fetching tax info: ${error}`;
            }

        case "search_documents":
            try {
                const whereClause: any = {};

                if (toolInput.clientId) {
                    const parsedClientId = parseInt(toolInput.clientId, 10);
                    if (!isNaN(parsedClientId)) {
                        whereClause.evidenceItem = {
                            vatPeriod: {
                                clientId: parsedClientId,
                            },
                        };
                    }
                }

                if (toolInput.query) {
                    whereClause.filename = { contains: toolInput.query, mode: "insensitive" };
                }

                if (toolInput.documentType) {
                    whereClause.documentType = toolInput.documentType.toUpperCase();
                }

                if (toolInput.status) {
                    whereClause.status = toolInput.status.toUpperCase();
                }

                const documents = await db.document.findMany({
                    where: whereClause,
                    take: 20,
                    orderBy: { createdAt: "desc" },
                    include: {
                        evidenceItem: {
                            include: {
                                vatPeriod: {
                                    include: {
                                        client: {
                                            select: { id: true, name: true },
                                        },
                                    },
                                },
                            },
                        },
                    },
                });

                if (documents.length === 0) {
                    return `No documents found matching the search criteria.`;
                }

                return `Found ${documents.length} document(s):\n${documents
                    .map((d: any) => {
                        const clientName = d.evidenceItem?.vatPeriod?.client?.name || "Unknown Client";
                        return `- ${d.filename} (${d.documentType || "Unknown Type"}) - Status: ${d.status || "Pending"} - Client: ${clientName} [Doc ID: ${d.id}]`;
                    })
                    .join("\n")}`;
            } catch (error) {
                return `Error searching documents: ${error}`;
            }

        case "get_document_details":
            try {
                const docId = parseInt(toolInput.documentId, 10);
                if (isNaN(docId)) {
                    return `Invalid document ID: ${toolInput.documentId}`;
                }

                const document = await db.document.findUnique({
                    where: { id: docId },
                    include: {
                        evidenceItem: {
                            include: {
                                vatPeriod: {
                                    include: {
                                        client: {
                                            select: { id: true, name: true, contactEmail: true },
                                        },
                                    },
                                },
                            },
                        },
                    },
                });

                if (!document) {
                    return `Document not found with ID: ${docId}`;
                }

                const client = document.evidenceItem?.vatPeriod?.client;
                const vatPeriod = document.evidenceItem?.vatPeriod;

                let result = `Document Details:
- Filename: ${document.filename}
- Type: ${document.documentType || "Not specified"}
- Status: ${document.status || "Pending"}
- Uploaded: ${document.createdAt ? new Date(document.createdAt).toLocaleDateString() : "Unknown"}
- File URL: ${document.s3Key || "Not available"}`;

                if (client) {
                    result += `\n\nClient Information:
- Name: ${client.name}
- Email: ${client.contactEmail || "Not set"}
- Client ID: ${client.id}`;
                }

                if (vatPeriod) {
                    result += `\n\nTax Period:
- Period: ${new Date(vatPeriod.periodStart).toLocaleDateString()} - ${new Date(vatPeriod.periodEnd).toLocaleDateString()}
- Status: ${vatPeriod.status}`;
                }

                return result;
            } catch (error) {
                return `Error fetching document details: ${error}`;
            }

        case "get_client_documents":
            try {
                const clientId = parseInt(toolInput.clientId, 10);
                if (isNaN(clientId)) {
                    return `Invalid client ID: ${toolInput.clientId}`;
                }

                const client = await db.client.findUnique({
                    where: { id: clientId },
                    include: {
                        vatPeriods: {
                            orderBy: { periodEnd: "desc" },
                            take: 1,
                            include: {
                                evidenceItems: {
                                    include: {
                                        documents: true,
                                    },
                                },
                            },
                        },
                    },
                });

                if (!client) {
                    return `Client not found with ID: ${clientId}`;
                }

                const currentPeriod = client.vatPeriods[0];
                if (!currentPeriod) {
                    return `No tax period found for client "${client.name}" (ID: ${clientId})`;
                }

                const allDocuments = currentPeriod.evidenceItems.flatMap(
                    (item: any) => item.documents
                );

                if (allDocuments.length === 0) {
                    return `No documents found for client "${client.name}" in the current tax period.`;
                }

                const statusCounts = {
                    pending: 0,
                    processing: 0,
                    extracted: 0,
                    validated: 0,
                    failed: 0,
                };

                allDocuments.forEach((doc: any) => {
                    const status = (doc.status || "pending").toLowerCase();
                    if (status in statusCounts) {
                        statusCounts[status as keyof typeof statusCounts]++;
                    }
                });

                let result = `Documents for ${client.name} (Current Tax Period):
Total: ${allDocuments.length} document(s)

Status Summary:
- Validated: ${statusCounts.validated}
- Failed: ${statusCounts.failed}
- Extracted: ${statusCounts.extracted}
- Processing: ${statusCounts.processing}
- Pending: ${statusCounts.pending}

Document List:\n${allDocuments
                    .map((d: any) => `- ${d.filename} (${d.documentType || "Unknown"}) - ${d.status || "Pending"} [ID: ${d.id}]`)
                    .join("\n")}`;

                return result;
            } catch (error) {
                return `Error fetching client documents: ${error}`;
            }

        default:
            return `Unknown tool: ${toolName}`;
    }
}

export async function POST(request: NextRequest) {
    const encoder = new TextEncoder();

    try {
        const { messages, context } = await request.json();

        // Build system prompt with context
        let systemPrompt = `You are an AI assistant for an accountant's tax compliance dashboard. You help accountants manage their clients' tax returns and documents.

You have access to tools to search for clients, documents, and tax information. Use these tools when the user asks about specific clients or documents.

IMPORTANT: When the user refers to "the document", "this document", "the client", or "this client" without specifying which one, use the context provided below to determine which client or document they're referring to.`;

        if (context) {
            if (context.current_client_id || context.current_client_name) {
                systemPrompt += `\n\nCurrent Context:
- Currently selected client: ${context.current_client_name || "Unknown"} (ID: ${context.current_client_id || "Unknown"})
When the user asks about "the client" or "this client" or their documents without specifying a name, they are referring to this client.`;
            }

            if (context.available_clients && context.available_clients.length > 0) {
                systemPrompt += `\n\nAvailable clients in the dashboard: ${context.available_clients.length} clients total.`;
            }
        }

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
                        system: systemPrompt,
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
                                    system: systemPrompt,
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
