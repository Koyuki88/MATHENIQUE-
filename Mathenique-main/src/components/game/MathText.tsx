import { Fragment, ReactNode } from "react";

const EXPONENT_RE = /\^(?:\{([^}]+)\}|\(([^)]+)\)|(-?\d+)|([a-zA-Z]))/g;

function renderMathNodes(text: string): ReactNode {
  if (!text.includes("^")) {
    return text;
  }

  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  EXPONENT_RE.lastIndex = 0;
  while ((match = EXPONENT_RE.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(
        <Fragment key={`t-${key++}`}>{text.slice(lastIndex, match.index)}</Fragment>
      );
    }

    const exponent = match[1] ?? match[2] ?? match[3] ?? match[4] ?? "";
    nodes.push(
      <sup
        key={`e-${key++}`}
        className="text-[0.7em] font-bold leading-none relative -top-[0.42em] mx-[0.5px]"
      >
        {exponent.includes("^") ? renderMathNodes(exponent) : exponent}
      </sup>
    );

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    nodes.push(<Fragment key={`t-${key++}`}>{text.slice(lastIndex)}</Fragment>);
  }

  return nodes.length > 0 ? nodes : text;
}

export function MathText({ text }: { text: string }) {
  return <>{renderMathNodes(text)}</>;
}
