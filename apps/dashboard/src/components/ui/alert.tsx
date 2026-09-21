import * as React from "react";
import { cn } from "@/lib/utils";

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "destructive" | "success" | "warning" | "info";
}

const variantStyles: Record<NonNullable<AlertProps["variant"]>, string> = {
  default:
    "bg-zinc-50 text-zinc-900 border-zinc-200 dark:bg-zinc-900/60 dark:text-zinc-100 dark:border-zinc-800",
  destructive:
    "border-red-200 bg-red-50/80 text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200",
  success:
    "border-emerald-200 bg-emerald-50/80 text-emerald-950 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-200",
  warning:
    "border-amber-200 bg-amber-50/80 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-200",
  info:
    "border-sky-200 bg-sky-50/80 text-sky-950 dark:border-sky-900/50 dark:bg-sky-950/40 dark:text-sky-200",
};

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <div
        ref={ref}
        role="alert"
        className={cn(
          "relative w-full rounded-xl border p-4 text-sm transition-colors",
          "[&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:h-4 [&>svg]:w-4",
          "[&>svg~*]:pl-7",
          variantStyles[variant],
          className
        )}
        {...props}
      />
    );
  }
);
Alert.displayName = "Alert";

export const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => {
  return (
    <h5
      ref={ref}
      className={cn(
        "mb-1 font-semibold leading-none tracking-tight text-xs uppercase",
        className
      )}
      {...props}
    />
  );
});
AlertTitle.displayName = "AlertTitle";

export const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn("text-xs leading-relaxed opacity-90 [&_p]:leading-relaxed", className)}
      {...props}
    />
  );
});
AlertDescription.displayName = "AlertDescription";
