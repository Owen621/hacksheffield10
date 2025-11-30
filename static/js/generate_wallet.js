import { Keypair } from "@solana/web3.js";
import fs from "fs";

const kp = Keypair.generate();

console.log("Public Key:", kp.publicKey.toBase58());

fs.writeFileSync(
  "master-wallet.json",
  JSON.stringify(Array.from(kp.secretKey))
);

console.log("Saved to master-wallet.json");
