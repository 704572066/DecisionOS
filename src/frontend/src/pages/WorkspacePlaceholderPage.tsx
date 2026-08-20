type WorkspacePlaceholderPageProps = {
  eyebrow: string;
  title: string;
  description: string;
};

export function WorkspacePlaceholderPage({eyebrow, title, description}: WorkspacePlaceholderPageProps) {
  return <section className="workspace-placeholder">
    <span className="eyebrow">{eyebrow}</span>
    <h1>{title}</h1>
    <p>{description}</p>
  </section>;
}
