export function cn(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

export async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
