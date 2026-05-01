"use client";

type Props = {
  className?: string;
  withWordmark?: boolean;
};

export function Logo({ className = "h-7 w-7", withWordmark = false }: Props) {
  const wreath = (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      className={className}
      aria-hidden
    >
      {/* Left branch stem */}
      <path
        d="M 32 56 C 16 52, 7 38, 10 21 C 13 11, 21 6, 28 5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        fill="none"
      />
      {/* Left leaves */}
      <g fill="currentColor">
        <ellipse cx="22" cy="50" rx="4.5" ry="1.8" transform="rotate(-78 22 50)" />
        <ellipse cx="14" cy="42" rx="4.8" ry="1.9" transform="rotate(-58 14 42)" />
        <ellipse cx="10" cy="32" rx="5" ry="2" transform="rotate(-32 10 32)" />
        <ellipse cx="11" cy="20" rx="4.8" ry="1.9" transform="rotate(-10 11 20)" />
        <ellipse cx="18" cy="11" rx="4.6" ry="1.8" transform="rotate(20 18 11)" />
      </g>

      {/* Right branch stem */}
      <path
        d="M 32 56 C 48 52, 57 38, 54 21 C 51 11, 43 6, 36 5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        fill="none"
      />
      {/* Right leaves */}
      <g fill="currentColor">
        <ellipse cx="42" cy="50" rx="4.5" ry="1.8" transform="rotate(78 42 50)" />
        <ellipse cx="50" cy="42" rx="4.8" ry="1.9" transform="rotate(58 50 42)" />
        <ellipse cx="54" cy="32" rx="5" ry="2" transform="rotate(32 54 32)" />
        <ellipse cx="53" cy="20" rx="4.8" ry="1.9" transform="rotate(10 53 20)" />
        <ellipse cx="46" cy="11" rx="4.6" ry="1.8" transform="rotate(-20 46 11)" />
      </g>

      {/* Knot at the base */}
      <circle cx="32" cy="56" r="2.2" fill="currentColor" />
    </svg>
  );

  if (!withWordmark) return wreath;

  return (
    <div className="flex items-center gap-2">
      <span className="text-magnus-700">{wreath}</span>
      <span className="text-xl font-semibold tracking-tight text-stone-900">
        Magnus
      </span>
    </div>
  );
}
