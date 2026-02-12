type Props = {
  message: string;
  visible: boolean;
};

export default function LoadingOverlay({ message, visible }: Props) {
  if (!visible) return null;
  return (
    <div className="overlay">
      <div className="overlay__backdrop" />
      <div className="overlay__content">
        <div className="overlay__spinner" aria-hidden="true" />
        <div className="overlay__message">{message}</div>
      </div>
    </div>
  );
}
