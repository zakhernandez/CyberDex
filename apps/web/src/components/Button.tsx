import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost";

const variantClasses: Record<Variant, string> = {
  primary:
    "border border-primary text-primary hover:bg-primary hover:text-background",
  secondary:
    "border border-border-strong text-foreground hover:border-primary hover:text-primary",
  ghost:
    "text-foreground-muted hover:text-primary",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  children: ReactNode;
}

export function Button({
  variant = "primary",
  className = "",
  children,
  ...rest
}: ButtonProps) {
  const base =
    "inline-flex items-center gap-2 px-4 py-2 font-mono text-sm uppercase tracking-wide transition-colors duration-[var(--duration-med)] ease-[var(--ease-sharp)] cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed";
  return (
    <button
      className={`${base} ${variantClasses[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}