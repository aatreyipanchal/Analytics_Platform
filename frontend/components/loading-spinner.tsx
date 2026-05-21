type Props = {
  label?: string;
};

export function LoadingSpinner({ label = "Loading" }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 p-8" role="status" aria-live="polite">
      <div
        className="h-10 w-10 animate-spin rounded-full border-2 border-stone-300 border-t-orange-500"
        aria-hidden="true"
      />
      <p className="text-sm text-stone-500">{label}…</p>
    </div>
  );
}
