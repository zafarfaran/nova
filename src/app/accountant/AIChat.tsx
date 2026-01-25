"use client";

import { useState, useRef, useEffect } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
    role: "user" | "assistant";
    content: string;
}

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

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const recognitionRef = useRef<any>(null);
    const synthRef = useRef<SpeechSynthesisUtterance | null>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

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

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        const userInput = input;
        setInput("");
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
                        ...messages.map((m) => ({
                            role: m.role,
                            content: m.content,
                        })),
                        { role: "user", content: userInput },
                    ],
                    context,
                }),
            });

            if (!response.ok) throw new Error("Failed to get response");

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = "";
            let buffer = "";

            setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

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
                                const content = data.content || data.delta?.text || "";
                                assistantMessage += content;
                                setMessages((prev) => {
                                    const newMessages = [...prev];
                                    newMessages[newMessages.length - 1] = {
                                        role: "assistant",
                                        content: assistantMessage,
                                    };
                                    return newMessages;
                                });
                            } else if (data.type === "tool_executing" || data.type === "tool_use") {
                                setCurrentToolUse(data.tool || data.name || "searching");
                            } else if (data.type === "tool_result") {
                                setCurrentToolUse(null);
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
                        const content = data.content || data.delta?.text || "";
                        assistantMessage += content;
                        setMessages((prev) => {
                            const newMessages = [...prev];
                            newMessages[newMessages.length - 1] = {
                                role: "assistant",
                                content: assistantMessage,
                            };
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
                    role: "assistant",
                    content: "Sorry, I encountered an error. Please try again.",
                },
            ]);
        } finally {
            setIsLoading(false);
            setCurrentToolUse(null);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const quickPrompts = [
        "Which clients need attention?",
        "VAT returns due this month",
        "Missing documents summary",
    ];

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
                            Ask about clients, VAT returns, or documents
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
                        {messages.map((message, index) => (
                            <div
                                key={index}
                                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                {message.role === "assistant" && (
                                    <div className="w-6 h-6 rounded-full bg-[#0052CC] flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                                        </svg>
                                    </div>
                                )}
                                <div
                                    className={`max-w-[75%] rounded-lg px-3 py-2 ${
                                        message.role === "user"
                                            ? "bg-[#0052CC] text-white"
                                            : "bg-[#F4F5F7] text-[#172B4D]"
                                    }`}
                                >
                                    <p className="whitespace-pre-wrap text-[13px] leading-relaxed">{message.content}</p>
                                </div>
                            </div>
                        ))}

                        {currentToolUse && (
                            <div className="flex justify-start">
                                <div className="w-6 h-6 rounded-full bg-[#0052CC] flex items-center justify-center mr-2 flex-shrink-0">
                                    <svg className="w-3 h-3 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                </div>
                                <div className="bg-[#FFFAE6] text-[#974F0C] px-3 py-2 rounded-lg text-[12px]">
                                    Searching: {currentToolUse}
                                </div>
                            </div>
                        )}

                        {isLoading && !currentToolUse && messages[messages.length - 1]?.role === "assistant" && messages[messages.length - 1]?.content === "" && (
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
                        className="flex-1 resize-none rounded border border-[#DFE1E6] bg-white px-3 py-2 text-[13px] text-[#172B4D] placeholder:text-[#97A0AF] focus:border-[#0052CC] focus:outline-none transition-colors"
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
