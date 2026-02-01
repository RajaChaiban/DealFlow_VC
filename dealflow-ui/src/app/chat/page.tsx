"use client";

import { useState, useEffect, useRef } from "react";
import {
  Send,
  Plus,
  MessageSquare,
  Sparkles,
  Loader2,
  History,
  Trash2,
} from "lucide-react";
import { ChatMessage } from "@/types";
import { API_V1 } from "@/lib/utils";

interface SessionListItem {
  session_id: string;
  analysis_id?: string;
  message_count: number;
  created_at: string;
}

interface ActiveSession {
  session_id: string;
  title: string;
  messages: ChatMessage[];
  analysis_id?: string;
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [activeSession?.messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchSessions = async () => {
    try {
      const response = await fetch(`${API_V1}/chat/sessions`);
      if (!response.ok) return;

      const data = await response.json();
      const sessionList: SessionListItem[] = data.sessions || [];
      setSessions(sessionList);
    } catch (error) {
      console.error("Failed to fetch chat sessions:", error);
    }
  };

  const loadSessionHistory = async (sessionId: string) => {
    try {
      const response = await fetch(`${API_V1}/chat/${sessionId}/history`);
      if (!response.ok) return;

      const data = await response.json();
      setActiveSession({
        session_id: sessionId,
        title: `Chat ${sessionId}`,
        messages: (data.messages || []).map((m: any) => ({
          role: m.role,
          content: m.content,
          timestamp: m.timestamp || new Date().toISOString(),
        })),
        analysis_id: data.analysis_id,
      });
    } catch (error) {
      console.error("Failed to load session history:", error);
    }
  };

  const createNewSession = () => {
    setActiveSession({
      session_id: "",
      title: "New Conversation",
      messages: [],
    });
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await fetch(`${API_V1}/chat/${sessionId}`, {
        method: "DELETE",
      });

      const updatedSessions = sessions.filter((s) => s.session_id !== sessionId);
      setSessions(updatedSessions);

      if (activeSession?.session_id === sessionId) {
        setActiveSession(null);
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !activeSession) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    // Update UI immediately
    const updatedMessages = [...activeSession.messages, userMessage];
    setActiveSession({ ...activeSession, messages: updatedMessages });
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_V1}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          session_id: activeSession.session_id || undefined,
          analysis_id: selectedDeal || undefined,
        }),
      });

      if (!response.ok) throw new Error("Chat request failed");

      const data = await response.json();

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.response,
        timestamp: new Date().toISOString(),
      };

      const newSession: ActiveSession = {
        ...activeSession,
        session_id: data.session_id || activeSession.session_id,
        messages: [...updatedMessages, assistantMessage],
        title:
          activeSession.messages.length === 0
            ? input.slice(0, 30) + "..."
            : activeSession.title,
      };

      setActiveSession(newSession);

      // If this was a new session, refresh the session list
      if (!activeSession.session_id && data.session_id) {
        fetchSessions();
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: "Sorry, I encountered an error processing your message. Please try again.",
        timestamp: new Date().toISOString(),
      };
      setActiveSession({
        ...activeSession,
        messages: [...updatedMessages, errorMessage],
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestedQuestions = [
    "What are the key risks in the latest deal?",
    "Compare valuation metrics across recent deals",
    "Summarize financial projections for Deal X",
    "What market trends affect this portfolio?",
  ];

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-6">
      {/* Sessions Sidebar */}
      <div className="w-80 flex-shrink-0 glass-effect rounded-lg border border-border flex flex-col">
        <div className="border-b border-border p-4">
          <button
            onClick={createNewSession}
            className="button-primary w-full flex items-center justify-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center px-4">
              <MessageSquare className="h-12 w-12 text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">
                No conversations yet
              </p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.session_id}
                className={`group rounded-lg p-3 cursor-pointer transition-all ${
                  activeSession?.session_id === session.session_id
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-secondary"
                }`}
                onClick={() => loadSessionHistory(session.session_id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm truncate mb-1">
                      Chat {session.session_id}
                    </h3>
                    <div className="flex items-center gap-2 text-xs opacity-70">
                      <History className="h-3 w-3" />
                      <span>
                        {new Date(session.created_at).toLocaleDateString()}
                      </span>
                      <span>{session.message_count} msgs</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(session.session_id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20 transition-all"
                  >
                    <Trash2 className="h-4 w-4 text-red-400" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 glass-effect rounded-lg border border-border flex flex-col">
        {/* Chat Header */}
        <div className="border-b border-border p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary/20 p-2">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-foreground">
                {activeSession?.title || "Select a conversation"}
              </h2>
              <p className="text-xs text-muted-foreground">
                Ask questions about your deals
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">Analysis ID:</label>
            <input
              type="text"
              value={selectedDeal}
              onChange={(e) => setSelectedDeal(e.target.value)}
              placeholder="Optional"
              className="input-field text-sm w-40"
            />
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!activeSession || activeSession.messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="rounded-full bg-primary/20 p-6 mb-6">
                <Sparkles className="h-12 w-12 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Start a conversation
              </h3>
              <p className="text-muted-foreground mb-8 text-center max-w-md">
                Ask questions about your deals, compare metrics, or get insights
                from your portfolio
              </p>

              <div className="grid grid-cols-2 gap-3 w-full max-w-2xl">
                {suggestedQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      if (!activeSession) createNewSession();
                      setInput(question);
                    }}
                    className="glass-effect border border-border rounded-lg p-4 text-left hover:border-primary/50 transition-all text-sm text-muted-foreground hover:text-foreground"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {activeSession.messages.map((message, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {message.role === "assistant" && (
                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                      <Sparkles className="h-4 w-4 text-primary" />
                    </div>
                  )}

                  <div
                    className={`max-w-[70%] rounded-lg p-4 ${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "glass-effect border border-border"
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>
                    <p
                      className={`text-xs mt-2 ${
                        message.role === "user"
                          ? "text-primary-foreground/70"
                          : "text-muted-foreground"
                      }`}
                    >
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </p>
                  </div>

                  {message.role === "user" && (
                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-secondary flex items-center justify-center">
                      <span className="text-xs font-semibold text-foreground">
                        You
                      </span>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex gap-3">
                  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                    <Sparkles className="h-4 w-4 text-primary" />
                  </div>
                  <div className="glass-effect border border-border rounded-lg p-4">
                    <Loader2 className="h-5 w-5 text-primary animate-spin" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-border p-4">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask a question about your deals..."
                disabled={loading || !activeSession}
                rows={1}
                className="input-field w-full resize-none pr-12 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || loading || !activeSession}
                className="absolute right-2 top-1/2 -translate-y-1/2 button-primary p-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {activeSession &&
              activeSession.messages.length === 0 &&
              suggestedQuestions.slice(0, 2).map((question, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(question)}
                  className="text-xs px-3 py-1.5 rounded-full border border-border hover:border-primary/50 text-muted-foreground hover:text-foreground transition-all"
                >
                  {question}
                </button>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
