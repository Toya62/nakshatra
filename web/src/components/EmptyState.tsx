"use client";

import React from "react";
import { LucideIcon } from "lucide-react";

interface Props {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<Props> = ({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <div
      className="card"
      style={{
        padding: "var(--space-12) var(--space-6)",
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "var(--space-3)",
        maxWidth: "600px",
        margin: "0 auto",
        width: "100%",
      }}
    >
      <div
        style={{
          width: "56px",
          height: "56px",
          borderRadius: "50%",
          background: "rgba(229, 185, 76, 0.08)",
          border: "1px solid var(--gold-border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--gold-vivid)",
          marginBottom: "var(--space-2)",
        }}
        aria-hidden="true"
      >
        <Icon size={26} strokeWidth={1.75} />
      </div>

      <h3 style={{ fontSize: "var(--type-heading)", fontWeight: 700, color: "var(--text-high)" }}>
        {title}
      </h3>

      <p style={{ fontSize: "var(--type-body)", color: "var(--text-mid)", maxWidth: "420px", lineHeight: 1.55 }}>
        {description}
      </p>

      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="btn-primary"
          style={{ marginTop: "var(--space-2)" }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};
