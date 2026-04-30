import * as age from "age-encryption";

export type ScanIdentity = {
  identity: string;
  recipient: string;
  createdAt: string;
};

export async function generateScanIdentity(): Promise<ScanIdentity> {
  const identity = await age.generateIdentity();
  const recipient = await age.identityToRecipient(identity);
  return {
    identity,
    recipient,
    createdAt: new Date().toISOString(),
  };
}

export async function decryptBundleBytes(
  ciphertext: Uint8Array,
  identity: string,
): Promise<Uint8Array> {
  const decrypter = new age.Decrypter();
  decrypter.addIdentity(identity);
  return await decrypter.decrypt(ciphertext);
}

export async function decryptBundleJson(
  ciphertext: Uint8Array,
  identity: string,
): Promise<unknown> {
  const plaintext = await decryptBundleBytes(ciphertext, identity);
  const text = new TextDecoder().decode(plaintext);
  return JSON.parse(text);
}

export function downloadIdentityFile(identity: ScanIdentity, filename = "spieon-key.txt"): void {
  if (typeof window === "undefined") return;
  const body = [
    "# Spieon scan recipient key.",
    "# Keep this file safe. Anyone with it can decrypt the encrypted finding bundles for the matching scans.",
    `# Created: ${identity.createdAt}`,
    `# Public recipient: ${identity.recipient}`,
    "",
    identity.identity,
    "",
  ].join("\n");
  const blob = new Blob([body], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
