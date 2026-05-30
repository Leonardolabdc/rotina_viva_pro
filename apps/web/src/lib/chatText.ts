/** Remove markdown bold/italic — o chat renderiza texto puro. */
export function plainChatText(text: string): string {
  let s = text ?? "";
  for (let i = 0; i < 3; i++) {
    const next = s
      .replace(/\*\*([\s\S]+?)\*\*/g, "$1")
      .replace(/__([\s\S]+?)__/g, "$1");
    if (next === s) break;
    s = next;
  }
  return s;
}
