"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ClientFlowDiagram, getClientStage } from "./components/ClientFlowDiagram";
import type { FlowStage } from "./components/ClientFlowDiagram";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type TextMessage = {
    id: string;
    kind: "text";
    role: "user" | "assistant";
    content: string;
};

type ToolMessage = {
    id: string;
    kind: "tool";
    role: "tool";
    toolName: string;
    toolInput?: Record<string, any>;
    toolResult?: any;
};

type FormMessage = {
    id: string;
    kind: "create_client_form";
    role: "assistant";
};

type Message = TextMessage | ToolMessage | FormMessage;

interface AIChatProps {
    clientId?: string;
    clientName?: string;
    allClients?: { id: string; name: string; email: string }[];
}

export function AIChat({ clientId, clientName, allClients }: AIChatProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [voiceEnabled, setVoiceEnabled] = useState(false);
    const [currentToolUse, setCurrentToolUse] = useState<string | null>(null);

    const assistantMessageIndexRef = useRef<number | null>(null);
    const toolInputMapRef = useRef<Map<string, any>>(new Map());

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const recognitionRef = useRef<any>(null);
    const synthRef = useRef<SpeechSynthesisUtterance | null>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const makeId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

    const shouldShowCreateClientForm = (text: string) => {
        return /(create|add|new)\s+(client|user)/i.test(text);
    };

    // Initialize Speech Recognition
    useEffect(() => {
        if (typeof window !== "undefined" && "webkitSpeechRecognition" in window) {
            const SpeechRecognition = (window as any).webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = false;
            recognitionRef.current.interimResults = false;

            recognitionRef.current.onresult = (event: any) => {
                const transcript = event.results[0][0].transcript;
                setInput(transcript);
                setIsListening(false);
            };

            recognitionRef.current.onerror = () => {
                setIsListening(false);
            };

            recognitionRef.current.onend = () => {
                setIsListening(false);
            };
        }
    }, []);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Auto-resize textarea
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = "auto";
            inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + "px";
        }
    }, [input]);

    const speak = (text: string) => {
        if (!voiceEnabled || !window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        synthRef.current = utterance;
        window.speechSynthesis.speak(utterance);
    };

    const startListening = () => {
        if (recognitionRef.current && !isListening) {
            setIsListening(true);
            recognitionRef.current.start();
        }
    };

    const stopListening = () => {
        if (recognitionRef.current && isListening) {
            recognitionRef.current.stop();
            setIsListening(false);
        }
    };

    const sendMessageWithContent = async (content: string) => {
        if (!content.trim() || isLoading) return;

        const userMessage: Message = { id: makeId(), kind: "text", role: "user", content };
        const assistantPlaceholder: Message = { id: makeId(), kind: "text", role: "assistant", content: "" };

        setMessages((prev) => {
            const next = [...prev, userMessage, assistantPlaceholder];
            assistantMessageIndexRef.current = next.length - 1;
            return next;
        });
        setIsLoading(true);

        try {
            // Build context for the AI
            const context: Record<string, any> = {};
            if (clientId) {
                context.current_client_id = clientId;
            }
            if (clientName) {
                context.current_client_name = clientName;
            }
            if (allClients && allClients.length > 0) {
                context.available_clients = allClients;
            }

            const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    messages: [
                        ...messages
                            .filter((m) => m.kind === "text")
                            .map((m) => ({
                                role: m.role,
                                content: m.content,
                            })),
                        { role: "user", content },
                    ],
                    context,
                }),
            });

            if (!response.ok) throw new Error("Failed to get response");

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = "";
            let buffer = "";

            while (true) {
                const { done, value } = (await reader?.read()) || {};
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (trimmedLine.startsWith("data: ")) {
                        const jsonStr = trimmedLine.slice(6);
                        if (jsonStr === "[DONE]") continue;

                        try {
                            const data = JSON.parse(jsonStr);

                            if (data.type === "text" || data.type === "content_block_delta") {
                                const deltaText = data.content || data.delta?.text || "";
                                assistantMessage += deltaText;
                                setMessages((prev) => {
                                    const newMessages = [...prev];
                                    const idx = assistantMessageIndexRef.current;
                                    if (idx !== null && newMessages[idx]?.kind === "text") {
                                        newMessages[idx] = {
                                            ...(newMessages[idx] as TextMessage),
                                            content: assistantMessage,
                                        };
                                    }
                                    return newMessages;
                                });
                            } else if (data.type === "tool_executing" || data.type === "tool_use") {
                                setCurrentToolUse(data.tool || data.name || "searching");
                                if (data.tool_call_id) {
                                    toolInputMapRef.current.set(data.tool_call_id, data.input || {});
                                }
                            } else if (data.type === "tool_result") {
                                setCurrentToolUse(null);
                                const toolInput = data.tool_call_id
                                    ? toolInputMapRef.current.get(data.tool_call_id)
                                    : undefined;
                                if (data.tool_call_id) {
                                    toolInputMapRef.current.delete(data.tool_call_id);
                                }
                                setMessages((prev) => [
                                    ...prev,
                                    {
                                        id: makeId(),
                                        kind: "tool",
                                        role: "tool",
                                        toolName: data.tool || "tool",
                                        toolInput,
                                        toolResult: data.result,
                                    },
                                ]);
                            } else if (data.type === "message_stop" || data.type === "done") {
                                if (voiceEnabled && assistantMessage) {
                                    speak(assistantMessage);
                                }
                            }
                        } catch (e) {
                            // Partial JSON, will be handled in next iteration
                        }
                    }
                }
            }

            // Process any remaining buffer
            if (buffer.trim().startsWith("data: ")) {
                try {
                    const data = JSON.parse(buffer.trim().slice(6));
                    if (data.type === "text" || data.type === "content_block_delta") {
                        const deltaText = data.content || data.delta?.text || "";
                        assistantMessage += deltaText;
                        setMessages((prev) => {
                            const newMessages = [...prev];
                            const idx = assistantMessageIndexRef.current;
                            if (idx !== null && newMessages[idx]?.kind === "text") {
                                newMessages[idx] = {
                                    ...(newMessages[idx] as TextMessage),
                                    content: assistantMessage,
                                };
                            }
                            return newMessages;
                        });
                    }
                } catch (e) {
                    // Ignore
                }
            }
        } catch (error) {
            console.error("Error:", error);
            setMessages((prev) => [
                ...prev,
                {
                    id: makeId(),
                    kind: "text",
                    role: "assistant",
                    content: "Sorry, I encountered an error. Please try again.",
                },
            ]);
        } finally {
            setIsLoading(false);
            setCurrentToolUse(null);
        }
    };

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userInput = input;
        setInput("");

        if (shouldShowCreateClientForm(userInput)) {
            const userMessage: Message = { id: makeId(), kind: "text", role: "user", content: userInput };
            const assistantMessage: Message = {
                id: makeId(),
                kind: "text",
                role: "assistant",
                content: "Love it. Pop the details in this quick form and I’ll set them up ✨",
            };
            const formMessage: Message = {
                id: makeId(),
                kind: "create_client_form",
                role: "assistant",
            };
            setMessages((prev) => [...prev, userMessage, assistantMessage, formMessage]);
            return;
        }

        await sendMessageWithContent(userInput);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const quickPrompts = [
        "Which clients need attention?",
        "Tax returns due this month",
        "Missing documents summary",
        "Create a new client",
    ];

    const lastMessage = messages[messages.length - 1];
    const showTypingIndicator =
        isLoading &&
        !currentToolUse &&
        lastMessage?.kind === "text" &&
        lastMessage.role === "assistant" &&
        lastMessage.content === "";

    const CreateClientFormCard = ({ onSubmit, onCancel }: { onSubmit: (payload: string) => void; onCancel: () => void }) => {
        const [name, setName] = useState("");
        const [email, setEmail] = useState("");
        const [entityType, setEntityType] = useState("limited_company");
        const [vatScheme, setVatScheme] = useState("standard");
        const [vatNumber, setVatNumber] = useState("");
        const [notes, setNotes] = useState("");

        const handleSubmit = () => {
            if (!name.trim() || !email.trim()) return;
            const message = [
                "Please create a new client with the following details:",
                `Name: ${name}`,
                `Email: ${email}`,
                `Entity type: ${entityType}`,
                `Tax scheme: ${vatScheme}`,
                vatNumber ? `Tax number: ${vatNumber}` : null,
                notes ? `Notes: ${notes}` : null,
            ]
                .filter(Boolean)
                .join("\n");

            onSubmit(message);
        };

        return (
            <div className="rounded-lg border border-[#C0B6F2] bg-gradient-to-br from-[#F4F5F7] to-[#EAE6FF] p-4">
                <div className="flex items-center gap-2 mb-3">
                    <span className="text-[14px]">✨</span>
                    <div>
                        <p className="text-[13px] font-semibold text-[#403294]">New Client Capsule</p>
                        <p className="text-[11px] text-[#5E6C84]">Drop the details and I’ll handle the rest.</p>
                    </div>
                </div>
                <div className="grid gap-2">
                    <input
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Client name"
                        className="w-full rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D]"
                    />
                    <input
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Email"
                        className="w-full rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D]"
                    />
                    <div className="grid grid-cols-2 gap-2">
                        <select
                            value={entityType}
                            onChange={(e) => setEntityType(e.target.value)}
                            className="rounded border border-[#DFE1E6] bg-white px-2 py-2 text-[12px] text-[#172B4D]"
                        >
                            <option value="sole_trader">Sole Trader</option>
                            <option value="partnership">Partnership</option>
                            <option value="llp">LLP</option>
                            <option value="limited_company">Limited Company</option>
                            <option value="plc">PLC</option>
                            <option value="charity">Charity</option>
                            <option value="other">Other</option>
                        </select>
                        <select
                            value={vatScheme}
                            onChange={(e) => setVatScheme(e.target.value)}
                            className="rounded border border-[#DFE1E6] bg-white px-2 py-2 text-[12px] text-[#172B4D]"
                        >
                            <option value="standard">Standard</option>
                            <option value="flat_rate">Flat Rate</option>
                            <option value="cash_accounting">Cash Accounting</option>
                            <option value="annual_accounting">Annual Accounting</option>
                        </select>
                    </div>
                    <input
                        value={vatNumber}
                        onChange={(e) => setVatNumber(e.target.value)}
                        placeholder="Tax number (optional)"
                        className="w-full rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D]"
                    />
                    <textarea
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Notes (optional)"
                        className="w-full rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D]"
                        rows={2}
                    />
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleSubmit}
                            disabled={!name.trim() || !email.trim() || isLoading}
                            className="rounded bg-[#6554C0] px-3 py-2 text-[12px] font-semibold text-white disabled:opacity-50"
                        >
                            Create client
                        </button>
                        <button
                            onClick={onCancel}
                            className="rounded border border-[#DFE1E6] px-3 py-2 text-[12px] text-[#5E6C84]"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        );
    };

    const ToolCard = ({ children }: { children: React.ReactNode }) => (
        <div className="rounded-xl border border-[#DFE1E6] bg-[#FAFBFC] p-4 shadow-sm">
            <div className="text-[12px] text-[#172B4D] leading-relaxed">{children}</div>
        </div>
    );

    const renderToolResult = (message: ToolMessage) => {
        const result = message.toolResult || {};
        if (result.error) {
            return (
                <ToolCard>
                    <p className="text-[12px] font-semibold text-[#BF2600]">Tool error</p>
                    <p className="text-[11px] text-[#5E6C84]">{result.error}</p>
                </ToolCard>
            );
        }

        if (message.toolName === "create_client") {
            return (
                <ToolCard>
                    <p className="text-[13px] font-semibold text-[#172B4D]">Client created</p>
                    <p className="text-[12px] text-[#5E6C84]">{result.message}</p>
                    {result.client && (
                        <div className="mt-2 text-[12px] text-[#172B4D]">
                            <div className="font-medium">{result.client.name}</div>
                            <div className="text-[#5E6C84]">{result.client.email}</div>
                        </div>
                    )}
                    {result.onboarding_link && (
                        <button
                            onClick={() => window.open(result.onboarding_link, "_blank")}
                            className="mt-2 text-[11px] font-semibold text-[#0052CC] hover:text-[#0747A6]"
                        >
                            Open onboarding link
                        </button>
                    )}
                </ToolCard>
            );
        }

        if (message.toolName === "list_clients" || message.toolName === "search_clients") {
            const clients = result.clients || [];
            return (
                <ToolCard>
                    <p className="text-[13px] font-semibold text-[#172B4D]">
                        {result.total ?? clients.length} client{(result.total ?? clients.length) !== 1 ? "s" : ""}
                    </p>
                    <div className="mt-2 space-y-2">
                        {clients.map((client: any) => (
                            <div key={client.id} className="border border-[#EBECF0] rounded-lg bg-white px-3 py-2">
                                <div className="text-[12px] text-[#172B4D] font-semibold">{client.name}</div>
                                <div className="text-[11px] text-[#5E6C84]">{client.email}</div>
                                <div className="text-[10px] text-[#97A0AF] uppercase tracking-wide">
                                    {client.entity_type || "entity"} • {client.vat_scheme || "scheme"}
                                </div>
                            </div>
                        ))}
                        {clients.length === 0 && (
                            <p className="text-[11px] text-[#5E6C84]">No clients found.</p>
                        )}
                    </div>
                </ToolCard>
            );
        }

        if (message.toolName === "get_client_details") {
            const docs = result.documents || {};
            const hasBank = result.has_bank_connected || false;
            const stage = getClientStage({
                documentsUploaded: docs.uploaded || 0,
                documentsRequired: docs.total_required || 0,
                hasBankConnection: hasBank,
                status: docs.uploaded === docs.total_required ? "complete" : "needs_attention",
            });
            return (
                <ToolCard>
                    <p className="text-[13px] font-semibold text-[#172B4D]">{result.client?.name}</p>
                    <p className="text-[11px] text-[#5E6C84]">{result.client?.email}</p>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-[12px] text-[#172B4D]">
                        <div>
                            Docs: {docs.uploaded}/{docs.total_required}
                        </div>
                        <div>Bank: {hasBank ? "Connected" : "Not linked"}</div>
                    </div>
                    <div className="mt-3 rounded-lg bg-white p-2">
                        <ClientFlowDiagram currentStage={stage} variant="horizontal" />
                    </div>
                </ToolCard>
            );
        }

        if (message.toolName === "get_document_checklist") {
            const checklist = result.checklist || [];
            const summary = result.summary || {};
            const docsRequired = summary.required_items ?? summary.total_items ?? 0;
            const docsUploaded = summary.uploaded ?? 0;
            const hasBank =
                typeof result.has_bank_connected === "boolean" ? result.has_bank_connected : undefined;
            const stage = getClientStage({
                documentsUploaded: docsUploaded,
                documentsRequired: docsRequired,
                hasBankConnection: hasBank ?? false,
                status: docsUploaded === docsRequired ? "complete" : "needs_attention",
            });
            return (
                <ToolCard>
                    <p className="text-[13px] font-semibold text-[#172B4D]">{result.client_name}</p>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-[12px] text-[#172B4D]">
                        <div>
                            Docs: {docsUploaded}/{docsRequired}
                        </div>
                        <div>
                            Bank: {hasBank === undefined ? "Unknown" : hasBank ? "Connected" : "Not linked"}
                        </div>
                    </div>
                    <div className="mt-3 rounded-lg bg-white p-2">
                        <ClientFlowDiagram currentStage={stage} variant="horizontal" />
                    </div>
                    {checklist.length > 0 && (
                        <details className="mt-3">
                            <summary className="cursor-pointer text-[11px] font-semibold text-[#0052CC]">
                                View checklist
                            </summary>
                            <div className="mt-2 space-y-1">
                                {checklist.map((item: any) => (
                                    <div
                                        key={item.id}
                                        className="flex items-center justify-between text-[12px] rounded bg-white px-2 py-1"
                                    >
                                        <span className="text-[#172B4D]">{item.title}</span>
                                        <span className="text-[#5E6C84]">{item.status_icon}</span>
                                    </div>
                                ))}
                            </div>
                        </details>
                    )}
                </ToolCard>
            );
        }

        if (message.toolName === "get_clients_needing_attention") {
            const clients = result.clients_needing_attention || [];
            return (
                <ToolCard>
                    <p className="text-[13px] font-semibold text-[#172B4D]">{result.message}</p>
                    <div className="mt-2 space-y-3">
                        {clients.map((client: any) => {
                            const stage = getClientStage({
                                documentsUploaded: client.documents_uploaded || 0,
                                documentsRequired: client.documents_required || 0,
                                hasBankConnection: client.has_bank_connection || false,
                                status: client.vat_period_status || "needs_attention",
                                hasFailedValidations: client.has_failed_validations || false,
                                hasPendingReviews: client.has_pending_reviews || false,
                            });
                            const failedStages: FlowStage[] =
                                client.has_pending_reviews || client.has_failed_validations
                                    ? ["verification"]
                                    : [];
                            const attentionBits: string[] = [];
                            if ((client.validation_issue_count || 0) > 0) {
                                attentionBits.push(`Validation docs: ${client.validation_issue_count}`);
                            }
                            if ((client.pending_review_count || 0) > 0) {
                                attentionBits.push(`Pending review docs: ${client.pending_review_count}`);
                            }
                            if (client.vat_period_status === "under_review") {
                                attentionBits.push("Under review");
                            }
                            return (
                                <div key={client.id} className="border border-[#EBECF0] rounded-lg bg-white p-3">
                                    <div className="text-[12px] font-semibold text-[#172B4D]">{client.name}</div>
                                    <div className="text-[11px] text-[#5E6C84]">{client.email}</div>
                                    {client.missing_documents > 0 && (
                                        <div className="text-[11px] text-[#BF2600] mt-1">
                                            Missing: {client.missing_documents}
                                            {client.missing_items?.length
                                                ? ` • ${client.missing_items.join(", ")}`
                                                : ""}
                                        </div>
                                    )}
                                    {attentionBits.length > 0 && (
                                        <div className="text-[11px] text-[#6B778C] mt-1">
                                            {attentionBits.join(" • ")}
                                        </div>
                                    )}
                                    <div className="mt-3 rounded-lg bg-[#F4F5F7] p-2">
                                        <ClientFlowDiagram
                                            currentStage={stage}
                                            variant="horizontal"
                                            failedStages={failedStages}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </ToolCard>
            );
        }

        if (message.toolName === "update_checklist_item") {
            return (
                <ToolCard>
                    <p className="text-[13px] font-semibold text-[#172B4D]">{result.message}</p>
                </ToolCard>
            );
        }

        return (
            <ToolCard>
                <p className="text-[12px] font-semibold text-[#172B4D]">{message.toolName}</p>
                <pre className="text-[10px] text-[#5E6C84] mt-2 whitespace-pre-wrap">
                    {JSON.stringify(result, null, 2)}
                </pre>
            </ToolCard>
        );
    };

    return (
        <div className="flex h-full flex-col bg-white">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                {messages.length === 0 ? (
                    <div className="flex h-full flex-col items-center justify-center p-6">
                        <div className="w-10 h-10 rounded-full bg-[#DEEBFF] flex items-center justify-center mb-4">
                            <svg className="w-5 h-5 text-[#0052CC]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                            </svg>
                        </div>
                        <h3 className="text-[15px] font-semibold text-[#172B4D] mb-1">How can I help?</h3>
                        <p className="text-[12px] text-[#5E6C84] text-center mb-6">
                            Ask about clients, tax returns, or documents
                        </p>

                        {/* Quick prompts */}
                        <div className="flex flex-col gap-2 w-full max-w-[280px]">
                            {quickPrompts.map((prompt, i) => (
                                <button
                                    key={i}
                                    onClick={() => setInput(prompt)}
                                    className="text-left px-3 py-2 text-[12px] text-[#172B4D] bg-[#F4F5F7] hover:bg-[#EBECF0] rounded transition-colors"
                                >
                                    {prompt}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="p-4 space-y-3">
                        {messages.map((message) => {
                            if (message.kind === "tool") {
                                return (
                                    <div key={message.id} className="flex justify-start">
                                        <div className="w-6 h-6 rounded-full bg-white border border-[#DFE1E6] flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                                            <img src="/logo.svg" alt="Nova" className="h-4 w-4" />
                                        </div>
                                        <div className="max-w-[85%]">
                                            {renderToolResult(message)}
                                        </div>
                                    </div>
                                );
                            }

                            if (message.kind === "create_client_form") {
                                return (
                                    <div key={message.id} className="flex justify-start">
                                        <div className="w-6 h-6 rounded-full bg-[#6554C0] flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                                            <span className="text-white text-[11px]">✨</span>
                                        </div>
                                        <div className="max-w-[85%]">
                                            <CreateClientFormCard
                                                onSubmit={async (payload) => {
                                                    setMessages((prev) => prev.filter((m) => m.id !== message.id));
                                                    await sendMessageWithContent(payload);
                                                }}
                                                onCancel={() => {
                                                    setMessages((prev) => prev.filter((m) => m.id !== message.id));
                                                }}
                                            />
                                        </div>
                                    </div>
                                );
                            }

                            return (
                                <div
                                    key={message.id}
                                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                                >
                                    {message.role === "assistant" && (
                                        <div className="w-6 h-6 rounded-full bg-white border border-[#DFE1E6] flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                                            <img src="/logo.svg" alt="Nova" className="h-4 w-4" />
                                        </div>
                                    )}
                                    <div
                                        className={`max-w-[75%] rounded-lg px-3 py-2 ${
                                            message.role === "user"
                                                ? "bg-[#0052CC] text-white"
                                                : "bg-[#F4F5F7] text-[#172B4D]"
                                        }`}
                                    >
                                        {message.role === "assistant" ? (
                                            <div className="prose prose-sm max-w-none text-[12px] leading-relaxed prose-p:my-1.5 prose-li:my-1 prose-ul:my-2 prose-ol:my-2 prose-strong:text-inherit">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {message.content}
                                                </ReactMarkdown>
                                            </div>
                                        ) : (
                                            <p className="whitespace-pre-wrap text-[12px] leading-relaxed">{message.content}</p>
                                        )}
                                    </div>
                                </div>
                            );
                        })}

                        {currentToolUse && (
                            <div className="flex justify-start">
                                <div className="w-6 h-6 rounded-full bg-white border border-[#DFE1E6] flex items-center justify-center mr-2 flex-shrink-0">
                                    <img src="/logo.svg" alt="Nova" className="h-4 w-4" />
                                </div>
                                <div className="bg-[#FFFAE6] text-[#974F0C] px-3 py-2 rounded-lg text-[11px]">
                                    Searching: {currentToolUse}
                                </div>
                            </div>
                        )}

                        {showTypingIndicator && (
                            <div className="flex justify-start">
                                <div className="w-6 h-6 rounded-full bg-[#0052CC] flex items-center justify-center mr-2 flex-shrink-0">
                                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                                    </svg>
                                </div>
                                <div className="bg-[#F4F5F7] px-3 py-2 rounded-lg">
                                    <div className="flex gap-1">
                                        <span className="w-1.5 h-1.5 bg-[#5E6C84] rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                        <span className="w-1.5 h-1.5 bg-[#5E6C84] rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                        <span className="w-1.5 h-1.5 bg-[#5E6C84] rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="border-t border-[#DFE1E6] p-3 bg-[#FAFBFC]">
                {isListening && (
                    <div className="flex items-center gap-2 mb-2">
                        <span className="w-1.5 h-1.5 bg-[#DE350B] rounded-full animate-pulse" />
                        <span className="text-[11px] text-[#DE350B]">Listening...</span>
                    </div>
                )}

                <div className="flex items-center gap-2">
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask a question..."
                        className="flex-1 resize-none rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[12px] text-[#172B4D] placeholder:text-[#97A0AF] focus:border-[#0052CC] focus:outline-none transition-colors"
                        rows={1}
                        disabled={isLoading}
                        style={{ height: "36px" }}
                    />

                    <button
                        onClick={isListening ? stopListening : startListening}
                        disabled={isLoading}
                        className={`w-8 h-8 flex items-center justify-center rounded transition-colors ${
                            isListening
                                ? "bg-[#DE350B] text-white"
                                : "text-[#97A0AF] hover:text-[#172B4D]"
                        } disabled:opacity-50`}
                        title={isListening ? "Stop" : "Voice"}
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                    </button>

                    <button
                        onClick={() => setVoiceEnabled(!voiceEnabled)}
                        className={`w-8 h-8 flex items-center justify-center rounded transition-colors ${
                            voiceEnabled
                                ? "text-[#36B37E]"
                                : "text-[#97A0AF] hover:text-[#172B4D]"
                        }`}
                        title={voiceEnabled ? "Voice on" : "Voice off"}
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                            {voiceEnabled ? (
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                            ) : (
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                            )}
                        </svg>
                    </button>

                    <button
                        onClick={sendMessage}
                        disabled={!input.trim() || isLoading}
                        className="w-8 h-8 flex items-center justify-center rounded bg-[#0052CC] text-white hover:bg-[#0747A6] transition-colors disabled:opacity-30"
                        title="Send"
                    >
                        {isLoading ? (
                            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                        ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                            </svg>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
