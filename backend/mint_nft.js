import "dotenv/config";
import { Connection, Keypair, PublicKey, clusterApiUrl } from "@solana/web3.js";
import { createMint, getOrCreateAssociatedTokenAccount, mintTo } from "@solana/spl-token";

const [userWallet] = process.argv.slice(2);

if (!userWallet) {
  console.error("No user wallet provided");
  process.exit(1);
}

// Load master wallet secret from env
const secretKeyRaw = process.env.MASTER_WALLET_SECRET;

if (!secretKeyRaw) {
  console.error("❌ MASTER_WALLET_SECRET not defined!");
  process.exit(1);
}

const secretKey = JSON.parse(secretKeyRaw);
const masterKeypair = Keypair.fromSecretKey(Uint8Array.from(secretKey));

const connection = new Connection(clusterApiUrl("devnet"), "confirmed");

async function mintNFT() {
  try {
    // 1️⃣ Create NFT mint (0 decimals)
    const mint = await createMint(
      connection,
      masterKeypair,
      masterKeypair.publicKey,
      null,
      0
    );

    // 2️⃣ Get or create user's associated token account
    const userTokenAccount = await getOrCreateAssociatedTokenAccount(
      connection,
      masterKeypair,
      mint,
      new PublicKey(userWallet)
    );

    // 3️⃣ Mint 1 token to user's account
    await mintTo(
      connection,
      masterKeypair,
      mint,
      userTokenAccount.address,
      masterKeypair,
      1
    );

    // ✅ Return mint address
    console.log(JSON.stringify({ mint_address: mint.toBase58() }));
  } catch (err) {
    console.error("Mint failed:", err);
    console.log(JSON.stringify({ mint_address: null }));
  }
}

mintNFT();
