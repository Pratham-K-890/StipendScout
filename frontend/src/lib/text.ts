/** Light cleanup so a raw README excerpt reads reasonably as a plain-text
 * snippet — strips badges/images, link syntax, headers, and code fences
 * without needing a full markdown renderer for what's just a preview. */
export function stripMarkdownNoise(text: string): string {
  return text
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '') // badge/image
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1') // [text](url) -> text
    .replace(/```[\s\S]*?```/g, ' ') // code fences
    .replace(/^#{1,6}\s*/gm, '') // header markers
    .replace(/^-{3,}\s*$/gm, '') // horizontal rules
    .replace(/`([^`]*)`/g, '$1') // inline code
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{2,}/g, '\n')
    .trim()
}
