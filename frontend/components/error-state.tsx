interface ErrorStateProps {
  message?: string;
}

export function ErrorState({ message = "Something went wrong. Please try again later." }: ErrorStateProps) {
  return (
    <div className="text-center py-8 text-muted-foreground">
      <p>{message}</p>
    </div>
  );
}