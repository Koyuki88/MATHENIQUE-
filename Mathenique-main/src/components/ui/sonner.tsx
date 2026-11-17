import { useTheme } from "next-themes";
import { Toaster as Sonner, toast } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ style, toastOptions, ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme();

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      style={{ "--width": "380px", ...style } as React.CSSProperties}
      toastOptions={{
        ...toastOptions,
        style: {
          fontSize: "1.125rem",
          padding: "16px 20px",
          borderRadius: "1rem",
          ...toastOptions?.style,
        },
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-card group-[.toaster]:text-foreground group-[.toaster]:border-2 group-[.toaster]:border-primary/25 group-[.toaster]:shadow-xl group-[.toaster]:font-fredoka group-[.toaster]:gap-3.5",
          title:
            "group-[.toast]:text-base sm:group-[.toast]:text-lg group-[.toast]:font-semibold group-[.toast]:leading-snug",
          description:
            "group-[.toast]:text-sm sm:group-[.toast]:text-base group-[.toast]:text-muted-foreground",
          icon: "group-[.toast]:!w-6 group-[.toast]:!h-6 [&>svg]:!w-6 [&>svg]:!h-6 [&>svg]:!m-0",
          success:
            "group-[.toaster]:!border-success/50 [&_[data-icon]]:!text-success",
          error:
            "group-[.toaster]:!border-destructive/50 [&_[data-icon]]:!text-destructive",
          warning:
            "group-[.toaster]:!border-warning/60 [&_[data-icon]]:!text-warning",
          actionButton: "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
          cancelButton: "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground",
          ...toastOptions?.classNames,
        },
      }}
      {...props}
    />
  );
};

export { Toaster, toast };
