function normalizeText(value: string): string {
  return value.replace(/\r\n/g, '\n').replace(/\\n/g, '\n');
}

function escapeMarkdown(value: string): string {
  return value.replace(/([\\`*_{}\[\]()#+\-.!|>])/g, '\\$1');
}

function applyInlineFormats(text: string, node: any): string {
  let formatted = text;

  if (!formatted) return '';
  if (node?.code) formatted = `\`${formatted}\``;
  if (node?.bold) formatted = `**${formatted}**`;
  if (node?.italic) formatted = `*${formatted}*`;
  if (node?.strikethrough) formatted = `~~${formatted}~~`;
  if (node?.underline) formatted = `<u>${formatted}</u>`;

  return formatted;
}

function renderInline(node: any): string {
  if (typeof node === 'string') {
    return normalizeText(node);
  }

  if (!node || typeof node !== 'object') {
    return '';
  }

  if (typeof node.text === 'string') {
    return applyInlineFormats(escapeMarkdown(normalizeText(node.text)), node);
  }

  const children = Array.isArray(node.children)
    ? node.children
    : Array.isArray(node.content)
    ? node.content
    : [];
  const text = children.map((child: any) => renderInline(child)).join('');

  if (node.type === 'link' && node.url) {
    return `[${text || node.url}](${node.url})`;
  }

  return text;
}

function indentLines(value: string, indent: string): string {
  return value
    .split('\n')
    .map((line, index) => (index === 0 ? line : `${indent}${line}`))
    .join('\n');
}

function renderListItem(node: any, indent = 0, ordered = false, index = 0): string {
  const marker = ordered ? `${index + 1}. ` : '- ';
  const spacing = ' '.repeat(indent + marker.length);
  const children = Array.isArray(node?.children)
    ? node.children
    : Array.isArray(node?.content)
    ? node.content
    : [];

  if (children.length === 0) {
    const text = renderInline(node).trim();
    return text ? `${' '.repeat(indent)}${marker}${text}` : '';
  }

  const parts = children
    .map((child: any) => {
      if (child?.type === 'list') {
        return renderNode(child, indent + marker.length);
      }

      return renderNode(child, indent + marker.length).trim();
    })
    .filter(Boolean);

  if (parts.length === 0) return '';

  const [first, ...rest] = parts;
  return [
    `${' '.repeat(indent)}${marker}${first}`,
    ...rest.map((part) => indentLines(part, spacing)),
  ].join('\n');
}

function renderNode(node: any, indent = 0): string {
  if (typeof node === 'string') {
    return normalizeText(node).trim();
  }

  if (!node || typeof node !== 'object') {
    return '';
  }

  const type = String(node.type ?? '').toLowerCase();
  const children = Array.isArray(node.children)
    ? node.children
    : Array.isArray(node.content)
    ? node.content
    : [];

  if (type === 'list') {
    const ordered = node.format === 'ordered' || node.listType === 'ordered';
    return children
      .map((child: any, index: number) => renderListItem(child, indent, ordered, index))
      .filter(Boolean)
      .join('\n');
  }

  if (type === 'list-item') {
    return renderListItem(node, indent);
  }

  if (type === 'heading') {
    const level = Math.min(Math.max(Number(node.level ?? 2), 1), 6);
    const text = children.map((child: any) => renderInline(child)).join('').trim();
    return text ? `${'#'.repeat(level)} ${text}` : '';
  }

  if (type === 'quote' || type === 'blockquote') {
    const text = children
      .map((child: any) => renderNode(child, indent))
      .filter(Boolean)
      .join('\n\n');
    return text
      .split('\n')
      .map((line) => `> ${line}`)
      .join('\n');
  }

  if (type === 'code' || type === 'codeblock') {
    const code = typeof node.code === 'string'
      ? node.code
      : children.map((child: any) => renderInline(child)).join('');
    return code ? `\`\`\`\n${normalizeText(code)}\n\`\`\`` : '';
  }

  if (type === 'image' && node.image?.url) {
    const alt = typeof node.image?.alternativeText === 'string' ? node.image.alternativeText : '';
    return `![${alt}](${node.image.url})`;
  }

  if (type === 'paragraph') {
    return children.map((child: any) => renderInline(child)).join('').trim();
  }

  if (children.length > 0) {
    return children
      .map((child: any) => renderNode(child, indent))
      .filter(Boolean)
      .join('\n\n');
  }

  if (typeof node.text === 'string') {
    return renderInline(node).trim();
  }

  return '';
}

export function strapiRichTextToMarkdown(value: any): string {
  if (typeof value === 'string') {
    return normalizeText(value);
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => renderNode(item))
      .filter(Boolean)
      .join('\n\n')
      .trim();
  }

  return renderNode(value).trim();
}

export function cleanTextValue(value: any): string {
  return typeof value === 'string'
    ? value.replace(/\s+/g, ' ').trim()
    : '';
}
