"use client";

import { useState } from "react";
import {
  User,
  Key,
  Copy,
  Check,
  Shield,
  Settings as SettingsIcon,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { API_V1 } from "@/lib/utils";

export default function SettingsPage() {
  const { user, token, logout } = useAuth();
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateApiKey = async () => {
    if (!token) {
      setError("Please log in to generate an API key");
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      const response = await fetch(`${API_V1}/auth/api-key`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error("Failed to generate API key");

      const data = await response.json();
      setApiKey(data.api_key);
    } catch (err: any) {
      setError(err.message || "Failed to generate API key");
    } finally {
      setGenerating(false);
    }
  };

  const copyApiKey = async () => {
    if (apiKey) {
      await navigator.clipboard.writeText(apiKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="mt-2 text-muted-foreground">
          Manage your account and preferences
        </p>
      </div>

      {/* Profile Section */}
      <div className="glass-effect rounded-lg border border-border p-6">
        <div className="flex items-center gap-3 mb-6">
          <User className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Profile</h2>
        </div>

        {user ? (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-1">
                Name
              </label>
              <p className="text-foreground">
                {user.full_name || "Not set"}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-1">
                Email
              </label>
              <p className="text-foreground">{user.email}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-1">
                Organization
              </label>
              <p className="text-foreground">
                {user.organization || "Not set"}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-1">
                Role
              </label>
              <p className="text-foreground capitalize">{user.role}</p>
            </div>
          </div>
        ) : (
          <p className="text-muted-foreground">
            Not logged in. Please{" "}
            <a href="/login" className="text-primary hover:text-primary/80">
              sign in
            </a>{" "}
            to view your profile.
          </p>
        )}
      </div>

      {/* API Key Section */}
      <div className="glass-effect rounded-lg border border-border p-6">
        <div className="flex items-center gap-3 mb-6">
          <Key className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">API Key</h2>
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          Generate an API key for programmatic access to the DealFlow API.
          Use the header <code className="text-primary">X-API-Key: your_key</code> in requests.
        </p>

        {apiKey && (
          <div className="flex items-center gap-2 mb-4 p-3 rounded-lg bg-secondary">
            <code className="flex-1 text-sm text-foreground break-all">
              {apiKey}
            </code>
            <button
              onClick={copyApiKey}
              className="p-2 rounded hover:bg-muted transition-colors"
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-400" />
              ) : (
                <Copy className="h-4 w-4 text-muted-foreground" />
              )}
            </button>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 mb-4">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        <button
          onClick={generateApiKey}
          disabled={generating || !user}
          className="button-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {generating ? "Generating..." : "Generate New API Key"}
        </button>
      </div>

      {/* Security Section */}
      <div className="glass-effect rounded-lg border border-border p-6">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Security</h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">Session</p>
              <p className="text-xs text-muted-foreground">
                {user ? "You are currently signed in" : "Not signed in"}
              </p>
            </div>
            {user && (
              <button
                onClick={logout}
                className="button-secondary text-sm"
              >
                Sign Out
              </button>
            )}
          </div>
        </div>
      </div>

      {/* About Section */}
      <div className="glass-effect rounded-lg border border-border p-6">
        <div className="flex items-center gap-3 mb-6">
          <SettingsIcon className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">About</h2>
        </div>

        <div className="space-y-2 text-sm text-muted-foreground">
          <p>DealFlow AI Copilot</p>
          <p>AI-powered private equity deal analysis platform</p>
          <p>Powered by Google Gemini</p>
        </div>
      </div>
    </div>
  );
}
