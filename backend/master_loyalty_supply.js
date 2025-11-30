import "dotenv/config";
import { Connection, Keypair, PublicKey, clusterApiUrl } from "@solana/web3.js";
import { getOrCreateAssociatedTokenAccount, mintTo } from "@solana/spl-token";

// Load master wallet secret and token mint from .env
const secretKey = JSON.parse(process.env.MASTER_WALLET_SECRET);
const masterKeypair = Keypair.fromSecretKey(Uint8Array.from(secretKey));
const mintAddress = new PublicKey(process.env.LOYALTY_TOKEN_MINT);

const connection = new Connection(clusterApiUrl("devnet"), "confirmed");

async function mintBulk() {
    try {
        // Get or create master wallet token account
        const masterTokenAccount = await getOrCreateAssociatedTokenAccount(
            connection,
            masterKeypair,
            mintAddress,
            masterKeypair.publicKey
        );

        // Mint a large number of tokens
        const amountToMint = 1_000_000; // Adjust as needed
        await mintTo(
            connection,
            masterKeypair,
            mintAddress,
            masterTokenAccount.address,
            masterKeypair,
            amountToMint
        );

        console.log(JSON.stringify({ success: true, minted: amountToMint }));
    } catch (err) {
        console.log(JSON.stringify({ success: false, error: err.message }));
    }
}

mintBulk();
