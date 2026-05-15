import MarkdownIt from "markdown-it";
import { strapiRichTextToMarkdown } from "./strapiRichText";

const md = new MarkdownIt({ html: true });

export function richContentToHtml(value: unknown): string {
  if (!value) return "";
  if (typeof value === "string") {
    const text = value.trim();
    if (!text) return "";
    if (text.includes("<") && text.includes(">")) return text;
    return md.render(text);
  }
  return md.render(strapiRichTextToMarkdown(value));
}
