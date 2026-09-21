import React from "react";

interface CRouterLogoProps {
  className?: string;
  size?: number;
}

export function CRouterLogo({ className = "h-8 w-8", size = 32 }: CRouterLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="CRouter Logo"
    >
      {/* Container Background (shadcn dark/light responsive) */}
      <rect
        width="32"
        height="32"
        rx="7"
        className="fill-zinc-900 dark:fill-zinc-100"
      />
      {/* Precision Geometric C Path */}
      <path
        d="M22.5 10.5C21 8.2 18.3 6.8 15 6.8C9.9 6.8 6 10.9 6 16C6 21.1 9.9 25.2 15 25.2C18.4 25.2 21.2 23.7 22.7 21.3"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="stroke-white dark:stroke-zinc-950"
      />
      {/* Central Routing Switching Hub */}
      <circle cx="15" cy="16" r="2.2" fill="#10b981" />
      {/* Inbound Route Channel */}
      <path
        d="M6 16H12.8"
        strokeWidth="2"
        strokeLinecap="round"
        className="stroke-white dark:stroke-zinc-950"
      />
      {/* Route Vector Upward */}
      <path
        d="M15 13.8V11.2L18.5 8.5"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="stroke-white dark:stroke-zinc-950"
      />
      <circle cx="18.5" cy="8.5" r="1.3" className="fill-white dark:fill-zinc-950" />
      {/* Route Vector Downward */}
      <path
        d="M15 18.2V20.8L18.5 23.5"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="stroke-white dark:stroke-zinc-950"
      />
      <circle cx="18.5" cy="23.5" r="1.3" className="fill-white dark:fill-zinc-950" />
    </svg>
  );
}
