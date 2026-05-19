import MarkdownIt from "markdown-it";
import { strapiRichTextToMarkdown } from "./strapiRichText";

const md = new MarkdownIt({ html: true });

export function normalizeOdooHtml(value: unknown): string {
  if (typeof value !== "string") return "";
  const text = value.trim();
  if (!text) return "";
  return text
    .replace(/\sdata-oe-version=(['"]).*?\1/g, "")
    .replace(/\sdata-oe-[a-z-]+=(['"]).*?\1/g, "");
}

export function richContentToHtml(value: unknown): string {
  if (!value) return "";
  if (typeof value === "string") {
    const text = normalizeOdooHtml(value);
    if (!text) return "";
    if (text.includes("<") && text.includes(">")) return text;
    return md.render(text);
  }
  return md.render(strapiRichTextToMarkdown(value));
}
