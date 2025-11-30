import "dotenv/config";
import { Connection, Keypair, clusterApiUrl } from "@solana/web3.js";
import { createMint } from "@solana/spl-token";

// ----- CONFIG -----
const NETWORK = "devnet"; // or "mainnet-beta"
// ------------------

// Load master wallet from env
if (!process.env.MASTER_WALLET_SECRET) {
    console.error("Error: MASTER_WALLET_SECRET not set in .env");
    process.exit(1);
}

const secretKey = JSON.parse(process.env.MASTER_WALLET_SECRET);
const masterKeypair = Keypair.fromSecretKey(Uint8Array.from(secretKey));

const connection = new Connection(clusterApiUrl(NETWORK), "confirmed");

async function createLoyaltyToken() {
    try {
        const mint = await createMint(
            connection,
            masterKeypair,       // payer
            masterKeypair.publicKey, // mint authority
            null,                // freeze authority
            0                    // decimals: 0 for 1 token per journey
        );

        console.log(JSON.stringify({
            token_mint: mint.toBase58(),
            message: "Loyalty token created successfully!"
        }));
    } catch (err) {
        console.error(JSON.stringify({ token_mint: null, error: err.message }));
    }
}

createLoyaltyToken();
