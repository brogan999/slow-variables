// Reads a password from standard input (never from the command line, which a shell records) and prints
// "<salt hex>:<hash hex>": scrypt at Node's default cost with a 64-byte key, as the site's lock checks it.
import { randomBytes, scryptSync } from "node:crypto";
import { readFileSync } from "node:fs";

const password = readFileSync(0, "utf8").replace(/\r?\n$/, "");
if (!password) process.exit(1);
const salt = randomBytes(16);
console.log(`${salt.toString("hex")}:${scryptSync(password, salt, 64).toString("hex")}`);
